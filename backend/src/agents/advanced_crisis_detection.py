"""
Advanced Crisis Detection System for Mental Health Agent
Implements ML-based crisis detection to prevent evasion and improve accuracy.
"""

import asyncio
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity

from ..monitoring.logging_config import get_logger

logger = get_logger("agents.advanced_crisis_detection")


class AdvancedCrisisDetector:
    """Advanced ML-based crisis detection system."""
    
    def __init__(self):
        """Initialize advanced crisis detector."""
        self.crisis_classifier = None
        self.semantic_model = None
        self.tokenizer = None
        self.crisis_embeddings = None
        
        # Enhanced crisis patterns
        self.crisis_patterns = {
            'direct_threats': [
                r'\b(?:kill|hurt|harm|cut|end)\s+(?:myself|me)\b',
                r'\b(?:suicide|suicidal)\b',
                r'\bwant\s+to\s+die\b',
                r'\bend\s+(?:it\s+all|my\s+life)\b'
            ],
            'indirect_indicators': [
                r'\b(?:hopeless|worthless|burden)\b',
                r'\bno\s+(?:point|reason)\s+(?:living|going\s+on)\b',
                r'\beveryone\s+(?:better\s+off|happier)\s+without\s+me\b',
                r'\bcan\'?t\s+(?:take|handle)\s+(?:it|this)\s+anymore\b'
            ],
            'method_references': [
                r'\b(?:pills|overdose|bridge|jump|rope|gun|knife)\b',
                r'\b(?:hanging|drowning|poison)\b'
            ],
            'temporal_urgency': [
                r'\b(?:tonight|today|now|soon)\b.*(?:end|die|kill)',
                r'\bthis\s+is\s+(?:it|goodbye)\b'
            ]
        }
        
        # Obfuscation patterns
        self.obfuscation_patterns = [
            (r'[0-9]', {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't'}),
            (r'[^\w\s]', ''),  # Remove special characters
            (r'\s+', ' '),     # Normalize whitespace
        ]
        
    async def initialize_models(self):
        """Initialize ML models for crisis detection."""
        try:
            # Load pre-trained mental health classification model
            self.crisis_classifier = pipeline(
                "text-classification",
                model="mental-health/mental-bert-base-uncased",
                return_all_scores=True
            )
            
            # Load semantic similarity model
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            self.semantic_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            
            # Pre-compute crisis phrase embeddings
            await self._precompute_crisis_embeddings()
            
            logger.info("Advanced crisis detection models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize crisis detection models: {e}")
            # Fallback to rule-based detection
            self.crisis_classifier = None
    
    async def detect_crisis(self, text: str, context: Optional[Dict] = None) -> Tuple[bool, float, List[str]]:
        """
        Detect crisis indicators in text using multiple methods.
        
        Args:
            text: Input text to analyze
            context: Optional context information
            
        Returns:
            Tuple of (is_crisis, confidence_score, detected_indicators)
        """
        try:
            # Normalize and clean text
            normalized_text = self._normalize_text(text)
            
            # Multiple detection methods
            rule_based_result = await self._rule_based_detection(normalized_text)
            ml_based_result = await self._ml_based_detection(normalized_text)
            semantic_result = await self._semantic_similarity_detection(normalized_text)
            context_result = await self._context_aware_detection(normalized_text, context)
            
            # Combine results with weighted scoring
            combined_score = self._combine_detection_scores([
                (rule_based_result, 0.3),
                (ml_based_result, 0.4),
                (semantic_result, 0.2),
                (context_result, 0.1)
            ])
            
            is_crisis = combined_score['confidence'] >= 0.7
            
            # Log crisis detection for monitoring
            if is_crisis:
                await self._log_crisis_detection(text, combined_score)
            
            return (
                is_crisis,
                combined_score['confidence'],
                combined_score['indicators']
            )
            
        except Exception as e:
            logger.error(f"Crisis detection failed: {e}")
            # Fallback to basic keyword detection
            return await self._fallback_detection(text)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text to handle obfuscation attempts."""
        normalized = text.lower()
        
        # Handle common obfuscation patterns
        for pattern, replacements in self.obfuscation_patterns:
            if isinstance(replacements, dict):
                for char, replacement in replacements.items():
                    normalized = normalized.replace(char, replacement)
            else:
                normalized = re.sub(pattern, replacements, normalized)
        
        # Handle leetspeak and character substitution
        leetspeak_map = {
            '@': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '7': 't',
            '4': 'a', '8': 'b', '6': 'g', '9': 'g'
        }
        
        for leet, normal in leetspeak_map.items():
            normalized = normalized.replace(leet, normal)
        
        return normalized
    
    async def _rule_based_detection(self, text: str) -> Dict:
        """Rule-based crisis detection with pattern matching."""
        indicators = []
        confidence = 0.0
        
        for category, patterns in self.crisis_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    indicators.append(f"{category}: {pattern}")
                    
                    # Weight different categories
                    if category == 'direct_threats':
                        confidence += 0.4
                    elif category == 'method_references':
                        confidence += 0.3
                    elif category == 'temporal_urgency':
                        confidence += 0.3
                    else:
                        confidence += 0.2
        
        return {
            'method': 'rule_based',
            'confidence': min(confidence, 1.0),
            'indicators': indicators
        }
    
    async def _ml_based_detection(self, text: str) -> Dict:
        """ML-based crisis detection using pre-trained models."""
        if not self.crisis_classifier:
            return {'method': 'ml_based', 'confidence': 0.0, 'indicators': []}
        
        try:
            # Get classification results
            results = self.crisis_classifier(text)
            
            # Find crisis-related classifications
            crisis_score = 0.0
            indicators = []
            
            for result in results:
                if any(label in result['label'].lower() for label in ['crisis', 'suicide', 'self-harm']):
                    crisis_score = max(crisis_score, result['score'])
                    indicators.append(f"ML classification: {result['label']} ({result['score']:.3f})")
            
            return {
                'method': 'ml_based',
                'confidence': crisis_score,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"ML-based detection failed: {e}")
            return {'method': 'ml_based', 'confidence': 0.0, 'indicators': []}
    
    async def _semantic_similarity_detection(self, text: str) -> Dict:
        """Semantic similarity-based crisis detection."""
        if not self.semantic_model or self.crisis_embeddings is None:
            return {'method': 'semantic', 'confidence': 0.0, 'indicators': []}
        
        try:
            # Get text embedding
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = self.semantic_model(**inputs)
                text_embedding = outputs.last_hidden_state.mean(dim=1).numpy()
            
            # Calculate similarity with crisis embeddings
            similarities = cosine_similarity(text_embedding, self.crisis_embeddings)[0]
            max_similarity = np.max(similarities)
            
            indicators = []
            if max_similarity > 0.7:
                indicators.append(f"High semantic similarity to crisis phrases: {max_similarity:.3f}")
            
            return {
                'method': 'semantic',
                'confidence': max_similarity,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Semantic detection failed: {e}")
            return {'method': 'semantic', 'confidence': 0.0, 'indicators': []}
    
    async def _context_aware_detection(self, text: str, context: Optional[Dict]) -> Dict:
        """Context-aware crisis detection considering conversation history."""
        if not context:
            return {'method': 'context', 'confidence': 0.0, 'indicators': []}
        
        indicators = []
        confidence = 0.0
        
        # Check conversation history for escalating patterns
        if 'conversation_history' in context:
            history = context['conversation_history']
            
            # Look for escalating negative sentiment
            negative_count = sum(1 for msg in history[-5:] if self._is_negative_sentiment(msg))
            if negative_count >= 3:
                confidence += 0.3
                indicators.append("Escalating negative sentiment in conversation")
        
        # Check user profile for risk factors
        if 'user_profile' in context:
            profile = context['user_profile']
            
            if profile.get('previous_crisis_episodes', 0) > 0:
                confidence += 0.2
                indicators.append("User has previous crisis episodes")
            
            if profile.get('high_risk_period'):
                confidence += 0.3
                indicators.append("User in identified high-risk period")
        
        return {
            'method': 'context',
            'confidence': min(confidence, 1.0),
            'indicators': indicators
        }
    
    def _combine_detection_scores(self, results: List[Tuple[Dict, float]]) -> Dict:
        """Combine multiple detection method results with weights."""
        total_confidence = 0.0
        total_weight = 0.0
        all_indicators = []
        
        for result, weight in results:
            total_confidence += result['confidence'] * weight
            total_weight += weight
            all_indicators.extend(result['indicators'])
        
        final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
        
        return {
            'confidence': final_confidence,
            'indicators': all_indicators
        }
    
    async def _precompute_crisis_embeddings(self):
        """Pre-compute embeddings for known crisis phrases."""
        crisis_phrases = [
            "I want to kill myself",
            "I want to die",
            "I can't take it anymore",
            "I'm going to end it all",
            "Nobody would miss me",
            "I'm thinking about suicide",
            "I want to hurt myself",
            "Life isn't worth living"
        ]
        
        try:
            embeddings = []
            for phrase in crisis_phrases:
                inputs = self.tokenizer(phrase, return_tensors="pt", truncation=True, padding=True)
                with torch.no_grad():
                    outputs = self.semantic_model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).numpy()
                    embeddings.append(embedding[0])
            
            self.crisis_embeddings = np.array(embeddings)
            
        except Exception as e:
            logger.error(f"Failed to precompute crisis embeddings: {e}")
            self.crisis_embeddings = None
    
    def _is_negative_sentiment(self, text: str) -> bool:
        """Simple negative sentiment detection."""
        negative_words = ['sad', 'depressed', 'hopeless', 'worthless', 'terrible', 'awful', 'hate']
        return any(word in text.lower() for word in negative_words)
    
    async def _log_crisis_detection(self, text: str, result: Dict):
        """Log crisis detection for monitoring and improvement."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': result['confidence'],
            'indicators': result['indicators'],
            'text_length': len(text),
            'detection_method': 'advanced_ml'
        }
        
        # Log without exposing sensitive content
        logger.warning("Crisis detected", **log_data)
    
    async def _fallback_detection(self, text: str) -> Tuple[bool, float, List[str]]:
        """Fallback detection when ML models fail."""
        basic_keywords = ['suicide', 'kill myself', 'end my life', 'want to die']
        text_lower = text.lower()
        
        found_keywords = [kw for kw in basic_keywords if kw in text_lower]
        
        if found_keywords:
            return True, 0.8, [f"Keyword detected: {kw}" for kw in found_keywords]
        else:
            return False, 0.0, []


# Global instance
advanced_crisis_detector = AdvancedCrisisDetector()
