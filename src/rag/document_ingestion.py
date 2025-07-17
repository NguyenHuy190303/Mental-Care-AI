"""
Document ingestion pipeline for medical knowledge sources.
Handles PubMed, WHO, CDC, and other medical document sources.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

import aiofiles
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Metadata for medical documents with citation information."""
    source: str  # "pubmed", "who", "cdc", "manual"
    document_type: str  # "research_paper", "guideline", "fact_sheet"
    title: str
    authors: List[str]
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    medical_specialty: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    language: str = "en"
    confidence_score: float = 1.0
    ingestion_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ProcessedDocument:
    """Processed document ready for embedding and storage."""
    content: str
    metadata: DocumentMetadata
    chunks: List[str]
    chunk_metadata: List[Dict[str, Any]]
    document_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": asdict(self.metadata),
            "chunks": self.chunks,
            "chunk_metadata": self.chunk_metadata,
            "document_hash": self.document_hash
        }


class TextChunker:
    """Intelligent text chunking for medical documents."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        preserve_sections: bool = True
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_sections = preserve_sections
        
        # Medical section headers to preserve
        self.section_headers = [
            "abstract", "introduction", "methods", "results", "discussion",
            "conclusion", "background", "objective", "findings", "limitations",
            "clinical implications", "recommendations", "summary"
        ]
    
    def chunk_text(self, text: str, metadata: DocumentMetadata) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Chunk text while preserving medical document structure.
        
        Returns:
            Tuple of (chunks, chunk_metadata)
        """
        if self.preserve_sections and metadata.document_type == "research_paper":
            return self._chunk_with_sections(text, metadata)
        else:
            return self._chunk_simple(text, metadata)
    
    def _chunk_with_sections(self, text: str, metadata: DocumentMetadata) -> tuple[List[str], List[Dict[str, Any]]]:
        """Chunk text preserving medical paper sections."""
        chunks = []
        chunk_metadata = []
        
        # Split by common medical paper sections
        sections = self._identify_sections(text)
        
        for section_name, section_text in sections.items():
            if len(section_text.strip()) < 50:  # Skip very short sections
                continue
                
            section_chunks = self._split_text(section_text, self.chunk_size, self.chunk_overlap)
            
            for i, chunk in enumerate(section_chunks):
                chunks.append(chunk)
                chunk_metadata.append({
                    "section": section_name,
                    "chunk_index": i,
                    "total_chunks_in_section": len(section_chunks),
                    "source": metadata.source,
                    "document_type": metadata.document_type,
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "medical_specialty": metadata.medical_specialty
                })
        
        return chunks, chunk_metadata
    
    def _chunk_simple(self, text: str, metadata: DocumentMetadata) -> tuple[List[str], List[Dict[str, Any]]]:
        """Simple text chunking for non-research documents."""
        chunks = self._split_text(text, self.chunk_size, self.chunk_overlap)
        chunk_metadata = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source": metadata.source,
                "document_type": metadata.document_type,
                "title": metadata.title,
                "authors": metadata.authors,
                "medical_specialty": metadata.medical_specialty
            })
        
        return chunks, chunk_metadata
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """Identify and extract sections from medical papers."""
        sections = {"main": text}  # Default fallback
        
        # Simple section detection based on headers
        lines = text.split('\n')
        current_section = "introduction"
        current_content = []
        sections = {}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if line is a section header
            is_header = False
            for header in self.section_headers:
                if header in line_lower and len(line.strip()) < 100:
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = header
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Save final section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                for i in range(min(100, len(text) - end)):
                    if text[end + i] in '.!?':
                        end = end + i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks


