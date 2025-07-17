"""
ChromaDB integration for medical knowledge storage with proper metadata and citations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import uuid

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np

from .document_ingestion import ProcessedDocument, DocumentMetadata

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manager for ChromaDB operations with medical document storage."""
    
    def __init__(
        self,
        persist_directory: str = "data/chromadb",
        collection_name: str = "medical_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"ChromaDB initialized with collection: {collection_name}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one."""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            # Create new collection
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Medical knowledge base with citations",
                    "created_at": datetime.utcnow().isoformat(),
                    "embedding_model": self.embedding_model
                }
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    async def add_documents(self, documents: List[ProcessedDocument]) -> int:
        """
        Add processed documents to ChromaDB collection.
        
        Args:
            documents: List of processed documents with chunks and metadata
            
        Returns:
            Number of chunks successfully added
        """
        total_chunks = 0
        
        for doc in documents:
            try:
                chunks_added = await self._add_single_document(doc)
                total_chunks += chunks_added
            except Exception as e:
                logger.error(f"Error adding document {doc.metadata.title}: {e}")
        
        logger.info(f"Added {total_chunks} chunks from {len(documents)} documents")
        return total_chunks
    
    async def _add_single_document(self, doc: ProcessedDocument) -> int:
        """Add a single document's chunks to the collection."""
        if not doc.chunks:
            logger.warning(f"No chunks found for document: {doc.metadata.title}")
            return 0
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for i, (chunk, chunk_meta) in enumerate(zip(doc.chunks, doc.chunk_metadata)):
            # Create unique ID for each chunk
            chunk_id = f"{doc.document_hash}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            
            # Combine document metadata with chunk metadata
            combined_metadata = {
                # Document-level metadata
                "document_hash": doc.document_hash,
                "source": doc.metadata.source,
                "document_type": doc.metadata.document_type,
                "title": doc.metadata.title,
                "authors": json.dumps(doc.metadata.authors),
                "publication_date": doc.metadata.publication_date or "",
                "doi": doc.metadata.doi or "",
                "url": doc.metadata.url or "",
                "medical_specialty": doc.metadata.medical_specialty or "",
                "abstract": doc.metadata.abstract or "",
                "keywords": json.dumps(doc.metadata.keywords),
                "language": doc.metadata.language,
                "confidence_score": doc.metadata.confidence_score,
                "ingestion_timestamp": doc.metadata.ingestion_timestamp,
                
                # Chunk-level metadata
                "chunk_index": chunk_meta.get("chunk_index", i),
                "section": chunk_meta.get("section", "main"),
                "total_chunks": len(doc.chunks),
                
                # Additional searchable fields
                "content_length": len(chunk),
                "has_citations": "doi" in chunk.lower() or "pmid" in chunk.lower(),
                "is_abstract": chunk_meta.get("section") == "abstract"
            }
            
            metadatas.append(combined_metadata)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.debug(f"Added {len(chunks)} chunks for document: {doc.metadata.title}")
        return len(documents)
    
    async def search_similar(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filters: Optional metadata filters
            include_metadata: Whether to include full metadata in results
            
        Returns:
            Dictionary with search results and metadata
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
            
            # Process results
            processed_results = self._process_search_results(results, include_metadata)
            
            logger.debug(f"Search query: '{query}' returned {len(processed_results['documents'])} results")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "citations": []}
    
    def _process_search_results(
        self,
        raw_results: Dict[str, Any],
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Process raw ChromaDB search results."""
        if not raw_results["documents"] or not raw_results["documents"][0]:
            return {"documents": [], "metadatas": [], "distances": [], "citations": []}
        
        documents = raw_results["documents"][0]
        metadatas = raw_results["metadatas"][0] if include_metadata else []
        distances = raw_results["distances"][0]
        
        # Extract citations from metadata
        citations = []
        for metadata in metadatas:
            citation = self._extract_citation(metadata)
            citations.append(citation)
        
        return {
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
            "citations": citations
        }
    
    def _extract_citation(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract citation information from chunk metadata."""
        return {
            "title": metadata.get("title", "Unknown Title"),
            "authors": json.loads(metadata.get("authors", "[]")),
            "source": metadata.get("source", "unknown"),
            "publication_date": metadata.get("publication_date", ""),
            "doi": metadata.get("doi", ""),
            "url": metadata.get("url", ""),
            "document_type": metadata.get("document_type", "document"),
            "medical_specialty": metadata.get("medical_specialty", ""),
            "section": metadata.get("section", "main"),
            "confidence_score": metadata.get("confidence_score", 1.0),
            "relevance_score": 1.0 - metadata.get("distance", 0.0)  # Convert distance to relevance
        }
    
    async def search_by_filters(
        self,
        filters: Dict[str, Any],
        n_results: int = 100
    ) -> Dict[str, Any]:
        """
        Search documents by metadata filters only.
        
        Args:
            filters: Metadata filters (e.g., {"source": "pubmed", "medical_specialty": "psychiatry"})
            n_results: Maximum number of results
            
        Returns:
            Filtered search results
        """
        try:
            results = self.collection.get(
                where=filters,
                limit=n_results,
                include=["documents", "metadatas"]
            )
            
            # Convert to standard format
            processed_results = {
                "documents": results["documents"],
                "metadatas": results["metadatas"],
                "distances": [0.0] * len(results["documents"]),  # No distance for filter-only search
                "citations": [self._extract_citation(meta) for meta in results["metadatas"]]
            }
            
            logger.debug(f"Filter search returned {len(processed_results['documents'])} results")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error during filter search: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "citations": []}
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample_results = self.collection.get(
                limit=min(1000, count),
                include=["metadatas"]
            )
            
            # Analyze metadata
            stats = {
                "total_chunks": count,
                "sources": {},
                "document_types": {},
                "medical_specialties": {},
                "languages": {}
            }
            
            for metadata in sample_results["metadatas"]:
                # Count by source
                source = metadata.get("source", "unknown")
                stats["sources"][source] = stats["sources"].get(source, 0) + 1
                
                # Count by document type
                doc_type = metadata.get("document_type", "unknown")
                stats["document_types"][doc_type] = stats["document_types"].get(doc_type, 0) + 1
                
                # Count by medical specialty
                specialty = metadata.get("medical_specialty", "unknown")
                stats["medical_specialties"][specialty] = stats["medical_specialties"].get(specialty, 0) + 1
                
                # Count by language
                language = metadata.get("language", "unknown")
                stats["languages"][language] = stats["languages"].get(language, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_chunks": 0, "sources": {}, "document_types": {}, "medical_specialties": {}, "languages": {}}
    
    async def delete_documents_by_hash(self, document_hashes: List[str]) -> int:
        """
        Delete documents by their hash values.
        
        Args:
            document_hashes: List of document hashes to delete
            
        Returns:
            Number of chunks deleted
        """
        deleted_count = 0
        
        for doc_hash in document_hashes:
            try:
                # Get all chunks for this document
                results = self.collection.get(
                    where={"document_hash": doc_hash},
                    include=["ids"]
                )
                
                if results["ids"]:
                    # Delete all chunks for this document
                    self.collection.delete(ids=results["ids"])
                    deleted_count += len(results["ids"])
                    logger.debug(f"Deleted {len(results['ids'])} chunks for document hash: {doc_hash}")
                
            except Exception as e:
                logger.error(f"Error deleting document {doc_hash}: {e}")
        
        logger.info(f"Deleted {deleted_count} chunks for {len(document_hashes)} documents")
        return deleted_count
    
    async def update_document_metadata(
        self,
        document_hash: str,
        metadata_updates: Dict[str, Any]
    ) -> int:
        """
        Update metadata for all chunks of a document.
        
        Args:
            document_hash: Hash of the document to update
            metadata_updates: Dictionary of metadata fields to update
            
        Returns:
            Number of chunks updated
        """
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_hash": document_hash},
                include=["ids", "metadatas"]
            )
            
            if not results["ids"]:
                logger.warning(f"No chunks found for document hash: {document_hash}")
                return 0
            
            # Update metadata for each chunk
            updated_metadatas = []
            for metadata in results["metadatas"]:
                updated_metadata = metadata.copy()
                updated_metadata.update(metadata_updates)
                updated_metadatas.append(updated_metadata)
            
            # Update in ChromaDB
            self.collection.update(
                ids=results["ids"],
                metadatas=updated_metadatas
            )
            
            logger.debug(f"Updated metadata for {len(results['ids'])} chunks of document: {document_hash}")
            return len(results["ids"])
            
        except Exception as e:
            logger.error(f"Error updating document metadata: {e}")
            return 0
    
    def reset_collection(self):
        """Reset the collection (delete all data)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
    
    def close(self):
        """Close the ChromaDB client."""
        # ChromaDB client doesn't need explicit closing
        logger.info("ChromaDB manager closed")


class MedicalKnowledgeBase:
    """High-level interface for medical knowledge base operations."""
    
    def __init__(
        self,
        chromadb_manager: ChromaDBManager,
        confidence_threshold: float = 0.7
    ):
        self.chromadb = chromadb_manager
        self.confidence_threshold = confidence_threshold
    
    async def search_medical_knowledge(
        self,
        query: str,
        specialty_filter: Optional[str] = None,
        source_filter: Optional[str] = None,
        document_type_filter: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search medical knowledge with optional filters.
        
        Args:
            query: Medical query text
            specialty_filter: Filter by medical specialty
            source_filter: Filter by source (pubmed, who, cdc)
            document_type_filter: Filter by document type
            max_results: Maximum number of results
            
        Returns:
            Search results with confidence scoring
        """
        # Build filters
        filters = {}
        if specialty_filter:
            filters["medical_specialty"] = specialty_filter
        if source_filter:
            filters["source"] = source_filter
        if document_type_filter:
            filters["document_type"] = document_type_filter
        
        # Perform search
        results = await self.chromadb.search_similar(
            query=query,
            n_results=max_results,
            filters=filters if filters else None
        )
        
        # Add confidence scoring
        results = self._add_confidence_scores(results, query)
        
        return results
    
    def _add_confidence_scores(
        self,
        results: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """Add confidence scores to search results."""
        if not results["documents"]:
            return results
        
        # Calculate confidence based on distance and metadata
        for i, (distance, metadata) in enumerate(zip(results["distances"], results["metadatas"])):
            # Base confidence from similarity (1 - distance)
            similarity_confidence = max(0.0, 1.0 - distance)
            
            # Boost confidence for high-quality sources
            source_boost = {
                "pubmed": 1.2,
                "who": 1.1,
                "cdc": 1.1,
                "manual": 1.0
            }.get(metadata.get("source", "manual"), 1.0)
            
            # Boost confidence for research papers
            type_boost = {
                "research_paper": 1.1,
                "guideline": 1.05,
                "fact_sheet": 1.0
            }.get(metadata.get("document_type", "document"), 1.0)
            
            # Calculate final confidence
            final_confidence = min(1.0, similarity_confidence * source_boost * type_boost)
            
            # Update citation with confidence
            if i < len(results["citations"]):
                results["citations"][i]["confidence_score"] = final_confidence
                results["citations"][i]["meets_threshold"] = final_confidence >= self.confidence_threshold
        
        return results
    
    async def get_authoritative_sources(
        self,
        topic: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get most authoritative sources for a medical topic.
        
        Args:
            topic: Medical topic
            max_results: Maximum number of sources
            
        Returns:
            List of authoritative sources with metadata
        """
        # Search with preference for high-quality sources
        results = await self.search_medical_knowledge(
            query=topic,
            max_results=max_results * 2  # Get more to filter
        )
        
        # Filter and rank by authority
        authoritative_sources = []
        seen_documents = set()
        
        for i, citation in enumerate(results["citations"]):
            # Skip duplicates (same document)
            doc_key = (citation["title"], citation["source"])
            if doc_key in seen_documents:
                continue
            seen_documents.add(doc_key)
            
            # Only include high-confidence results
            if citation.get("confidence_score", 0) >= self.confidence_threshold:
                authoritative_sources.append({
                    "citation": citation,
                    "content": results["documents"][i],
                    "relevance_score": citation.get("relevance_score", 0),
                    "confidence_score": citation.get("confidence_score", 0)
                })
            
            if len(authoritative_sources) >= max_results:
                break
        
        # Sort by confidence and relevance
        authoritative_sources.sort(
            key=lambda x: (x["confidence_score"], x["relevance_score"]),
            reverse=True
        )
        
        return authoritative_sources[:max_results]


# Example usage and testing
async def main():
    """Example usage of ChromaDB integration."""
    # Initialize ChromaDB manager
    chromadb_manager = ChromaDBManager()
    
    # Initialize knowledge base
    knowledge_base = MedicalKnowledgeBase(chromadb_manager)
    
    # Get collection stats
    stats = await chromadb_manager.get_collection_stats()
    print(f"Collection stats: {stats}")
    
    # Example search
    results = await knowledge_base.search_medical_knowledge(
        query="depression treatment options",
        max_results=5
    )
    
    print(f"\nSearch results for 'depression treatment options':")
    for i, citation in enumerate(results["citations"]):
        print(f"{i+1}. {citation['title']}")
        print(f"   Source: {citation['source']} | Confidence: {citation.get('confidence_score', 0):.2f}")
        print(f"   Authors: {', '.join(citation['authors'][:3])}")
        print()


if __name__ == "__main__":
    asyncio.run(main())