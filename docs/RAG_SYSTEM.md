# RAG System Documentation

## Overview

Sage uses a sophisticated Retrieval-Augmented Generation (RAG) system to provide scientifically-backed medical information across all healthcare domains. The system ingests documents from authoritative medical sources including research papers, clinical guidelines, and medical literature to provide accurate, citable responses for comprehensive healthcare support.

## Architecture

```
Medical Sources → Document Ingestion → Text Chunking → Vector Storage → RAG Search → Citations
     ↓                    ↓                ↓              ↓            ↓           ↓
  PubMed API         TextChunker      ChromaDB      RAGSearchTool   Response    User
  WHO Guidelines     Metadata         Embeddings    Similarity      with        Interface
  CDC Fact Sheets    Processing       Storage       Search          Sources
```

## Document Ingestion Pipeline

### Supported Sources

1. **PubMed Research Papers**
   - Real-time API integration with NCBI E-utilities
   - Rate limiting compliance (3 requests/second)
   - Full metadata extraction including DOI, authors, abstracts
   - Automatic citation formatting

2. **WHO Guidelines**
   - World Health Organization clinical guidelines
   - Evidence-based recommendations
   - Policy and implementation guidance

3. **CDC Fact Sheets**
   - Centers for Disease Control prevention guidelines
   - Public health recommendations
   - Epidemiological data and statistics

4. **Local Documents**
   - Manual document upload capability
   - Support for text files and PDFs
   - Custom metadata assignment

### Document Processing

#### Intelligent Text Chunking

The system uses medical document structure-aware chunking:

```python
# Medical paper sections preserved
sections = [
    "abstract", "introduction", "methods", "results", 
    "discussion", "conclusion", "clinical implications"
]

# Configurable chunking parameters
chunk_size = 1000        # Characters per chunk
chunk_overlap = 200      # Overlap between chunks
preserve_sections = True # Maintain document structure
```

#### Metadata Management

Each document includes comprehensive metadata:

```python
@dataclass
class DocumentMetadata:
    source: str              # "pubmed", "who", "cdc", "manual"
    document_type: str       # "research_paper", "guideline", "fact_sheet"
    title: str
    authors: List[str]
    publication_date: str
    doi: str                 # Digital Object Identifier
    url: str                 # Direct link to source
    medical_specialty: str   # Medical domain classification
    abstract: str            # Document abstract/summary
    keywords: List[str]      # Medical keywords
    confidence_score: float  # Quality/reliability score
```

## Usage Guide

### Basic Document Ingestion

```python
from src.rag.document_ingestion import DocumentIngestionPipeline

# Initialize the pipeline
pipeline = DocumentIngestionPipeline(storage_path="data/ingestion_storage")

# Ingest from all sources with default queries
documents = await pipeline.ingest_all_sources()

print(f"Ingested {len(documents)} documents")
```

### Custom Source Ingestion

```python
# Custom PubMed queries for comprehensive healthcare
pubmed_queries = [
    "cardiovascular disease treatment guidelines",
    "diabetes management clinical trials",
    "cancer screening recommendations",
    "infectious disease prevention protocols",
    "pediatric care best practices",
    "geriatric medicine evidence-based treatment",
    "emergency medicine protocols",
    "preventive care guidelines"
]

# Custom WHO topics for global health
who_topics = [
    "cardiovascular-health",
    "diabetes-prevention", 
    "cancer-screening",
    "infectious-diseases",
    "maternal-health",
    "child-health",
    "aging-health",
    "emergency-care"
]

# Custom CDC topics for public health
cdc_topics = [
    "heart-disease",
    "diabetes-prevention",
    "cancer-prevention", 
    "infectious-disease-control",
    "vaccination-guidelines",
    "health-screening",
    "chronic-disease-management"
]

# Ingest with custom parameters
documents = await pipeline.ingest_all_sources(
    pubmed_queries=pubmed_queries,
    who_topics=who_topics,
    cdc_topics=cdc_topics
)
```

### Local Document Processing

```python
# Process local medical documents
local_files = [
    "docs/dsm5_excerpts.txt",
    "docs/treatment_guidelines.pdf",
    "docs/clinical_protocols.docx"
]

local_documents = await pipeline.ingest_local_documents(local_files)
```

### Loading Processed Documents

```python
# Load all previously processed documents
all_documents = await pipeline.load_processed_documents()

# Filter by source
pubmed_docs = [doc for doc in all_documents if doc.metadata.source == "pubmed"]
who_docs = [doc for doc in all_documents if doc.metadata.source == "who"]
```

## Document Structure

### ProcessedDocument Format

```python
@dataclass
class ProcessedDocument:
    content: str                    # Full document text
    metadata: DocumentMetadata      # Document metadata
    chunks: List[str]              # Text chunks for embedding
    chunk_metadata: List[Dict]     # Metadata for each chunk
    document_hash: str             # Unique document identifier
```

