"""
ChromaDB integration for vector storage and similarity search.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

from ..models.core import Citation, Document, RAGResults

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """ChromaDB manager for vector storage and retrieval."""
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize ChromaDB manager.
        
        Args:
            host: ChromaDB host (defaults to environment variable or localhost)
            port: ChromaDB port (defaults to environment variable or 8000)
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb package is required for ChromaDBManager")
        
        self.host = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMADB_PORT", "8000"))
        
        # Initialize client
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.basic.BasicAuthClientProvider",
                    chroma_client_auth_credentials=os.getenv("CHROMADB_AUTH", ""),
                ) if os.getenv("CHROMADB_AUTH") else Settings()
            )
        except Exception as e:
            logger.warning(f"Failed to connect to ChromaDB server, using persistent client: {e}")
            # Fallback to persistent client for development
            self.client = chromadb.PersistentClient(
                path=os.getenv("CHROMADB_PERSIST_PATH", "./data/chromadb")
            )
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
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
    
    async def search_similar(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: str = "medical_knowledge"
    ) -> Dict[str, Any]:
        """
        Perform similarity search across collections.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional filters
            collection_name: Collection to search
            
        Returns:
            Search results
        """
        if collection_name == "medical_knowledge":
            collection = self.get_medical_knowledge_collection()
        elif collection_name == "user_contexts":
            collection = self.get_user_contexts_collection()
        else:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        return await collection.search(query, n_results, filters)
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        stats = {}
        
        try:
            medical_collection = self.get_medical_knowledge_collection()
            stats["medical_knowledge"] = await medical_collection.get_stats()
        except Exception as e:
            logger.error(f"Error getting medical knowledge stats: {e}")
            stats["medical_knowledge"] = {"error": str(e)}
        
        try:
            user_collection = self.get_user_contexts_collection()
            stats["user_contexts"] = await user_collection.get_stats()
        except Exception as e:
            logger.error(f"Error getting user contexts stats: {e}")
            stats["user_contexts"] = {"error": str(e)}
        
        return stats


class MedicalKnowledgeCollection:
    """Medical knowledge collection for storing and retrieving medical documents."""
    
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
    
    async def add_documents(self, documents: List[Document]) -> int:
        """
        Add documents to the collection.
        
        Args:
            documents: List of documents to add
            
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        try:
            # Prepare data for ChromaDB
            ids = []
            texts = []
            metadatas = []
            
            for i, doc in enumerate(documents):
                doc_id = f"doc_{datetime.utcnow().timestamp()}_{i}"
                ids.append(doc_id)
                texts.append(doc.content)
                
                # Prepare metadata
                metadata = dict(doc.metadata)
                metadata["score"] = doc.score
                metadata["source"] = doc.source
                metadata["added_at"] = datetime.utcnow().isoformat()
                
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to medical knowledge collection")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error adding documents to collection: {e}")
            return 0
    
    async def search(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search the medical knowledge collection.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional filters
            
        Returns:
            Search results
        """
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                where_clause.update(filters)
            
            # Perform similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results into our format
            documents = []
            citations = []
            confidence_scores = []
            
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    # Convert distance to similarity score (1 - distance)
                    similarity_score = max(0.0, 1.0 - distance)
                    confidence_scores.append(similarity_score)
                    
                    # Create Document object
                    document = Document(
                        content=doc,
                        metadata=metadata,
                        score=similarity_score,
                        source=metadata.get("source", "unknown")
                    )
                    documents.append(document)
                    
                    # Create Citation if metadata contains citation info
                    if "title" in metadata and "url" in metadata:
                        citation = Citation(
                            source=metadata.get("source", "unknown"),
                            title=metadata.get("title", ""),
                            authors=metadata.get("authors", []),
                            publication_date=metadata.get("publication_date"),
                            url=metadata.get("url", ""),
                            excerpt=doc[:200] + "..." if len(doc) > 200 else doc,
                            relevance_score=similarity_score,
                            doi=metadata.get("doi")
                        )
                        citations.append(citation)
            
            return {
                "documents": documents,
                "citations": citations,
                "confidence_scores": confidence_scores,
                "search_metadata": {
                    "query": query,
                    "n_results": n_results,
                    "filters": filters,
                    "total_results": len(documents)
                }
            }
            
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return {
                "documents": [],
                "citations": [],
                "confidence_scores": [],
                "search_metadata": {"error": str(e)}
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.COLLECTION_NAME,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}


class UserContextCollection:
    """User context collection for storing conversation histories and user profiles."""
    
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
    
    async def add_user_context(
        self,
        user_id: str,
        session_id: str,
        context_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add user context to the collection.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            context_text: Context text to store
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            context_id = f"user_{user_id}_session_{session_id}_{datetime.utcnow().timestamp()}"
            
            context_metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            self.collection.add(
                ids=[context_id],
                documents=[context_text],
                metadatas=[context_metadata]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding user context: {e}")
            return False
    
    async def search(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search user contexts.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional filters (e.g., user_id)
            
        Returns:
            Search results
        """
        try:
            where_clause = {}
            if filters:
                where_clause.update(filters)
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            return {
                "contexts": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }
            
        except Exception as e:
            logger.error(f"Error searching user contexts: {e}")
            return {"contexts": [], "metadatas": [], "distances": []}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            return {
                "context_count": count,
                "collection_name": self.COLLECTION_NAME,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}


class MedicalKnowledgeBase:
    """High-level interface for medical knowledge operations."""
    
    def __init__(self, chromadb_manager: ChromaDBManager, confidence_threshold: float = 0.7):
        """
        Initialize medical knowledge base.
        
        Args:
            chromadb_manager: ChromaDB manager instance
            confidence_threshold: Minimum confidence threshold for results
        """
        self.chromadb_manager = chromadb_manager
        self.confidence_threshold = confidence_threshold
        self.collection = chromadb_manager.get_medical_knowledge_collection()
    
    async def search_medical_knowledge(
        self,
        query: str,
        specialty_filter: Optional[str] = None,
        source_filter: Optional[str] = None,
        max_results: int = 10
    ) -> RAGResults:
        """
        Search medical knowledge with filters.
        
        Args:
            query: Medical query
            specialty_filter: Filter by medical specialty
            source_filter: Filter by source
            max_results: Maximum results to return
            
        Returns:
            RAGResults object
        """
        # Build filters
        filters = {}
        if specialty_filter:
            filters["medical_specialty"] = specialty_filter
        if source_filter:
            filters["source"] = source_filter
        
        # Perform search
        results = await self.collection.search(query, max_results, filters)
        
        # Filter by confidence threshold
        filtered_documents = []
        filtered_citations = []
        filtered_scores = []
        
        for doc, citation, score in zip(
            results["documents"],
            results["citations"],
            results["confidence_scores"]
        ):
            if score >= self.confidence_threshold:
                filtered_documents.append(doc)
                filtered_citations.append(citation)
                filtered_scores.append(score)
        
        return RAGResults(
            documents=filtered_documents,
            citations=filtered_citations,
            confidence_scores=filtered_scores,
            search_metadata=results["search_metadata"]
        )
    
    async def get_authoritative_sources(
        self,
        topic: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get most authoritative sources for a topic.
        
        Args:
            topic: Topic to search for
            max_results: Maximum number of sources
            
        Returns:
            List of authoritative sources with metadata
        """
        # Search with high confidence threshold for authoritative sources
        filters = {"source": {"$in": ["pubmed", "who", "cdc", "nih"]}}
        results = await self.collection.search(topic, max_results * 2, filters)
        
        # Sort by confidence and return top results
        authoritative_sources = []
        for doc, citation, score in zip(
            results["documents"],
            results["citations"], 
            results["confidence_scores"]
        ):
            if score >= 0.8:  # High threshold for authoritative sources
                authoritative_sources.append({
                    "document": doc,
                    "citation": citation,
                    "confidence_score": score,
                    "relevance_score": score
                })
        
        # Sort by confidence
        authoritative_sources.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return authoritative_sources[:max_results]
