"""
Tests for data models and database schemas.
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any

from src.models.core import (
    UserInput, AnalyzedInput, RAGResults, Citation, 
    AgentResponse, MedicalImage, UserContext, ProcessingContext
)
from src.models.validation import DataValidator, ValidationUtils
from src.database.encryption import EncryptionManager


class TestCoreModels:
    """Test core Pydantic models."""
    
    def test_user_input_validation(self):
        """Test UserInput model validation."""
        valid_data = {
            "user_id": "user_123",
            "session_id": "session_456",
            "type": "text",
            "content": "I feel anxious",
            "timestamp": datetime.utcnow(),
            "metadata": {"source": "web"}
        }
        
        user_input = UserInput(**valid_data)
        assert user_input.user_id == "user_123"
        assert user_input.type == "text"
        assert isinstance(user_input.timestamp, datetime)
    
    def test_user_input_validation_errors(self):
        """Test UserInput validation errors."""
        # Empty user_id should fail
        with pytest.raises(ValueError):
            UserInput(
                user_id="",
                session_id="session_456",
                type="text",
                content="test",
                timestamp=datetime.utcnow()
            )
        
        # Empty text content should fail
        with pytest.raises(ValueError):
            UserInput(
                user_id="user_123",
                session_id="session_456", 
                type="text",
                content="",
                timestamp=datetime.utcnow()
            )
    
    def test_analyzed_input_validation(self):
        """Test AnalyzedInput model validation."""
        valid_data = {
            "text": "I have been feeling anxious",
            "intent": "emotional_support",
            "medical_entities": ["anxiety"],
            "urgency_level": 5,
            "confidence": 0.85
        }
        
        analyzed_input = AnalyzedInput(**valid_data)
        assert analyzed_input.intent == "emotional_support"
        assert "anxiety" in analyzed_input.medical_entities
        assert 1 <= analyzed_input.urgency_level <= 10
        assert 0.0 <= analyzed_input.confidence <= 1.0
    
    def test_analyzed_input_validation_errors(self):
        """Test AnalyzedInput validation errors."""
        # Invalid intent should fail
        with pytest.raises(ValueError):
            AnalyzedInput(
                text="test",
                intent="invalid_intent",
                urgency_level=5,
                confidence=0.8
            )
        
        # Invalid urgency level should fail
        with pytest.raises(ValueError):
            AnalyzedInput(
                text="test",
                intent="medical_question",
                urgency_level=15,  # > 10
                confidence=0.8
            )
    
    def test_citation_validation(self):
        """Test Citation model validation."""
        valid_data = {
            "source": "pubmed",
            "title": "Test Article",
            "authors": ["Dr. Smith"],
            "publication_date": date(2023, 1, 1),
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345",
            "excerpt": "This is a test excerpt",
            "relevance_score": 0.9
        }
        
        citation = Citation(**valid_data)
        assert citation.source == "pubmed"
        assert citation.url.startswith("https://")
        assert 0.0 <= citation.relevance_score <= 1.0
    
    def test_citation_validation_errors(self):
        """Test Citation validation errors."""
        # Invalid URL should fail
        with pytest.raises(ValueError):
            Citation(
                source="pubmed",
                title="Test",
                url="invalid-url",
                excerpt="test",
                relevance_score=0.9
            )
        
        # Invalid source should fail
        with pytest.raises(ValueError):
            Citation(
                source="invalid_source",
                title="Test",
                url="https://example.com",
                excerpt="test",
                relevance_score=0.9
            )
    
    def test_agent_response_validation(self):
        """Test AgentResponse model validation."""
        valid_data = {
            "content": "Based on your symptoms, you may be experiencing anxiety.",
            "citations": [],
            "medical_images": [],
            "reasoning_steps": ["Analyzed symptoms", "Consulted knowledge base"],
            "confidence_level": 0.8,
            "safety_warnings": ["Consult a healthcare professional"],
            "medical_disclaimer": "This is not medical advice."
        }
        
        response = AgentResponse(**valid_data)
        assert response.content.strip() != ""
        assert response.medical_disclaimer.strip() != ""
        assert 0.0 <= response.confidence_level <= 1.0
    
    def test_agent_response_validation_errors(self):
        """Test AgentResponse validation errors."""
        # Empty content should fail
        with pytest.raises(ValueError):
            AgentResponse(
                content="",
                confidence_level=0.8,
                medical_disclaimer="This is not medical advice."
            )
        
        # Empty disclaimer should fail
        with pytest.raises(ValueError):
            AgentResponse(
                content="Test response",
                confidence_level=0.8,
                medical_disclaimer=""
            )


class TestDataValidator:
    """Test data validation utilities."""
    
    def test_validate_user_input(self):
        """Test user input validation."""
        data = {
            "user_id": "user_123",
            "session_id": "session_456",
            "type": "text",
            "content": "test message",
            "timestamp": datetime.utcnow()
        }
        
        validator = DataValidator()
        user_input = validator.validate_user_input(data)
        assert isinstance(user_input, UserInput)
        assert user_input.user_id == "user_123"
    
    def test_validate_citation(self):
        """Test citation validation."""
        data = {
            "source": "pubmed",
            "title": "Test Article",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345",
            "excerpt": "Test excerpt",
            "relevance_score": 0.85
        }
        
        validator = DataValidator()
        citation = validator.validate_citation(data)
        assert isinstance(citation, Citation)
        assert citation.source == "pubmed"


class TestValidationUtils:
    """Test validation utility functions."""
    
    def test_is_valid_email(self):
        """Test email validation."""
        utils = ValidationUtils()
        
        assert utils.is_valid_email("test@example.com")
        assert utils.is_valid_email("user.name@domain.co.uk")
        assert not utils.is_valid_email("invalid-email")
        assert not utils.is_valid_email("@domain.com")
        assert not utils.is_valid_email("user@")
    
    def test_is_valid_url(self):
        """Test URL validation."""
        utils = ValidationUtils()
        
        assert utils.is_valid_url("https://example.com")
        assert utils.is_valid_url("http://test.org")
        assert not utils.is_valid_url("ftp://example.com")
        assert not utils.is_valid_url("invalid-url")
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        utils = ValidationUtils()
        
        # Test basic sanitization
        result = utils.sanitize_text("  Hello World  ")
        assert result == "Hello World"
        
        # Test length limiting
        result = utils.sanitize_text("Very long text", max_length=5)
        assert len(result) <= 5
        
        # Test control character removal
        result = utils.sanitize_text("Hello\x00World\x01")
        assert "\x00" not in result
        assert "\x01" not in result
    
    def test_validate_confidence_score(self):
        """Test confidence score validation."""
        utils = ValidationUtils()
        
        assert utils.validate_confidence_score(0.0)
        assert utils.validate_confidence_score(0.5)
        assert utils.validate_confidence_score(1.0)
        assert not utils.validate_confidence_score(-0.1)
        assert not utils.validate_confidence_score(1.1)
        assert not utils.validate_confidence_score("invalid")
    
    def test_validate_urgency_level(self):
        """Test urgency level validation."""
        utils = ValidationUtils()
        
        assert utils.validate_urgency_level(1)
        assert utils.validate_urgency_level(5)
        assert utils.validate_urgency_level(10)
        assert not utils.validate_urgency_level(0)
        assert not utils.validate_urgency_level(11)
        assert not utils.validate_urgency_level("invalid")
    
    def test_extract_medical_entities(self):
        """Test medical entity extraction."""
        utils = ValidationUtils()
        
        text = "I have a headache and feel anxious"
        entities = utils.extract_medical_entities(text)
        
        assert "headache" in entities
        assert "anxiety" in entities or "anxious" in entities
    
    def test_classify_intent(self):
        """Test intent classification."""
        utils = ValidationUtils()
        
        assert utils.classify_intent("I need help, this is an emergency") == "crisis"
        assert utils.classify_intent("I have a headache") == "symptom_description"
        assert utils.classify_intent("What medication should I take?") == "medication_query"
        assert utils.classify_intent("I feel sad and depressed") == "emotional_support"
        assert utils.classify_intent("What is diabetes?") == "medical_question"


class TestEncryption:
    """Test encryption functionality."""
    
    def test_encryption_decryption(self):
        """Test basic encryption and decryption."""
        manager = EncryptionManager()
        
        original_text = "This is sensitive medical data"
        encrypted = manager.encrypt(original_text)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original_text
        assert encrypted != original_text
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        manager = EncryptionManager()
        
        original_dict = {
            "user_id": "123",
            "medical_history": "Patient has anxiety",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        encrypted = manager.encrypt_dict(original_dict)
        decrypted = manager.decrypt_dict(encrypted)
        
        assert decrypted == original_dict
    
    def test_is_encrypted(self):
        """Test encryption detection."""
        manager = EncryptionManager()
        
        plaintext = "This is plaintext"
        encrypted = manager.encrypt(plaintext)
        
        assert not manager.is_encrypted(plaintext)
        assert manager.is_encrypted(encrypted)


if __name__ == "__main__":
    pytest.main([__file__])