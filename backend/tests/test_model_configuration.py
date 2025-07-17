"""
Test suite for default model configuration in healthcare mode.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from backend.src.agents.chain_of_thought_engine import ChainOfThoughtEngine, ModelType
from backend.src.utils.agent_factory import AgentFactory


class TestModelConfiguration:
    """Test suite for model configuration and selection."""
    
    def test_healthcare_default_model_type(self):
        """Test that HEALTHCARE_DEFAULT model type is correctly defined."""
        assert ModelType.HEALTHCARE_DEFAULT == "gpt-4o-mini"
        assert hasattr(ModelType, 'HEALTHCARE_DEFAULT')
    
    @patch.dict(os.environ, {'SAGE_HEALTHCARE_MODE': 'true'})
    def test_model_selection_healthcare_mode_simple(self):
        """Test model selection in healthcare mode for simple queries."""
        with patch('backend.src.agents.chain_of_thought_engine.openai'):
            engine = ChainOfThoughtEngine(api_key="test-key")
            selected_model = engine._select_model("simple")
            assert selected_model == ModelType.HEALTHCARE_DEFAULT
    
    @patch.dict(os.environ, {'SAGE_HEALTHCARE_MODE': 'true'})
    def test_model_selection_healthcare_mode_complex(self):
        """Test model selection in healthcare mode for complex queries."""
        with patch('backend.src.agents.chain_of_thought_engine.openai'):
            engine = ChainOfThoughtEngine(api_key="test-key")
            selected_model = engine._select_model("complex")
            assert selected_model == ModelType.HEALTHCARE_DEFAULT
    
    @patch.dict(os.environ, {'SAGE_HEALTHCARE_MODE': 'true'})
    def test_model_selection_healthcare_mode_critical(self):
        """Test model selection in healthcare mode for critical queries."""
        with patch('backend.src.agents.chain_of_thought_engine.openai'):
            engine = ChainOfThoughtEngine(api_key="test-key")
            selected_model = engine._select_model("critical")
            assert selected_model == ModelType.ADVANCED
    
    @patch.dict(os.environ, {'SAGE_HEALTHCARE_MODE': 'false'})
    def test_model_selection_non_healthcare_mode(self):
        """Test model selection in non-healthcare mode (legacy behavior)."""
        with patch('backend.src.agents.chain_of_thought_engine.openai'):
            engine = ChainOfThoughtEngine(api_key="test-key")
            
            # Test simple query
            selected_model = engine._select_model("simple")
            assert selected_model == ModelType.SIMPLE
            
            # Test complex query
            selected_model = engine._select_model("complex")
            assert selected_model == ModelType.COMPLEX
            
            # Test critical query
            selected_model = engine._select_model("critical")
            assert selected_model == ModelType.ADVANCED
    
    def test_default_model_initialization(self):
        """Test that ChainOfThoughtEngine initializes with healthcare default model."""
        with patch('backend.src.agents.chain_of_thought_engine.openai'):
            engine = ChainOfThoughtEngine(api_key="test-key")
            assert engine.default_model == ModelType.HEALTHCARE_DEFAULT
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key',
        'DEFAULT_HEALTHCARE_MODEL': 'gpt-4o-mini',
        'OPENAI_TEMPERATURE': '0.3'
    })
    @patch('backend.src.utils.agent_factory.ChainOfThoughtEngine')
    @patch('backend.src.utils.agent_factory.ChromaDBManager')
    @patch('backend.src.utils.agent_factory.create_cache_manager')
    @patch('backend.src.utils.agent_factory.create_rag_search_tool')
    @patch('backend.src.utils.agent_factory.SafetyComplianceLayer')
    @patch('backend.src.utils.agent_factory.InputAnalysisTool')
    @patch('backend.src.utils.agent_factory.ContextManagementSystem')
    @patch('backend.src.utils.agent_factory.MedicalImageSearchTool')
    @patch('backend.src.utils.agent_factory.LinearMentalHealthAgent')
    def test_agent_factory_uses_healthcare_model(
        self,
        mock_agent,
        mock_image_tool,
        mock_context_system,
        mock_input_tool,
        mock_safety_layer,
        mock_rag_tool,
        mock_cache_manager,
        mock_chromadb,
        mock_cot_engine
    ):
        """Test that AgentFactory initializes ChainOfThoughtEngine with healthcare model."""
        # Mock the return values
        mock_chromadb.return_value = MagicMock()
        mock_cache_manager.return_value = MagicMock()
        mock_rag_tool.return_value = MagicMock()
        mock_cot_engine.return_value = MagicMock()
        mock_safety_layer.return_value = MagicMock()
        mock_input_tool.return_value = MagicMock()
        mock_context_system.return_value = MagicMock()
        mock_image_tool.return_value = MagicMock()
        mock_agent.return_value = MagicMock()
        
        # Create agent through factory
        agent = AgentFactory.create_agent()
        
        # Verify ChainOfThoughtEngine was called with healthcare model
        mock_cot_engine.assert_called_once_with(
            api_key='test-key',
            default_model=ModelType.HEALTHCARE_DEFAULT,
            temperature=0.3,
            max_tokens=2000
        )
    
    def test_model_type_enum_completeness(self):
        """Test that all expected model types are available."""
        expected_models = {
            'SIMPLE': 'gpt-3.5-turbo',
            'COMPLEX': 'gpt-4',
            'ADVANCED': 'gpt-4-turbo',
            'HEALTHCARE_DEFAULT': 'gpt-4o-mini'
        }
        
        for model_name, model_value in expected_models.items():
            assert hasattr(ModelType, model_name)
            assert getattr(ModelType, model_name) == model_value
    
    @patch.dict(os.environ, {'SAGE_HEALTHCARE_MODE': 'true'})
    def test_healthcare_mode_environment_variable(self):
        """Test that healthcare mode is properly detected from environment variable."""
        with patch('backend.src.agents.chain_of_thought_engine.openai'):
            engine = ChainOfThoughtEngine(api_key="test-key")
            
            # Test that healthcare mode affects model selection
            selected_model = engine._select_model("simple")
            assert selected_model == ModelType.HEALTHCARE_DEFAULT
    
    def test_model_configuration_documentation(self):
        """Test that model configuration is properly documented."""
        # Verify that the healthcare default model is documented
        assert ModelType.HEALTHCARE_DEFAULT.__doc__ is None  # Enum values don't have docstrings
        
        # Verify that the model selection method has proper documentation
        engine_class = ChainOfThoughtEngine
        select_model_method = getattr(engine_class, '_select_model')
        assert select_model_method.__doc__ is not None
        assert "healthcare" in select_model_method.__doc__.lower()


if __name__ == "__main__":
    pytest.main([__file__])
