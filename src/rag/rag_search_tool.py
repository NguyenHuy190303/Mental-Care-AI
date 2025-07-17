"""
RAG Search Tool with vector similarity search functionality and citation extraction.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import re

from .chromadb_integration import ChromaDBManager, MedicalKnowledgeBase
from .document_ingestion import DocumentIngestionPipeline

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation information for medical sources."""
    title: str
    authors: List[str]
    source: str
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    document_type: str = "document"
    medical_specialty: Optional[str] = None
    section: str = "main"
    confidence_score: float = 1.0
    relevance_score: float = 1.0
    excerpt: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary."""
        return {
            "title": self.title,
            "authors": self.authors,
            "source": self.source,
            "publication_date": self.publication_date,
            "doi": self.doi,
            "url": self.url,
            "document_type": self.document_type,
            "medical_specialty": self.medical_specialty,
            "section": self.section,
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score,
            "excerpt": self.excerpt
        }
    
    def format_citation(self, style: str = "apa") -> str:
        """Format citation in specified style."""
        if style.lower() == "apa":
            return self._format_apa()
        elif style.lower() == "mla":
            return self._format_mla()
        else:
            return self._format_simple()
    
    def _format_apa(self) -> str:
        """Format citation in APA style."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += ", et al."
        
        year = ""
        if self.publication_date:
            try:
                year = f"({self.publication_date[:4]})"
            except:
                year = f"({self.publication_date})"
        
        citation = f"{authors_str} {year}. {self.title}."
        
        if self.url:
            citation += f" Retrieved from {self.url}"
        elif self.doi:
            citation += f" doi:{self.doi}"
        
        return citation
    
    def _format_mla(self) -> str:
        """Format citation in MLA style."""
        if self.authors:
            author = self.authors[0]
            if "," not in author:
                # Assume "First Last" format, convert to "Last, First"
                parts = author.split()
                if len(parts) >= 2:
                    author = f"{parts[-1]}, {' '.join(parts[:-1])}"
        else:
            author = "Unknown Author"
        
        citation = f"{author}. \"{self.title}.\""
        
        if self.source:
            citation += f" {self.source.title()},"
        
        if self.publication_date:
            citation += f" {self.publication_date},"
        
        if self.url:
            citation += f" {self.url}."
        
        return citation
    
    def _format_simple(self) -> str:
        """Format citation in simple style."""
        return f"{self.title} - {', '.join(self.authors[:2])} ({self.source})"


@dataclass
class RAGSearchResult:
    """Result from RAG search with documents and citations."""
    query: str
    documents: List[str]
    citations: List[Citation]
    confidence_scores: List[float]
    search_metadata: Dict[str, Any]
    total_results: int
    search_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "query": self.query,
            "documents": self.documents,
            "citations": [citation.to_dict() for citation in self.citations],
            "confidence_scores": self.confidence_scores,
            "search_metadata": self.search_metadata,
            "total_results": self.total_results,
            "search_timestamp": self.search_timestamp
        }
    
    def get_high_confidence_results(self, threshold: float = 0.7) -> 'RAGSearchResult':
        """Filter results to only high-confidence matches."""
        filtered_docs = []
        filtered_citations = []
        filtered_scores = []
        
        for doc, citation, score in zip(self.documents, self.citations, self.confidence_scores):
            if score >= threshold:
                filtered_docs.append(doc)
                filtered_citations.append(citation)
                filtered_scores.append(score)
        
        return RAGSearchResult(
            query=self.query,
            documents=filtered_docs,
            citations=filtered_citations,
            confidence_scores=filtered_scores,
            search_metadata=self.search_metadata,
            total_results=len(filtered_docs),
            search_timestamp=self.search_timestamp
        )
    
    def get_citations_by_source(self, source: str) -> List[Citation]:
        """Get citations filtered by source."""
        return [citation for citation in self.citations if citation.source == source]
    
    def get_unique_sources(self) -> List[str]:
        """Get list of unique sources in results."""
        return list(set(citation.source for citation in self.citations))