class PubMedIngester:
    """Ingester for PubMed research papers."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.rate_limit_delay = 0.34  # NCBI rate limit: 3 requests per second
    
    async def search_and_ingest(
        self,
        query: str,
        max_results: int = 100,
        date_range: Optional[str] = None
    ) -> List[ProcessedDocument]:
        """
        Search PubMed and ingest matching papers.
        
        Args:
            query: Search query (e.g., "mental health treatment")
            max_results: Maximum number of papers to retrieve
            date_range: Date range filter (e.g., "2020:2024")
        """
        logger.info(f"Searching PubMed for: {query}")
        
        # Search for paper IDs
        paper_ids = await self._search_pubmed(query, max_results, date_range)
        
        # Fetch paper details
        documents = []
        for paper_id in paper_ids:
            try:
                doc = await self._fetch_paper_details(paper_id)
                if doc:
                    documents.append(doc)
                await asyncio.sleep(self.rate_limit_delay)
            except Exception as e:
                logger.error(f"Error fetching paper {paper_id}: {e}")
                continue
        
        logger.info(f"Successfully ingested {len(documents)} papers from PubMed")
        return documents
    
    async def _search_pubmed(
        self,
        query: str,
        max_results: int,
        date_range: Optional[str] = None
    ) -> List[str]:
        """Search PubMed for paper IDs."""
        search_url = f"{self.base_url}esearch.fcgi"
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }
        
        if date_range:
            params["datetype"] = "pdat"
            params["mindate"] = date_range.split(":")[0]
            params["maxdate"] = date_range.split(":")[1] if ":" in date_range else date_range.split(":")[0]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])
    
    async def _fetch_paper_details(self, paper_id: str) -> Optional[ProcessedDocument]:
        """Fetch detailed information for a specific paper."""
        fetch_url = f"{self.base_url}efetch.fcgi"
        
        params = {
            "db": "pubmed",
            "id": paper_id,
            "retmode": "xml"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(fetch_url, params=params)
            response.raise_for_status()
            
            # Parse XML response (simplified - would need proper XML parsing)
            xml_content = response.text
            
            # Extract basic information (this is a simplified version)
            # In production, you'd use proper XML parsing
            metadata = self._parse_pubmed_xml(xml_content, paper_id)
            
            if not metadata:
                return None
            
            # Create processed document
            content = f"{metadata.title}\n\n{metadata.abstract or ''}"
            
            chunker = TextChunker()
            chunks, chunk_metadata = chunker.chunk_text(content, metadata)
            
            document_hash = hashlib.sha256(content.encode()).hexdigest()
            
            return ProcessedDocument(
                content=content,
                metadata=metadata,
                chunks=chunks,
                chunk_metadata=chunk_metadata,
                document_hash=document_hash
            )
    
    def _parse_pubmed_xml(self, xml_content: str, paper_id: str) -> Optional[DocumentMetadata]:
        """Parse PubMed XML response (simplified version)."""
        # This is a simplified parser - in production you'd use lxml or similar
        try:
            # Extract title (very basic extraction)
            title_start = xml_content.find("<ArticleTitle>")
            title_end = xml_content.find("</ArticleTitle>")
            title = "Unknown Title"
            if title_start != -1 and title_end != -1:
                title = xml_content[title_start + 14:title_end].strip()
            
            # Extract abstract
            abstract_start = xml_content.find("<AbstractText>")
            abstract_end = xml_content.find("</AbstractText>")
            abstract = None
            if abstract_start != -1 and abstract_end != -1:
                abstract = xml_content[abstract_start + 14:abstract_end].strip()
            
            return DocumentMetadata(
                source="pubmed",
                document_type="research_paper",
                title=title,
                authors=["Unknown"],  # Would extract from XML
                abstract=abstract,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{paper_id}/",
                medical_specialty="general"
            )
        except Exception as e:
            logger.error(f"Error parsing PubMed XML for {paper_id}: {e}")
            return None


class WHOIngester:
    """Ingester for WHO guidelines and fact sheets."""
    
    def __init__(self):
        self.base_url = "https://www.who.int"
    
    async def ingest_guidelines(self, topics: List[str]) -> List[ProcessedDocument]:
        """
        Ingest WHO guidelines for specified topics.
        
        Args:
            topics: List of health topics (e.g., ["mental-health", "depression"])
        """
        documents = []
        
        for topic in topics:
            try:
                topic_docs = await self._fetch_topic_documents(topic)
                documents.extend(topic_docs)
            except Exception as e:
                logger.error(f"Error ingesting WHO documents for {topic}: {e}")
        
        return documents
    
    async def _fetch_topic_documents(self, topic: str) -> List[ProcessedDocument]:
        """Fetch WHO documents for a specific topic."""
        # This is a placeholder - in production you'd implement proper WHO API integration
        # or web scraping with proper rate limiting and robots.txt compliance
        
        # For now, return sample document structure
        sample_content = f"""
        WHO Guidelines on {topic.replace('-', ' ').title()}
        
        This document provides evidence-based recommendations for healthcare providers
        and policymakers regarding {topic.replace('-', ' ')}.
        
        Key recommendations:
        1. Early identification and intervention
        2. Integrated care approaches
        3. Community-based support systems
        4. Training for healthcare workers
        
        Implementation considerations:
        - Resource requirements
        - Training needs
        - Monitoring and evaluation
        """
        
        metadata = DocumentMetadata(
            source="who",
            document_type="guideline",
            title=f"WHO Guidelines on {topic.replace('-', ' ').title()}",
            authors=["World Health Organization"],
            url=f"https://www.who.int/publications/guidelines/{topic}",
            medical_specialty=topic.replace('-', '_')
        )
        
        chunker = TextChunker()
        chunks, chunk_metadata = chunker.chunk_text(sample_content, metadata)
        
        document_hash = hashlib.sha256(sample_content.encode()).hexdigest()
        
        return [ProcessedDocument(
            content=sample_content,
            metadata=metadata,
            chunks=chunks,
            chunk_metadata=chunk_metadata,
            document_hash=document_hash
        )]


class CDCIngester:
    """Ingester for CDC fact sheets and guidelines."""
    
    def __init__(self):
        self.base_url = "https://www.cdc.gov"
    
    async def ingest_fact_sheets(self, topics: List[str]) -> List[ProcessedDocument]:
        """
        Ingest CDC fact sheets for specified topics.
        
        Args:
            topics: List of health topics
        """
        documents = []
        
        for topic in topics:
            try:
                topic_docs = await self._fetch_topic_fact_sheets(topic)
                documents.extend(topic_docs)
            except Exception as e:
                logger.error(f"Error ingesting CDC documents for {topic}: {e}")
        
        return documents
    
    async def _fetch_topic_fact_sheets(self, topic: str) -> List[ProcessedDocument]:
        """Fetch CDC fact sheets for a specific topic."""
        # Placeholder implementation - would integrate with CDC APIs or web scraping
        
        sample_content = f"""
        CDC Fact Sheet: {topic.replace('-', ' ').title()}
        
        Overview:
        This fact sheet provides essential information about {topic.replace('-', ' ')}
        based on current scientific evidence and public health recommendations.
        
        Key Facts:
        - Prevalence and impact
        - Risk factors and prevention
        - Treatment and management options
        - Public health implications
        
        Prevention Strategies:
        1. Primary prevention approaches
        2. Early detection and screening
        3. Community-based interventions
        4. Policy recommendations
        
        Resources:
        - Healthcare provider resources
        - Patient education materials
        - Community program guidelines
        """
        
        metadata = DocumentMetadata(
            source="cdc",
            document_type="fact_sheet",
            title=f"CDC Fact Sheet: {topic.replace('-', ' ').title()}",
            authors=["Centers for Disease Control and Prevention"],
            url=f"https://www.cdc.gov/factsheets/{topic}",
            medical_specialty=topic.replace('-', '_')
        )
        
        chunker = TextChunker()
        chunks, chunk_metadata = chunker.chunk_text(sample_content, metadata)
        
        document_hash = hashlib.sha256(sample_content.encode()).hexdigest()
        
        return [ProcessedDocument(
            content=sample_content,
            metadata=metadata,
            chunks=chunks,
            chunk_metadata=chunk_metadata,
            document_hash=document_hash
        )]


class DocumentIngestionPipeline:
    """Main pipeline for ingesting medical documents from multiple sources."""
    
    def __init__(self, storage_path: str = "data/ingestion_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ingesters
        self.pubmed_ingester = PubMedIngester()
        self.who_ingester = WHOIngester()
        self.cdc_ingester = CDCIngester()
        
        # Initialize chunker
        self.chunker = TextChunker()
    
    async def ingest_all_sources(
        self,
        pubmed_queries: List[str] = None,
        who_topics: List[str] = None,
        cdc_topics: List[str] = None
    ) -> List[ProcessedDocument]:
        """
        Ingest documents from all configured sources.
        
        Args:
            pubmed_queries: List of PubMed search queries
            who_topics: List of WHO topics to ingest
            cdc_topics: List of CDC topics to ingest
        """
        all_documents = []
        
        # Default queries/topics for mental health
        if pubmed_queries is None:
            pubmed_queries = [
                "mental health treatment",
                "depression therapy",
                "anxiety disorders",
                "cognitive behavioral therapy",
                "psychiatric medications"
            ]
        
        if who_topics is None:
            who_topics = ["mental-health", "depression", "anxiety", "suicide-prevention"]
        
        if cdc_topics is None:
            cdc_topics = ["mental-health", "depression", "anxiety", "stress-management"]
        
        # Ingest from PubMed
        logger.info("Starting PubMed ingestion...")
        for query in pubmed_queries:
            try:
                docs = await self.pubmed_ingester.search_and_ingest(query, max_results=20)
                all_documents.extend(docs)
            except Exception as e:
                logger.error(f"Error with PubMed query '{query}': {e}")
        
        # Ingest from WHO
        logger.info("Starting WHO ingestion...")
        try:
            who_docs = await self.who_ingester.ingest_guidelines(who_topics)
            all_documents.extend(who_docs)
        except Exception as e:
            logger.error(f"Error with WHO ingestion: {e}")
        
        # Ingest from CDC
        logger.info("Starting CDC ingestion...")
        try:
            cdc_docs = await self.cdc_ingester.ingest_fact_sheets(cdc_topics)
            all_documents.extend(cdc_docs)
        except Exception as e:
            logger.error(f"Error with CDC ingestion: {e}")
        
        # Save processed documents
        await self._save_documents(all_documents)
        
        logger.info(f"Ingestion complete. Total documents: {len(all_documents)}")
        return all_documents
    
    async def ingest_local_documents(self, file_paths: List[str]) -> List[ProcessedDocument]:
        """
        Ingest documents from local files.
        
        Args:
            file_paths: List of paths to local document files
        """
        documents = []
        
        for file_path in file_paths:
            try:
                doc = await self._process_local_file(file_path)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Error processing local file {file_path}: {e}")
        
        await self._save_documents(documents)
        return documents
    
    async def _process_local_file(self, file_path: str) -> Optional[ProcessedDocument]:
        """Process a single local file."""
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Read file content
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Create metadata
        metadata = DocumentMetadata(
            source="manual",
            document_type="document",
            title=path.stem,
            authors=["Unknown"],
            url=f"file://{path.absolute()}",
            medical_specialty="general"
        )
        
        # Chunk content
        chunks, chunk_metadata = self.chunker.chunk_text(content, metadata)
        
        # Create document hash
        document_hash = hashlib.sha256(content.encode()).hexdigest()
        
        return ProcessedDocument(
            content=content,
            metadata=metadata,
            chunks=chunks,
            chunk_metadata=chunk_metadata,
            document_hash=document_hash
        )
    
    async def _save_documents(self, documents: List[ProcessedDocument]):
        """Save processed documents to storage."""
        for doc in documents:
            # Create filename from document hash
            filename = f"{doc.document_hash}.json"
            file_path = self.storage_path / filename
            
            # Save document
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(doc.to_dict(), indent=2, ensure_ascii=False))
        
        logger.info(f"Saved {len(documents)} documents to {self.storage_path}")
    
    async def load_processed_documents(self) -> List[ProcessedDocument]:
        """Load all processed documents from storage."""
        documents = []
        
        for file_path in self.storage_path.glob("*.json"):
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    data = json.loads(await f.read())
                
                # Reconstruct ProcessedDocument
                doc = ProcessedDocument(
                    content=data["content"],
                    metadata=DocumentMetadata(**data["metadata"]),
                    chunks=data["chunks"],
                    chunk_metadata=data["chunk_metadata"],
                    document_hash=data["document_hash"]
                )
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error loading document from {file_path}: {e}")
        
        return documents


# Example usage
async def main():
    """Example usage of the document ingestion pipeline."""
    pipeline = DocumentIngestionPipeline()
    
    # Ingest from all sources
    documents = await pipeline.ingest_all_sources()
    
    print(f"Ingested {len(documents)} documents")
    for doc in documents[:3]:  # Show first 3 documents
        print(f"- {doc.metadata.title} ({doc.metadata.source})")
        print(f"  Chunks: {len(doc.chunks)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())