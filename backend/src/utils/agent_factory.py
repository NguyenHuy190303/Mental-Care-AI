"""
Factory for creating and configuring the Linear Mental Health Agent.
"""

import os
import logging
from typing import Optional

from ..agents import LinearMentalHealthAgent, ChainOfThoughtEngine, SafetyComplianceLayer, ModelType
from ..tools import (
    RAGSearchTool, ChromaDBManager, create_cache_manager, create_rag_search_tool,
    InputAnalysisTool, ContextManagementSystem, MedicalImageSearchTool
)

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating configured Mental Health Agent instances."""
    
    @staticmethod
    async def create_linear_mental_health_agent(
        confidence_threshold: float = 0.7,
        enable_caching: bool = True,
        enable_detailed_logging: bool = True,
        chromadb_host: Optional[str] = None,
        chromadb_port: Optional[int] = None
    ) -> LinearMentalHealthAgent:
        """
        Create a fully configured Linear Mental Health Agent.
        
        Args:
            confidence_threshold: Minimum confidence threshold for RAG results
            enable_caching: Whether to enable response caching
            enable_detailed_logging: Whether to enable detailed step logging
            chromadb_host: ChromaDB host (uses environment variable if None)
            chromadb_port: ChromaDB port (uses environment variable if None)
            
        Returns:
            Configured LinearMentalHealthAgent instance
        """
        logger.info("Creating Linear Mental Health Agent...")
        
        try:
            # Initialize ChromaDB manager
            chromadb_manager = ChromaDBManager(
                host=chromadb_host,
                port=chromadb_port
            )
            logger.info("ChromaDB manager initialized")
            
            # Initialize cache manager
            cache_manager = None
            if enable_caching:
                cache_manager = create_cache_manager()
                logger.info(f"Cache manager initialized: {type(cache_manager).__name__}")
            
            # Initialize RAG search tool
            rag_search_tool = create_rag_search_tool(
                chromadb_manager=chromadb_manager,
                cache_manager=cache_manager,
                confidence_threshold=confidence_threshold,
                enable_caching=enable_caching
            )
            logger.info("RAG search tool initialized")
            
            # Initialize Chain-of-Thought engine with healthcare default model
            healthcare_model = os.getenv("DEFAULT_HEALTHCARE_MODEL", "gpt-4o-mini")
            chain_of_thought_engine = ChainOfThoughtEngine(
                api_key=os.getenv("OPENAI_API_KEY"),
                default_model=ModelType.HEALTHCARE_DEFAULT,
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
                max_tokens=2000
            )
            logger.info("Chain-of-Thought engine initialized")
            
            # Initialize Safety Compliance Layer
            safety_compliance_layer = SafetyComplianceLayer()
            logger.info("Safety Compliance Layer initialized")

            # Initialize Input Analysis Tool
            input_analysis_tool = InputAnalysisTool(
                enable_vision=True,
                enable_speech=True
            )
            logger.info("Input Analysis Tool initialized")

            # Initialize Context Management System
            context_management_system = ContextManagementSystem(
                chromadb_manager=chromadb_manager
            )
            logger.info("Context Management System initialized")

            # Initialize Medical Image Search Tool
            medical_image_search_tool = MedicalImageSearchTool(
                enable_caching=enable_caching,
                cache_ttl=3600,
                max_results_per_source=5
            )
            logger.info("Medical Image Search Tool initialized")

            # Create the Linear Mental Health Agent
            agent = LinearMentalHealthAgent(
                rag_search_tool=rag_search_tool,
                chain_of_thought_engine=chain_of_thought_engine,
                safety_compliance_layer=safety_compliance_layer,
                input_analysis_tool=input_analysis_tool,
                context_management_system=context_management_system,
                medical_image_search_tool=medical_image_search_tool,
                enable_detailed_logging=enable_detailed_logging
            )
            
            logger.info("Linear Mental Health Agent created successfully")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create Linear Mental Health Agent: {e}")
            raise
    
    @staticmethod
    async def validate_agent_dependencies() -> dict:
        """
        Validate that all agent dependencies are available.
        
        Returns:
            Dictionary with validation results for each dependency
        """
        validation_results = {}
        
        # Check OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        validation_results["openai_api_key"] = {
            "available": bool(openai_key),
            "details": "OpenAI API key found" if openai_key else "OpenAI API key missing"
        }
        
        # Check ChromaDB connection
        try:
            chromadb_manager = ChromaDBManager()
            stats = await chromadb_manager.get_collection_stats()
            validation_results["chromadb"] = {
                "available": True,
                "details": f"ChromaDB connected, collections: {list(stats.keys())}"
            }
        except Exception as e:
            validation_results["chromadb"] = {
                "available": False,
                "details": f"ChromaDB connection failed: {e}"
            }
        
        # Check cache system
        try:
            cache_manager = create_cache_manager()
            await cache_manager.set("test_key", "test_value", 1)
            test_value = await cache_manager.get("test_key")
            await cache_manager.delete("test_key")
            
            validation_results["cache_system"] = {
                "available": test_value == "test_value",
                "details": f"Cache system working: {type(cache_manager).__name__}"
            }
        except Exception as e:
            validation_results["cache_system"] = {
                "available": False,
                "details": f"Cache system failed: {e}"
            }
        
        # Check database connection
        try:
            from ..database import check_database_health
            db_healthy = await check_database_health()
            validation_results["database"] = {
                "available": db_healthy,
                "details": "Database connection healthy" if db_healthy else "Database connection failed"
            }
        except Exception as e:
            validation_results["database"] = {
                "available": False,
                "details": f"Database check failed: {e}"
            }
        
        return validation_results
    
    @staticmethod
    def get_agent_configuration() -> dict:
        """
        Get current agent configuration from environment variables.
        
        Returns:
            Dictionary with current configuration
        """
        return {
            "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
            "chromadb_host": os.getenv("CHROMADB_HOST", "localhost"),
            "chromadb_port": int(os.getenv("CHROMADB_PORT", "8000")),
            "redis_url": os.getenv("REDIS_URL"),
            "database_url": os.getenv("DATABASE_URL"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }


# Global agent instance
_global_agent: Optional[LinearMentalHealthAgent] = None


async def get_global_agent() -> LinearMentalHealthAgent:
    """
    Get or create the global agent instance.
    
    Returns:
        Global LinearMentalHealthAgent instance
    """
    global _global_agent
    
    if _global_agent is None:
        _global_agent = await AgentFactory.create_linear_mental_health_agent()
    
    return _global_agent


async def initialize_global_agent() -> LinearMentalHealthAgent:
    """
    Initialize the global agent instance.
    
    Returns:
        Initialized global agent
    """
    global _global_agent
    
    logger.info("Initializing global Mental Health Agent...")
    
    # Validate dependencies first
    validation_results = await AgentFactory.validate_agent_dependencies()
    
    # Log validation results
    for component, result in validation_results.items():
        if result["available"]:
            logger.info(f"✓ {component}: {result['details']}")
        else:
            logger.warning(f"✗ {component}: {result['details']}")
    
    # Check if critical dependencies are available
    critical_deps = ["openai_api_key"]
    missing_critical = [
        dep for dep in critical_deps 
        if not validation_results.get(dep, {}).get("available", False)
    ]
    
    if missing_critical:
        raise RuntimeError(f"Critical dependencies missing: {missing_critical}")
    
    # Create agent
    _global_agent = await AgentFactory.create_linear_mental_health_agent(
        confidence_threshold=0.7,
        enable_caching=True,
        enable_detailed_logging=True
    )
    
    logger.info("Global Mental Health Agent initialized successfully")
    return _global_agent


def reset_global_agent():
    """Reset the global agent instance (useful for testing)."""
    global _global_agent
    _global_agent = None
    logger.info("Global agent instance reset")


async def get_agent_health_status() -> dict:
    """
    Get comprehensive health status of the agent system.
    
    Returns:
        Health status dictionary
    """
    try:
        agent = await get_global_agent()
        agent_status = await agent.get_agent_status()
        
        validation_results = await AgentFactory.validate_agent_dependencies()
        configuration = AgentFactory.get_agent_configuration()
        
        # Calculate overall health
        all_deps_healthy = all(
            result.get("available", False) 
            for result in validation_results.values()
        )
        
        return {
            "overall_status": "healthy" if all_deps_healthy else "degraded",
            "agent_status": agent_status,
            "dependencies": validation_results,
            "configuration": configuration,
            "timestamp": logger.info("Health status check completed")
        }
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": logger.info("Health status check failed")
        }