### Chunk Metadata Structure

Each text chunk includes detailed metadata for precise citation:

```python
chunk_metadata = {
    "section": "results",           # Document section
    "chunk_index": 2,              # Position within section
    "total_chunks_in_section": 5,  # Total chunks in section
    "source": "pubmed",            # Original source
    "document_type": "research_paper",
    "title": "Cognitive Behavioral Therapy for Depression",
    "authors": ["Smith, J.", "Johnson, A."],
    "medical_specialty": "psychiatry"
}
```

## Integration with Vector Database

### ChromaDB Integration (Next Phase)

The ingestion pipeline prepares documents for vector storage:

```python
# Document chunks ready for embedding
for doc in processed_documents:
    for i, chunk in enumerate(doc.chunks):
        # Embed chunk text
        embedding = embedding_model.embed(chunk)
        
        # Store in ChromaDB with metadata
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[doc.chunk_metadata[i]],
            ids=[f"{doc.document_hash}_{i}"]
        )
```

### Search and Retrieval

```python
# Vector similarity search
query = "What are the most effective treatments for depression?"
query_embedding = embedding_model.embed(query)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"source": "pubmed"}  # Filter by source
)

# Results include original text, metadata, and similarity scores
for result in results:
    print(f"Source: {result['metadata']['title']}")
    print(f"Content: {result['document']}")
    print(f"Citation: {result['metadata']['url']}")
```

## Medical Compliance Features

### Rate Limiting

- **PubMed API**: 3 requests per second (NCBI compliance)
- **Exponential backoff** for failed requests
- **Request queuing** to prevent API overload

### Citation Tracking

- **Direct source links** for all medical information
- **Author and publication date** preservation
- **DOI tracking** for academic papers
- **Confidence scoring** based on source authority

### Error Handling

```python
# Comprehensive error handling
try:
    documents = await pipeline.ingest_all_sources()
except PubMedAPIError as e:
    logger.error(f"PubMed API error: {e}")
    # Fallback to cached documents
except NetworkError as e:
    logger.error(f"Network error: {e}")
    # Continue with available sources
except ValidationError as e:
    logger.error(f"Document validation error: {e}")
    # Skip invalid documents
```

## Performance Optimization

### Caching Strategy

- **Document deduplication** using content hashing
- **Metadata caching** for repeated queries
- **Incremental updates** to avoid re-processing

### Async Processing

- **Concurrent API requests** within rate limits
- **Batch processing** for large document sets
- **Progress tracking** for long-running operations

## Configuration

### Environment Variables

```bash
# PubMed API (optional - increases rate limits)
PUBMED_API_KEY=your-ncbi-api-key

# Storage paths
INGESTION_STORAGE_PATH=data/ingestion_storage
CACHE_STORAGE_PATH=data/cache

# Processing parameters
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_DOCUMENTS_PER_QUERY=100
```

### Pipeline Configuration

```python
# Custom chunker configuration
chunker = TextChunker(
    chunk_size=1500,           # Larger chunks for complex documents
    chunk_overlap=300,         # More overlap for context preservation
    preserve_sections=True     # Maintain medical document structure
)

# Custom pipeline with chunker
pipeline = DocumentIngestionPipeline(
    storage_path="custom/path",
    chunker=chunker
)
```

## Monitoring and Logging

### Structured Logging

```python
import logging
logger = logging.getLogger(__name__)

# Automatic logging of ingestion progress
logger.info("Starting PubMed ingestion", extra={
    "query": "depression treatment",
    "max_results": 50,
    "source": "pubmed"
})

logger.info("Ingestion complete", extra={
    "total_documents": 45,
    "processing_time": "2.3s",
    "success_rate": 0.9
})
```

### Metrics Tracking

- **Documents processed per source**
- **Processing time and success rates**
- **API usage and rate limiting**
- **Storage utilization**

## Next Steps

1. **ChromaDB Integration**: Vector storage and similarity search
2. **RAG Search Tool**: Query interface for the knowledge base
3. **Citation Formatter**: Automatic citation generation
4. **Real-time Updates**: Incremental document ingestion
5. **Quality Scoring**: Document relevance and authority ranking

## Troubleshooting

### Common Issues

**PubMed API Rate Limiting**
```python
# Increase delay between requests
pubmed_ingester.rate_limit_delay = 0.5  # 2 requests per second
```

**Memory Usage with Large Documents**
```python
# Reduce chunk size for memory efficiency
chunker = TextChunker(chunk_size=500, chunk_overlap=100)
```

**Network Timeouts**
```python
# Increase HTTP client timeout
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.get(url)
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("src.rag.document_ingestion").setLevel(logging.DEBUG)

# Verbose processing information
pipeline = DocumentIngestionPipeline(debug=True)
```

This RAG system provides the foundation for reliable, scientifically-backed medical information retrieval across all healthcare domains in the Sage comprehensive healthcare support system.