"""
ChromaDB collection schemas and management.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manages ChromaDB collections and operations."""
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize ChromaDB manager.
        
        Args:
            host: ChromaDB host (defaults to environment variable or localhost)
            port: ChromaDB port (defaults to environment variable or 8000)
        """
        self.host = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMADB_PORT", "8000"))
        
        # Initialize client
        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port,
            settings=Settings(
                chroma_client_auth_provider="chromadb.auth.basic.BasicAuthClientProvider",
                chroma_client_auth_credentials=os.getenv("CHROMADB_AUTH", ""),
            ) if os.getenv("CHROMADB_AUTH") else Settings()
        )
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        
        # Collection instances
        self._medical_knowledge = None
        self._user_contexts = None
    
    def get_medical_knowledge_collection(self) -> 'MedicalKnowledgeCollection':
        """Get or create medical knowledge collection."""
        if self._medical_knowledge is None:
            self._medical_knowledge = MedicalKnowledgeCollection(self)
        return self._medical_knowledge
    
    def get_user_contexts_collection(self) -> 'UserContextCollection':
        """Get or create user contexts collection."""
        if self._user_contexts is None:
            self._user_contexts = UserContextCollection(self)
        return self._user_contexts
    
    def health_check(self) -> bool:
        """Check ChromaDB connectivity."""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def delete_collection(self, name: str):
        """Delete a collection."""
        try:
            self.client.delete_collection(name)
            logger.info(f"Deleted collection: {name}")
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            raise


class MedicalKnowledgeCollection:
    """Manages the medical knowledge collection in ChromaDB."""
    
    COLLECTION_NAME = "medical_knowledge"
    
    def __init__(self, chroma_manager: ChromaDBManager):
        """
        Initialize medical knowledge collection.
        
        Args:
            chroma_manager: ChromaDB manager instance
        """
        self.chroma_manager = chroma_manager
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get or create the medical knowledge collection."""
        try:
            return self.chroma_manager.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self.chroma_manager.embedding_function,
                metadata={
                    "description": "Medical knowledge base with scientific citations",
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
            )
        except Exception as e:
            logger.error(f"Failed to create medical knowledge collection: {e}")
            raise
    
    def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        Add a medical document to the collection.
        
        Args:
            document_id: Unique document identifier
            content: Document content
            metadata: Document metadata
        """
        # Validate required metadata fields
        required_fields = ["source", "document_type", "url"]
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Required metadata field missing: {field}")
        
        # Add timestamp
        metadata["indexed_at"] = datetime.utcnow().isoformat()
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[document_id]
            )
            logger.info(f"Added document {document_id} to medical knowledge collection")
        except Exception as e:
            logger.error(f"Failed to add document {document_id}: {e}")
            raise
    
    def add_documents_batch(
        self,
        document_ids: List[str],
        contents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        """
        Add multiple documents in batch.
        
        Args:
            document_ids: List of document IDs
            contents: List of document contents
            metadatas: List of document metadata
        """
        if not (len(document_ids) == len(contents) == len(metadatas)):
            raise ValueError("All input lists must have the same length")
        
        # Add timestamps to all metadata
        for metadata in metadatas:
            metadata["indexed_at"] = datetime.utcnow().isoformat()
        
        try:
            self.collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=document_ids
            )
            logger.info(f"Added {len(document_ids)} documents to medical knowledge collection")
        except Exception as e:
            logger.error(f"Failed to add documents batch: {e}")
            raise
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search medical knowledge collection.
        
        Args:
            query: Search query
            n_results: Number of results to return
            where: Metadata filter conditions
            
        Returns:
            Search results dictionary
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            logger.info(f"Medical knowledge search returned {len(results['documents'][0])} results")
            return results
        except Exception as e:
            logger.error(f"Medical knowledge search failed: {e}")
            raise
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document data or None if not found
        """
        try:
            results = self.collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )
            
            if results['documents']:
                return {
                    "id": document_id,
                    "document": results['documents'][0],
                    "metadata": results['metadatas'][0]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    def delete_document(self, document_id: str):
        """Delete a document from the collection."""
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id} from medical knowledge collection")
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            return {
                "name": self.COLLECTION_NAME,
                "document_count": count,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}


class UserContextCollection:
    """Manages the user context collection in ChromaDB."""
    
    COLLECTION_NAME = "user_contexts"
    
    def __init__(self, chroma_manager: ChromaDBManager):
        """
        Initialize user context collection.
        
        Args:
            chroma_manager: ChromaDB manager instance
        """
        self.chroma_manager = chroma_manager
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get or create the user context collection."""
        try:
            return self.chroma_manager.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self.chroma_manager.embedding_function,
                metadata={
                    "description": "User conversation contexts and summaries",
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
            )
        except Exception as e:
            logger.error(f"Failed to create user context collection: {e}")
            raise
    
    def add_context(
        self,
        context_id: str,
        user_id: str,
        session_id: str,
        conversation_summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add user context to the collection.
        
        Args:
            context_id: Unique context identifier
            user_id: User identifier
            session_id: Session identifier
            conversation_summary: Summarized conversation content
            metadata: Additional metadata
        """
        context_metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        }
        
        try:
            self.collection.add(
                documents=[conversation_summary],
                metadatas=[context_metadata],
                ids=[context_id]
            )
            logger.info(f"Added context {context_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to add context {context_id}: {e}")
            raise
    
    def get_user_contexts(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get contexts for a specific user.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            limit: Maximum number of contexts to return
            
        Returns:
            List of user contexts
        """
        where_clause = {"user_id": user_id}
        if session_id:
            where_clause["session_id"] = session_id
        
        try:
            results = self.collection.query(
                query_texts=[""],  # Empty query to get all matching metadata
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas"]
            )
            
            contexts = []
            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    contexts.append({
                        "document": doc,
                        "metadata": results['metadatas'][0][i]
                    })
            
            return contexts
        except Exception as e:
            logger.error(f"Failed to get contexts for user {user_id}: {e}")
            return []
    
    def search_user_contexts(
        self,
        user_id: str,
        query: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search user contexts by content.
        
        Args:
            user_id: User identifier
            query: Search query
            n_results: Number of results to return
            
        Returns:
            Search results
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id},
                include=["documents", "metadatas", "distances"]
            )
            
            return results
        except Exception as e:
            logger.error(f"Failed to search contexts for user {user_id}: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def delete_user_contexts(self, user_id: str, session_id: Optional[str] = None):
        """
        Delete contexts for a user.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier (if None, deletes all user contexts)
        """
        where_clause = {"user_id": user_id}
        if session_id:
            where_clause["session_id"] = session_id
        
        try:
            self.collection.delete(where=where_clause)
            logger.info(f"Deleted contexts for user {user_id}" + 
                       (f" session {session_id}" if session_id else ""))
        except Exception as e:
            logger.error(f"Failed to delete contexts for user {user_id}: {e}")
            raise


# Global ChromaDB manager instance
chroma_manager = ChromaDBManager()