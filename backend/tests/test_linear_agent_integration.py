"""
Integration tests for the Linear Mental Health Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from backend.src.models.core import UserInput, InputType, AgentResponse
from backend.src.agents import LinearMentalHealthAgent, ChainOfThoughtEngine, SafetyComplianceLayer
from backend.src.tools import (
    RAGSearchTool, ChromaDBManager, InputAnalysisTool, 
    ContextManagementSystem, MedicalImageSearchTool
)
from backend.src.utils import AgentFactory


class TestLinearMentalHealthAgent:
    """Test suite for Linear Mental Health Agent integration."""
    
    @pytest.fixture
    async def mock_components(self):
        """Create mock components for testing."""
        # Mock ChromaDB Manager
        chromadb_manager = Mock(spec=ChromaDBManager)
        chromadb_manager.search_similar = AsyncMock(return_value={
            "documents": ["Test medical document"],
            "metadatas": [{"source": "test", "title": "Test Document"}],
            "distances": [0.3]
        })
        
        # Mock RAG Search Tool
        rag_search_tool = Mock(spec=RAGSearchTool)
        rag_search_tool.search = AsyncMock(return_value=Mock(
            documents=[],
            citations=[],
            confidence_scores=[],
            search_metadata={}
        ))
        
        # Mock Chain of Thought Engine
        chain_of_thought_engine = Mock(spec=ChainOfThoughtEngine)
        chain_of_thought_engine.generate_response = AsyncMock(return_value=(
            Mock(
                content="This is a test response from the mental health agent.",
                citations=[],
                medical_images=[],
                reasoning_steps=["Step 1: Analyzed input", "Step 2: Generated response"],
                confidence_level=0.8,
                safety_warnings=[],
                medical_disclaimer="This is not medical advice.",
                response_metadata={"model_used": "gpt-4"}
            ),
            []  # reasoning steps
        ))
        
        # Mock Safety Compliance Layer
        safety_compliance_layer = Mock(spec=SafetyComplianceLayer)
        safety_compliance_layer.assess_input_safety = AsyncMock(return_value=(
            "safe", []
        ))
        safety_compliance_layer.validate_response_safety = AsyncMock(return_value=[])
        safety_compliance_layer.enhance_response_safety = AsyncMock(side_effect=lambda x, y: x)
        safety_compliance_layer.get_compliance_summary = Mock(return_value={
            "overall_safe": True,
            "compliance_rate": 1.0,
            "failed_checks": []
        })
        
        # Mock Input Analysis Tool
        input_analysis_tool = Mock(spec=InputAnalysisTool)
        input_analysis_tool.analyze_input = AsyncMock(return_value=Mock(
            text="I'm feeling anxious about my upcoming presentation",
            intent="emotional_support",
            medical_entities=["anxiety"],
            urgency_level=5,
            confidence=0.8,
            emotional_context="anxiety"
        ))
        
        # Mock Context Management System
        context_management_system = Mock(spec=ContextManagementSystem)
        context_management_system.get_user_context = AsyncMock(return_value=Mock(
            user_id="test_user",
            session_id="test_session",
            compressed_history="Previous conversation about anxiety",
            user_profile={},
            session_context={},
            last_updated=datetime.utcnow()
        ))
        context_management_system.update_context = AsyncMock(side_effect=lambda x, *args: x)
        
        # Mock Medical Image Search Tool
        medical_image_search_tool = Mock(spec=MedicalImageSearchTool)
        medical_image_search_tool.search_medical_images = AsyncMock(return_value=[])
        
        return {
            "chromadb_manager": chromadb_manager,
            "rag_search_tool": rag_search_tool,
            "chain_of_thought_engine": chain_of_thought_engine,
            "safety_compliance_layer": safety_compliance_layer,
            "input_analysis_tool": input_analysis_tool,
            "context_management_system": context_management_system,
            "medical_image_search_tool": medical_image_search_tool
        }
    
    @pytest.fixture
    def linear_agent(self, mock_components):
        """Create Linear Mental Health Agent with mock components."""
        return LinearMentalHealthAgent(
            rag_search_tool=mock_components["rag_search_tool"],
            chain_of_thought_engine=mock_components["chain_of_thought_engine"],
            safety_compliance_layer=mock_components["safety_compliance_layer"],
            input_analysis_tool=mock_components["input_analysis_tool"],
            context_management_system=mock_components["context_management_system"],
            medical_image_search_tool=mock_components["medical_image_search_tool"],
            enable_detailed_logging=True
        )
    
    @pytest.mark.asyncio
    async def test_linear_agent_pipeline(self, linear_agent, mock_components):
        """Test the complete linear agent pipeline."""
        # Create test user input
        user_input = UserInput(
            user_id="test_user_123",
            session_id="test_session_456",
            type=InputType.TEXT,
            content="I'm feeling really anxious about my upcoming presentation at work. I can't sleep and my heart races when I think about it.",
            metadata={"source": "test"}
        )
        
        # Process the request
        response, processing_metadata = await linear_agent.process_request(user_input)
        
        # Verify response structure
        assert isinstance(response, AgentResponse)
        assert response.content
        assert response.medical_disclaimer
        assert isinstance(response.confidence_level, float)
        assert 0.0 <= response.confidence_level <= 1.0
        
        # Verify processing metadata
        assert "trace_id" in processing_metadata
        assert "total_duration" in processing_metadata
        assert "steps_completed" in processing_metadata
        assert "success_rate" in processing_metadata
        
        # Verify all pipeline steps were executed
        expected_steps = [
            "input_validation",
            "input_analysis",
            "context_retrieval", 
            "safety_assessment",
            "knowledge_retrieval",
            "image_search",
            "reasoning_generation",
            "safety_validation",
            "response_formatting",
            "context_update"
        ]
        
        completed_steps = [step["name"] for step in processing_metadata["step_details"]]
        for expected_step in expected_steps:
            assert expected_step in completed_steps
        
        # Verify tools were called in correct sequence
        mock_components["input_analysis_tool"].analyze_input.assert_called_once()
        mock_components["context_management_system"].get_user_context.assert_called_once()
        mock_components["safety_compliance_layer"].assess_input_safety.assert_called_once()
        mock_components["rag_search_tool"].search.assert_called_once()
        mock_components["medical_image_search_tool"].search_medical_images.assert_called()
        mock_components["chain_of_thought_engine"].generate_response.assert_called_once()
        mock_components["safety_compliance_layer"].validate_response_safety.assert_called_once()
        mock_components["context_management_system"].update_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_crisis_input_handling(self, linear_agent, mock_components):
        """Test handling of crisis-level input."""
        # Mock crisis detection
        mock_components["safety_compliance_layer"].assess_input_safety = AsyncMock(return_value=(
            "critical", ["Crisis keywords detected", "Self-harm indicators detected"]
        ))
        
        # Create crisis input
        user_input = UserInput(
            user_id="test_user_123",
            session_id="test_session_456",
            type=InputType.TEXT,
            content="I want to hurt myself and end everything",
            metadata={}
        )
        
        # Process the request
        response, processing_metadata = await linear_agent.process_request(user_input)
        
        # Verify crisis handling
        assert response.safety_warnings
        assert any("crisis" in warning.lower() for warning in response.safety_warnings)
        assert "emergency" in response.content.lower() or "crisis" in response.content.lower()
    
    @pytest.mark.asyncio
    async def test_multimodal_input_support(self, linear_agent, mock_components):
        """Test multimodal input processing."""
        # Test voice input
        voice_input = UserInput(
            user_id="test_user_123",
            session_id="test_session_456",
            type=InputType.VOICE,
            content=b"fake_audio_data",
            metadata={"audio_format": "wav"}
        )
        
        response, _ = await linear_agent.process_request(voice_input)
        assert isinstance(response, AgentResponse)
        
        # Verify input analysis tool was called for voice processing
        mock_components["input_analysis_tool"].analyze_input.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, linear_agent, mock_components):
        """Test error handling in the pipeline."""
        # Mock an error in the chain of thought engine
        mock_components["chain_of_thought_engine"].generate_response = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        user_input = UserInput(
            user_id="test_user_123",
            session_id="test_session_456",
            type=InputType.TEXT,
            content="Test input",
            metadata={}
        )
        
        response, processing_metadata = await linear_agent.process_request(user_input)
        
        # Verify error response
        assert "error" in response.content.lower() or "issue" in response.content.lower()
        assert response.confidence_level == 0.0
        assert processing_metadata["success_rate"] < 1.0
    
    @pytest.mark.asyncio
    async def test_agent_status(self, linear_agent):
        """Test agent status reporting."""
        status = await linear_agent.get_agent_status()
        
        assert status["agent_type"] == "LinearMentalHealthAgent"
        assert status["status"] == "healthy"
        assert "components" in status
        assert "pipeline_steps" in status
        assert status["detailed_logging"] is True


class TestAgentFactory:
    """Test suite for Agent Factory."""
    
    @pytest.mark.asyncio
    async def test_dependency_validation(self):
        """Test dependency validation."""
        validation_results = await AgentFactory.validate_agent_dependencies()
        
        assert "openai_api_key" in validation_results
        assert "chromadb" in validation_results
        assert "cache_system" in validation_results
        assert "database" in validation_results
        
        # Each validation should have 'available' and 'details' keys
        for component, result in validation_results.items():
            assert "available" in result
            assert "details" in result
            assert isinstance(result["available"], bool)
    
    def test_agent_configuration(self):
        """Test agent configuration retrieval."""
        config = AgentFactory.get_agent_configuration()
        
        expected_keys = [
            "openai_api_key_set",
            "chromadb_host",
            "chromadb_port",
            "environment",
            "debug"
        ]
        
        for key in expected_keys:
            assert key in config


class TestSingleThreadedLinearPattern:
    """Test suite to verify Single-Threaded Linear Agent pattern compliance."""
    
    @pytest.mark.asyncio
    async def test_sequential_processing(self, linear_agent, mock_components):
        """Test that processing is truly sequential, not parallel."""
        call_order = []
        
        # Mock functions to track call order
        original_analyze = mock_components["input_analysis_tool"].analyze_input
        original_search = mock_components["rag_search_tool"].search
        original_generate = mock_components["chain_of_thought_engine"].generate_response
        
        async def track_analyze(*args, **kwargs):
            call_order.append("analyze_input")
            return await original_analyze(*args, **kwargs)
        
        async def track_search(*args, **kwargs):
            call_order.append("rag_search")
            return await original_search(*args, **kwargs)
        
        async def track_generate(*args, **kwargs):
            call_order.append("generate_response")
            return await original_generate(*args, **kwargs)
        
        mock_components["input_analysis_tool"].analyze_input = track_analyze
        mock_components["rag_search_tool"].search = track_search
        mock_components["chain_of_thought_engine"].generate_response = track_generate
        
        # Process request
        user_input = UserInput(
            user_id="test_user",
            session_id="test_session",
            type=InputType.TEXT,
            content="Test sequential processing",
            metadata={}
        )
        
        await linear_agent.process_request(user_input)
        
        # Verify sequential order
        expected_order = ["analyze_input", "rag_search", "generate_response"]
        actual_order = [call for call in call_order if call in expected_order]
        
        assert actual_order == expected_order, f"Expected {expected_order}, got {actual_order}"
    
    @pytest.mark.asyncio
    async def test_context_integrity(self, linear_agent, mock_components):
        """Test that context is maintained throughout the pipeline."""
        context_states = []
        
        # Mock to capture context at each step
        original_search = mock_components["rag_search_tool"].search
        
        async def capture_context_search(*args, **kwargs):
            # The context should be passed to RAG search
            context_states.append("rag_search_has_context")
            return await original_search(*args, **kwargs)
        
        mock_components["rag_search_tool"].search = capture_context_search
        
        user_input = UserInput(
            user_id="test_user",
            session_id="test_session", 
            type=InputType.TEXT,
            content="Test context integrity",
            metadata={}
        )
        
        response, _ = await linear_agent.process_request(user_input)
        
        # Verify context was maintained
        assert "rag_search_has_context" in context_states
        assert response.response_metadata  # Should contain processing metadata
    
    def test_no_parallel_subagents(self, linear_agent):
        """Test that the agent doesn't use parallel sub-agents."""
        # Verify the agent only has tool dependencies, not sub-agent dependencies
        agent_attributes = dir(linear_agent)
        
        # Should have tools
        assert hasattr(linear_agent, 'rag_search_tool')
        assert hasattr(linear_agent, 'chain_of_thought_engine')
        assert hasattr(linear_agent, 'safety_compliance_layer')
        
        # Should not have sub-agents or parallel processing attributes
        parallel_indicators = [
            'sub_agents', 'parallel_agents', 'agent_pool', 
            'concurrent_agents', 'worker_agents'
        ]
        
        for indicator in parallel_indicators:
            assert not hasattr(linear_agent, indicator), f"Found parallel processing indicator: {indicator}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
