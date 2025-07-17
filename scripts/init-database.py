#!/usr/bin/env python3
"""
Database initialization script for the Mental Health Agent system.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import (
    DatabaseManager, 
    create_tables, 
    migrate_database,
    check_database_health,
    ChromaDBManager
)
from database.encryption import ensure_encryption_key_exists

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_postgresql():
    """Initialize PostgreSQL database."""
    logger.info("Initializing PostgreSQL database...")
    
    # Ensure encryption key exists
    encryption_key = ensure_encryption_key_exists()
    if encryption_key:
        logger.info("Encryption key generated/verified")
    
    # Create database manager
    db_manager = DatabaseManager()
    
    try:
        # Check database connectivity
        if not await check_database_health(db_manager):
            logger.error("Database health check failed")
            return False
        
        # Run migrations
        await migrate_database(db_manager)
        logger.info("PostgreSQL database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}")
        return False
    finally:
        await db_manager.close()


async def initialize_chromadb():
    """Initialize ChromaDB collections."""
    logger.info("Initializing ChromaDB collections...")
    
    try:
        # Create ChromaDB manager
        chroma_manager = ChromaDBManager()
        
        # Check connectivity
        if not chroma_manager.health_check():
            logger.error("ChromaDB health check failed")
            return False
        
        # Initialize collections
        medical_collection = chroma_manager.get_medical_knowledge_collection()
        user_collection = chroma_manager.get_user_contexts_collection()
        
        # Get collection stats
        medical_stats = medical_collection.get_collection_stats()
        logger.info(f"Medical knowledge collection: {medical_stats}")
        
        logger.info("ChromaDB collections initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
        return False


async def test_data_models():
    """Test data model validation."""
    logger.info("Testing data models...")
    
    try:
        from models.validation import validator
        from models.core import UserInput, AnalyzedInput, Citation
        from datetime import datetime
        
        # Test UserInput validation
        user_input_data = {
            "user_id": "test_user_123",
            "session_id": "session_456",
            "type": "text",
            "content": "I have been feeling anxious lately",
            "timestamp": datetime.utcnow(),
            "metadata": {"source": "web_interface"}
        }
        
        user_input = validator.validate_user_input(user_input_data)
        logger.info(f"UserInput validation passed: {user_input.user_id}")
        
        # Test AnalyzedInput validation
        analyzed_input_data = {
            "text": "I have been feeling anxious lately",
            "intent": "emotional_support",
            "medical_entities": ["anxiety"],
            "urgency_level": 3,
            "confidence": 0.85,
            "emotional_context": "distressed"
        }
        
        analyzed_input = validator.validate_analyzed_input(analyzed_input_data)
        logger.info(f"AnalyzedInput validation passed: {analyzed_input.intent}")
        
        # Test Citation validation
        citation_data = {
            "source": "pubmed",
            "title": "Anxiety Disorders: A Review",
            "authors": ["Dr. Smith", "Dr. Johnson"],
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345",
            "excerpt": "Anxiety disorders are common mental health conditions...",
            "relevance_score": 0.92
        }
        
        citation = validator.validate_citation(citation_data)
        logger.info(f"Citation validation passed: {citation.title}")
        
        logger.info("Data model validation tests passed")
        return True
        
    except Exception as e:
        logger.error(f"Data model testing failed: {e}")
        return False


async def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    success = True
    
    # Test data models first
    if not await test_data_models():
        success = False
    
    # Initialize PostgreSQL
    if not await initialize_postgresql():
        success = False
    
    # Initialize ChromaDB
    if not await initialize_chromadb():
        success = False
    
    if success:
        logger.info("✅ Database initialization completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Run 'python scripts/test-config.py' to verify configuration")
        logger.info("2. Start implementing Task 3: Build FastAPI backend foundation")
    else:
        logger.error("❌ Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())