class ConfidenceScorer:
    """Calculate confidence scores for search results."""
    
    def __init__(self):
        # Source reliability weights
        self.source_weights = {
            "pubmed": 1.0,
            "who": 0.95,
            "cdc": 0.95,
            "manual": 0.8,
            "unknown": 0.5
        }
        
        # Document type weights
        self.type_weights = {
            "research_paper": 1.0,
            "guideline": 0.9,
            "fact_sheet": 0.85,
            "document": 0.8
        }
        
        # Recency weights (newer is better for medical info)
        self.recency_weights = {
            "2020-": 1.0,  # 2020 and later
            "2015-2019": 0.95,
            "2010-2014": 0.9,
            "2005-2009": 0.85,
            "-2004": 0.8  # Before 2005
        }
    
    def calculate_confidence(
        self,
        similarity_score: float,
        metadata: Dict[str, Any],
        query: str
    ) -> float:
        """
        Calculate overall confidence score for a search result.
        
        Args:
            similarity_score: Vector similarity score (0-1)
            metadata: Document metadata
            query: Original search query
            
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
        
        # Combine factors
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
            return 0.7  # Default for unknown dates
        
        try:
            year = int(publication_date[:4])
            if year >= 2020:
                return self.recency_weights["2020-"]
            elif year >= 2015:
                return self.recency_weights["2015-2019"]
            elif year >= 2010:
                return self.recency_weights["2010-2014"]
            elif year >= 2005:
                return self.recency_weights["2005-2009"]
            else:
                return self.recency_weights["-2004"]
        except:
            return 0.7
    
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
        keywords_str = metadata.get("keywords", "[]")
        try:
            keywords = json.loads(keywords_str) if isinstance(keywords_str, str) else keywords_str
            keyword_matches = sum(1 for keyword in keywords if any(word in keyword.lower() for word in query_lower.split()))
            keyword_relevance = min(0.3, keyword_matches * 0.1)
        except:
            keyword_relevance = 0.0
        
        return min(1.0, title_relevance * 0.6 + specialty_relevance + keyword_relevance)
    
    def _calculate_citation_quality(self, metadata: Dict[str, Any]) -> float:
        """Calculate citation quality factor."""
        quality = 0.5  # Base quality
        
        # Has DOI
        if metadata.get("doi"):
            quality += 0.2
        
        # Has URL
        if metadata.get("url"):
            quality += 0.1
        
        # Has authors
        authors_str = metadata.get("authors", "[]")
        try:
            authors = json.loads(authors_str) if isinstance(authors_str, str) else authors_str
            if authors and len(authors) > 0 and authors[0] != "Unknown":
                quality += 0.2
        except:
            pass
        
        return min(1.0, quality)


class RAGSearchTool:
    """Main RAG search tool with vector similarity search and citation extraction."""
    
    def __init__(
        self,
        chromadb_manager: ChromaDBManager,
        confidence_threshold: float = 0.7,
        max_results: int = 10
    ):
        self.chromadb_manager = chromadb_manager
        self.knowledge_base = MedicalKnowledgeBase(chromadb_manager, confidence_threshold)
        self.confidence_scorer = ConfidenceScorer()
        self.confidence_threshold = confidence_threshold
        self.max_results = max_results
        
        logger.info("RAG Search Tool initialized")
    
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: Optional[int] = None,
        include_low_confidence: bool = False
    ) -> RAGSearchResult:
        """
        Perform RAG search with vector similarity.
        
        Args:
            query: Search query
            filters: Optional metadata filters
            max_results: Maximum number of results (overrides default)
            include_low_confidence: Whether to include low-confidence results
            
        Returns:
            RAGSearchResult with documents and citations
        """
        search_start = datetime.utcnow()
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
            processed_results = self._limit_results(processed_results, max_results)
            
            search_duration = (datetime.utcnow() - search_start).total_seconds()
            
            return RAGSearchResult(
                query=query,
                documents=processed_results["documents"],
                citations=processed_results["citations"],
                confidence_scores=processed_results["confidence_scores"],
                search_metadata={
                    "search_duration_seconds": search_duration,
                    "filters_applied": filters or {},
                    "confidence_threshold": self.confidence_threshold,
                    "include_low_confidence": include_low_confidence,
                    "total_candidates": len(raw_results["documents"])
                },
                total_results=len(processed_results["documents"]),
                search_timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error during RAG search: {e}")
            return RAGSearchResult(
                query=query,
                documents=[],
                citations=[],
                confidence_scores=[],
                search_metadata={"error": str(e)},
                total_results=0,
                search_timestamp=datetime.utcnow().isoformat()
            )
    
    async def _process_search_results(
        self,
        query: str,
        raw_results: Dict[str, Any],
        include_low_confidence: bool = False
    ) -> Dict[str, Any]:
        """Process raw search results and calculate confidence scores."""
        if not raw_results["documents"]:
            return {"documents": [], "citations": [], "confidence_scores": []}
        
        documents = []
        citations = []
        confidence_scores = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            raw_results["documents"],
            raw_results["metadatas"],
            raw_results["distances"]
        )):
            # Calculate similarity score (1 - distance)
            similarity_score = max(0.0, 1.0 - distance)
            
            # Calculate overall confidence
            confidence = self.confidence_scorer.calculate_confidence(
                similarity_score=similarity_score,
                metadata=metadata,
                query=query
            )
            
            # Filter by confidence threshold
            if not include_low_confidence and confidence < self.confidence_threshold:
                continue
            
            # Create citation
            citation = self._create_citation(metadata, doc, confidence, similarity_score)
            
            documents.append(doc)
            citations.append(citation)
            confidence_scores.append(confidence)
        
        return {
            "documents": documents,
            "citations": citations,
            "confidence_scores": confidence_scores
        }
    
    def _create_citation(
        self,
        metadata: Dict[str, Any],
        document_text: str,
        confidence_score: float,
        relevance_score: float
    ) -> Citation:
        """Create Citation object from metadata."""
        # Parse authors
        authors_str = metadata.get("authors", "[]")
        try:
            authors = json.loads(authors_str) if isinstance(authors_str, str) else authors_str
            if not authors or authors == ["Unknown"]:
                authors = ["Unknown Author"]
        except:
            authors = ["Unknown Author"]
        
        # Create excerpt from document text
        excerpt = self._create_excerpt(document_text, max_length=200)
        
        return Citation(
            title=metadata.get("title", "Unknown Title"),
            authors=authors,
            source=metadata.get("source", "unknown"),
            publication_date=metadata.get("publication_date"),
            doi=metadata.get("doi"),
            url=metadata.get("url"),
            document_type=metadata.get("document_type", "document"),
            medical_specialty=metadata.get("medical_specialty"),
            section=metadata.get("section", "main"),
            confidence_score=confidence_score,
            relevance_score=relevance_score,
            excerpt=excerpt
        )
    
    def _create_excerpt(self, text: str, max_length: int = 200) -> str:
        """Create a relevant excerpt from document text."""
        if len(text) <= max_length:
            return text
        
        # Try to find a good breaking point
        excerpt = text[:max_length]
        
        # Find last sentence boundary
        last_sentence = max(
            excerpt.rfind('.'),
            excerpt.rfind('!'),
            excerpt.rfind('?')
        )
        
        if last_sentence > max_length * 0.7:  # If we found a good break point
            excerpt = excerpt[:last_sentence + 1]
        else:
            # Find last word boundary
            last_space = excerpt.rfind(' ')
            if last_space > max_length * 0.8:
                excerpt = excerpt[:last_space] + "..."
            else:
                excerpt = excerpt + "..."
        
        return excerpt.strip()
    
    def _limit_results(
        self,
        results: Dict[str, Any],
        max_results: int
    ) -> Dict[str, Any]:
        """Limit results to maximum number."""
        if len(results["documents"]) <= max_results:
            return results
        
        return {
            "documents": results["documents"][:max_results],
            "citations": results["citations"][:max_results],
            "confidence_scores": results["confidence_scores"][:max_results]
        }
    
    async def search_by_medical_specialty(
        self,
        query: str,
        specialty: str,
        max_results: Optional[int] = None
    ) -> RAGSearchResult:
        """Search within a specific medical specialty."""
        filters = {"medical_specialty": specialty}
        return await self.search(
            query=query,
            filters=filters,
            max_results=max_results
        )
    
    async def search_by_source(
        self,
        query: str,
        source: str,
        max_results: Optional[int] = None
    ) -> RAGSearchResult:
        """Search within a specific source (pubmed, who, cdc)."""
        filters = {"source": source}
        return await self.search(
            query=query,
            filters=filters,
            max_results=max_results
        )
    
    async def search_recent_research(
        self,
        query: str,
        years_back: int = 5,
        max_results: Optional[int] = None
    ) -> RAGSearchResult:
        """Search for recent research papers."""
        current_year = datetime.now().year
        min_year = current_year - years_back
        
        # This would require a more sophisticated date filtering approach
        # For now, we'll search and then filter results
        results = await self.search(query=query, max_results=(max_results or 10) * 2)
        
        # Filter by publication date
        filtered_docs = []
        filtered_citations = []
        filtered_scores = []
        
        for doc, citation, score in zip(results.documents, results.citations, results.confidence_scores):
            if citation.publication_date:
                try:
                    pub_year = int(citation.publication_date[:4])
                    if pub_year >= min_year:
                        filtered_docs.append(doc)
                        filtered_citations.append(citation)
                        filtered_scores.append(score)
                except:
                    # Include if we can't parse the date
                    filtered_docs.append(doc)
                    filtered_citations.append(citation)
                    filtered_scores.append(score)
            else:
                # Include if no date available
                filtered_docs.append(doc)
                filtered_citations.append(citation)
                filtered_scores.append(score)
        
        # Limit results
        max_results = max_results or self.max_results
        filtered_docs = filtered_docs[:max_results]
        filtered_citations = filtered_citations[:max_results]
        filtered_scores = filtered_scores[:max_results]
        
        return RAGSearchResult(
            query=query,
            documents=filtered_docs,
            citations=filtered_citations,
            confidence_scores=filtered_scores,
            search_metadata={
                "filter_type": "recent_research",
                "years_back": years_back,
                "min_year": min_year
            },
            total_results=len(filtered_docs),
            search_timestamp=datetime.utcnow().isoformat()
        )
    
    async def get_authoritative_sources(
        self,
        topic: str,
        max_sources: int = 5
    ) -> List[Citation]:
        """Get most authoritative sources for a topic."""
        authoritative_results = await self.knowledge_base.get_authoritative_sources(
            topic=topic,
            max_results=max_sources
        )
        
        return [result["citation"] for result in authoritative_results]


# Example usage and testing
async def main():
    """Example usage of RAG Search Tool."""
    from .chromadb_integration import ChromaDBManager
    
    # Initialize components
    chromadb_manager = ChromaDBManager()
    rag_tool = RAGSearchTool(chromadb_manager)
    
    # Example searches
    queries = [
        "depression treatment options",
        "anxiety therapy techniques",
        "mental health medication side effects"
    ]
    
    for query in queries:
        print(f"\n--- Search: {query} ---")
        results = await rag_tool.search(query, max_results=3)
        
        print(f"Found {results.total_results} results")
        for i, citation in enumerate(results.citations):
            print(f"{i+1}. {citation.title}")
            print(f"   Authors: {', '.join(citation.authors[:2])}")
            print(f"   Source: {citation.source} | Confidence: {citation.confidence_score:.2f}")
            print(f"   Excerpt: {citation.excerpt[:100]}...")
            print()


if __name__ == "__main__":
    asyncio.run(main())