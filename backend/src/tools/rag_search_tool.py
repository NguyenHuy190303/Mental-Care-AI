"""
RAG Search Tool with vector similarity search functionality and citation extraction.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from .chromadb_integration import ChromaDBManager, MedicalKnowledgeBase
from .caching import CacheManager, CachedRAGSearchTool
from ..models.core import RAGResults, Citation, Document

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculates confidence scores for search results."""
    
    def __init__(self):
        """Initialize confidence scorer with source weights."""
        self.source_weights = {
            "pubmed": 1.0,
            "who": 0.95,
            "cdc": 0.9,
            "nih": 0.9,
            "mayo_clinic": 0.8,
            "webmd": 0.6,
            "manual": 0.5,
            "unknown": 0.3
        }
        
        self.type_weights = {
            "research_paper": 1.0,
            "clinical_guideline": 0.95,
            "fact_sheet": 0.8,
            "article": 0.7,
            "document": 0.6
        }
    
    def calculate_confidence(
        self,
        similarity_score: float,
        metadata: Dict[str, Any],
        query: str
    ) -> float:
        """
        Calculate overall confidence score.
        
        Args:
            similarity_score: Vector similarity score
            metadata: Document metadata
            query: Original query
            
        Returns:
            Confidence score (0-1)
        """
        # Base confidence from similarity
        base_confidence = similarity_score
        
        # Source reliability factor
        source = metadata.get("source", "unknown")
        source_factor = self.source_weights.get(source, 0.5)
        
        # Document type factor
        doc_type = metadata.get("document_type", "document")
        type_factor = self.type_weights.get(doc_type, 0.8)
        
        # Recency factor
        recency_factor = self._calculate_recency_factor(metadata.get("publication_date"))
        
        # Query relevance factor
        relevance_factor = self._calculate_query_relevance(query, metadata)
        
        # Citation quality factor
        citation_factor = self._calculate_citation_quality(metadata)
        
        # Weighted combination
        confidence = (
            base_confidence * 0.4 +
            source_factor * 0.2 +
            type_factor * 0.15 +
            recency_factor * 0.1 +
            relevance_factor * 0.1 +
            citation_factor * 0.05
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_recency_factor(self, publication_date: Optional[str]) -> float:
        """Calculate recency factor based on publication date."""
        if not publication_date:
            return 0.5
        
        try:
            if isinstance(publication_date, str):
                pub_date = datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
            else:
                pub_date = publication_date
            
            years_old = (datetime.now() - pub_date).days / 365.25
            
            if years_old <= 1:
                return 1.0
            elif years_old <= 3:
                return 0.9
            elif years_old <= 5:
                return 0.8
            elif years_old <= 10:
                return 0.6
            else:
                return 0.4
                
        except Exception:
            return 0.5
    
    def _calculate_query_relevance(self, query: str, metadata: Dict[str, Any]) -> float:
        """Calculate how relevant the document is to the query."""
        query_lower = query.lower()
        
        # Check title relevance
        title = metadata.get("title", "").lower()
        title_matches = sum(1 for word in query_lower.split() if word in title)
        title_relevance = title_matches / max(1, len(query_lower.split()))
        
        # Check specialty relevance
        specialty = metadata.get("medical_specialty", "").lower()
        specialty_relevance = 0.0
        if specialty and any(word in specialty for word in query_lower.split()):
            specialty_relevance = 0.2
        
        # Check keywords relevance
        keywords = metadata.get("keywords", [])
        if isinstance(keywords, str):
            try:
                import json
                keywords = json.loads(keywords)
            except:
                keywords = []
        
        keyword_matches = sum(1 for keyword in keywords if any(word in keyword.lower() for word in query_lower.split()))
        keyword_relevance = min(0.3, keyword_matches * 0.1)
        
        return min(1.0, title_relevance * 0.6 + specialty_relevance + keyword_relevance)
    
    def _calculate_citation_quality(self, metadata: Dict[str, Any]) -> float:
        """Calculate citation quality factor."""
        quality_score = 0.5  # Base score
        
        # Has DOI
        if metadata.get("doi"):
            quality_score += 0.2
        
        # Has authors
        authors = metadata.get("authors", [])
        if authors and len(authors) > 0:
            quality_score += 0.2
        
        # Has publication date
        if metadata.get("publication_date"):
            quality_score += 0.1
        
        return min(1.0, quality_score)


class RAGSearchTool:
    """Main RAG search tool with vector similarity search and citation extraction."""
    
    def __init__(
        self,
        chromadb_manager: ChromaDBManager,
        cache_manager: Optional[CacheManager] = None,
        confidence_threshold: float = 0.7,
        max_results: int = 10,
        enable_caching: bool = True
    ):
        """
        Initialize RAG search tool.
        
        Args:
            chromadb_manager: ChromaDB manager instance
            cache_manager: Cache manager for caching results
            confidence_threshold: Minimum confidence threshold
            max_results: Maximum results to return
            enable_caching: Whether to enable caching
        """
        self.chromadb_manager = chromadb_manager
        self.knowledge_base = MedicalKnowledgeBase(chromadb_manager, confidence_threshold)
        self.confidence_scorer = ConfidenceScorer()
        self.confidence_threshold = confidence_threshold
        self.max_results = max_results
        
        # Set up caching if enabled
        if enable_caching and cache_manager:
            self._cached_tool = CachedRAGSearchTool(
                rag_tool=self,
                cache_manager=cache_manager,
                enable_caching=True
            )
        else:
            self._cached_tool = None
        
        logger.info("RAG Search Tool initialized")
    
    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        include_low_confidence: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> RAGResults:
        """
        Perform RAG search with confidence scoring.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            include_low_confidence: Include results below confidence threshold
            filters: Optional search filters
            
        Returns:
            RAGResults with documents, citations, and confidence scores
        """
        if self._cached_tool:
            return await self._cached_tool.search(
                query=query,
                max_results=max_results or self.max_results,
                include_low_confidence=include_low_confidence,
                filters=filters
            )
        
        return await self._perform_search(query, max_results, include_low_confidence, filters)
    
    async def _perform_search(
        self,
        query: str,
        max_results: Optional[int] = None,
        include_low_confidence: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> RAGResults:
        """Perform the actual search without caching."""
        max_results = max_results or self.max_results
        
        try:
            # Perform vector similarity search
            raw_results = await self.chromadb_manager.search_similar(
                query=query,
                n_results=max_results * 2,  # Get more to filter
                filters=filters
            )
            
            # Process results
            processed_results = await self._process_search_results(
                query=query,
                raw_results=raw_results,
                include_low_confidence=include_low_confidence
            )
            
            # Limit to max_results
            processed_results.documents = processed_results.documents[:max_results]
            processed_results.citations = processed_results.citations[:max_results]
            processed_results.confidence_scores = processed_results.confidence_scores[:max_results]
            
            logger.info(f"RAG search completed: {len(processed_results.documents)} results for query '{query}'")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error during RAG search: {e}")
            return RAGResults(
                documents=[],
                citations=[],
                confidence_scores=[],
                search_metadata={"error": str(e), "query": query}
            )
    
    async def _process_search_results(
        self,
        query: str,
        raw_results: Dict[str, Any],
        include_low_confidence: bool = False
    ) -> RAGResults:
        """Process raw search results into RAGResults format."""
        documents = []
        citations = []
        confidence_scores = []
        
        if not raw_results.get("documents"):
            return RAGResults(
                documents=documents,
                citations=citations,
                confidence_scores=confidence_scores,
                search_metadata={"query": query, "total_results": 0}
            )
        
        for doc, metadata, similarity_score in zip(
            raw_results["documents"],
            raw_results.get("metadatas", []),
            raw_results.get("distances", [])
        ):
            # Convert distance to similarity if needed
            if isinstance(similarity_score, float) and similarity_score > 1.0:
                similarity_score = max(0.0, 1.0 - similarity_score)
            
            # Calculate confidence score
            confidence = self.confidence_scorer.calculate_confidence(
                similarity_score=similarity_score,
                metadata=metadata or {},
                query=query
            )
            
            # Filter by confidence threshold
            if not include_low_confidence and confidence < self.confidence_threshold:
                continue
            
            # Create Document object
            document = Document(
                content=doc,
                metadata=metadata or {},
                score=confidence,
                source=metadata.get("source", "unknown") if metadata else "unknown"
            )
            documents.append(document)
            
            # Create Citation if possible
            if metadata and "title" in metadata and "url" in metadata:
                citation = Citation(
                    source=metadata.get("source", "unknown"),
                    title=metadata.get("title", ""),
                    authors=metadata.get("authors", []),
                    publication_date=metadata.get("publication_date"),
                    url=metadata.get("url", ""),
                    excerpt=doc[:200] + "..." if len(doc) > 200 else doc,
                    relevance_score=confidence,
                    doi=metadata.get("doi")
                )
                citations.append(citation)
            
            confidence_scores.append(confidence)
        
        # Sort by confidence score
        sorted_results = sorted(
            zip(documents, citations, confidence_scores),
            key=lambda x: x[2],
            reverse=True
        )
        
        if sorted_results:
            documents, citations, confidence_scores = zip(*sorted_results)
            documents = list(documents)
            citations = list(citations)
            confidence_scores = list(confidence_scores)
        
        return RAGResults(
            documents=documents,
            citations=citations,
            confidence_scores=confidence_scores,
            search_metadata={
                "query": query,
                "total_results": len(documents),
                "confidence_threshold": self.confidence_threshold,
                "include_low_confidence": include_low_confidence
            }
        )
    
    async def get_authoritative_sources(
        self,
        topic: str,
        max_sources: int = 5
    ) -> List[Citation]:
        """Get most authoritative sources for a topic."""
        if self._cached_tool:
            return await self._cached_tool.get_authoritative_sources(topic, max_sources)
        
        authoritative_results = await self.knowledge_base.get_authoritative_sources(
            topic=topic,
            max_results=max_sources
        )
        
        return [result["citation"] for result in authoritative_results]
    
    async def search_by_specialty(
        self,
        query: str,
        specialty: str,
        max_results: int = 10
    ) -> RAGResults:
        """
        Search for medical information filtered by specialty.
        
        Args:
            query: Search query
            specialty: Medical specialty filter
            max_results: Maximum results to return
            
        Returns:
            RAGResults filtered by specialty
        """
        filters = {"medical_specialty": specialty}
        return await self.search(
            query=query,
            max_results=max_results,
            filters=filters
        )
    
    async def search_by_source(
        self,
        query: str,
        source: str,
        max_results: int = 10
    ) -> RAGResults:
        """
        Search for medical information filtered by source.
        
        Args:
            query: Search query
            source: Source filter (e.g., 'pubmed', 'who', 'cdc')
            max_results: Maximum results to return
            
        Returns:
            RAGResults filtered by source
        """
        filters = {"source": source}
        return await self.search(
            query=query,
            max_results=max_results,
            filters=filters
        )
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        return await self.chromadb_manager.get_collection_stats()


# Factory function for creating RAG search tool
def create_rag_search_tool(
    chromadb_manager: Optional[ChromaDBManager] = None,
    cache_manager: Optional[CacheManager] = None,
    confidence_threshold: float = 0.7,
    enable_caching: bool = True
) -> RAGSearchTool:
    """
    Create RAG search tool with default configuration.
    
    Args:
        chromadb_manager: ChromaDB manager (creates default if None)
        cache_manager: Cache manager (creates default if None)
        confidence_threshold: Confidence threshold for results
        enable_caching: Whether to enable caching
        
    Returns:
        Configured RAG search tool
    """
    if chromadb_manager is None:
        chromadb_manager = ChromaDBManager()
    
    if cache_manager is None and enable_caching:
        from .caching import create_cache_manager
        cache_manager = create_cache_manager()
    
    return RAGSearchTool(
        chromadb_manager=chromadb_manager,
        cache_manager=cache_manager,
        confidence_threshold=confidence_threshold,
        enable_caching=enable_caching
    )
