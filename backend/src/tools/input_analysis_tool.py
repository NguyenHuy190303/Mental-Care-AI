"""
Input Analysis Tool with multimodal support for text, voice, and image processing.
"""

import os
import logging
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

from ..models.core import UserInput, AnalyzedInput, InputType

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classifies user intent from text input."""
    
    INTENT_CATEGORIES = {
        "crisis": {
            "keywords": [
                "suicide", "kill myself", "end my life", "self-harm", "hurt myself",
                "overdose", "emergency", "crisis", "hopeless", "worthless", "die"
            ],
            "patterns": [
                r"want to die", r"end it all", r"can't go on", r"no point",
                r"better off dead", r"hurt myself", r"kill myself"
            ]
        },
        "emotional_support": {
            "keywords": [
                "sad", "depressed", "depression", "down", "lonely", "anxious",
                "worried", "scared", "overwhelmed", "stressed", "grief", "loss"
            ],
            "patterns": [
                r"feeling (sad|down|depressed)", r"can't cope", r"struggling with",
                r"hard time", r"difficult period", r"emotional pain"
            ]
        },
        "medical_question": {
            "keywords": [
                "doctor", "therapist", "treatment", "therapy", "counseling",
                "psychiatrist", "psychologist", "diagnosis", "symptoms"
            ],
            "patterns": [
                r"should i see", r"need help", r"professional help",
                r"medical advice", r"treatment options"
            ]
        },
        "medication_query": {
            "keywords": [
                "medication", "medicine", "pills", "prescription", "drug",
                "antidepressant", "anxiety medication", "side effects", "dosage"
            ],
            "patterns": [
                r"taking (medication|pills)", r"side effects", r"drug interactions",
                r"prescription", r"dosage"
            ]
        },
        "symptom_description": {
            "keywords": [
                "symptoms", "feeling", "experience", "having", "trouble",
                "difficulty", "problems", "issues", "concerns"
            ],
            "patterns": [
                r"i (feel|am feeling)", r"experiencing", r"having trouble",
                r"symptoms include", r"been feeling"
            ]
        }
    }
    
    def classify_intent(self, text: str) -> str:
        """
        Classify the intent of the input text.
        
        Args:
            text: Input text to classify
            
        Returns:
            Classified intent category
        """
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, config in self.INTENT_CATEGORIES.items():
            score = 0
            
            # Check keywords
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    score += 1
            
            # Check patterns
            import re
            for pattern in config.get("patterns", []):
                if re.search(pattern, text_lower):
                    score += 2  # Patterns have higher weight
            
            intent_scores[intent] = score
        
        # Return intent with highest score, default to general_inquiry
        if intent_scores and max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        
        return "general_inquiry"


class MedicalEntityExtractor:
    """Extracts medical entities from text."""
    
    MEDICAL_ENTITIES = {
        "mental_health_conditions": [
            "depression", "anxiety", "bipolar", "ptsd", "ocd", "adhd", "schizophrenia",
            "panic disorder", "social anxiety", "generalized anxiety", "major depression",
            "manic depression", "post-traumatic stress", "obsessive compulsive",
            "attention deficit", "eating disorder", "anorexia", "bulimia"
        ],
        "symptoms": [
            "insomnia", "fatigue", "mood swings", "panic attacks", "hallucinations",
            "delusions", "paranoia", "mania", "hypomania", "dissociation",
            "flashbacks", "nightmares", "compulsions", "obsessions"
        ],
        "treatments": [
            "therapy", "counseling", "psychotherapy", "cbt", "dbt", "emdr",
            "cognitive behavioral therapy", "dialectical behavior therapy",
            "exposure therapy", "group therapy", "family therapy"
        ],
        "medications": [
            "antidepressant", "ssri", "snri", "benzodiazepine", "antipsychotic",
            "mood stabilizer", "lithium", "prozac", "zoloft", "xanax", "ativan"
        ]
    }
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract medical entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted medical entities
        """
        text_lower = text.lower()
        extracted_entities = []
        
        for category, entities in self.MEDICAL_ENTITIES.items():
            for entity in entities:
                if entity in text_lower:
                    extracted_entities.append(entity)
        
        return list(set(extracted_entities))  # Remove duplicates


class UrgencyAssessor:
    """Assesses urgency level of user input."""
    
    URGENCY_INDICATORS = {
        10: ["suicide", "kill myself", "end my life", "overdose", "emergency"],
        9: ["crisis", "urgent", "immediate", "can't wait", "right now"],
        8: ["very worried", "extremely", "severe", "intense", "unbearable"],
        7: ["worried", "concerned", "anxious", "scared", "frightened"],
        6: ["uncomfortable", "bothered", "troubled", "distressed"],
        5: ["somewhat", "a bit", "slightly", "mild", "moderate"],
        3: ["curious", "wondering", "interested", "general question"]
    }
    
    def assess_urgency(self, text: str, intent: str) -> int:
        """
        Assess urgency level of the input.
        
        Args:
            text: Input text
            intent: Classified intent
            
        Returns:
            Urgency level (1-10)
        """
        text_lower = text.lower()
        
        # Crisis intent automatically gets high urgency
        if intent == "crisis":
            return 10
        
        # Check for urgency indicators
        for urgency_level, indicators in self.URGENCY_INDICATORS.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return urgency_level
        
        # Default urgency based on intent
        intent_urgency = {
            "crisis": 10,
            "medical_question": 6,
            "symptom_description": 5,
            "emotional_support": 4,
            "medication_query": 5,
            "general_inquiry": 3
        }
        
        return intent_urgency.get(intent, 3)


class EmotionalContextDetector:
    """Detects emotional context from text."""
    
    EMOTIONAL_INDICATORS = {
        "sadness": ["sad", "depressed", "down", "blue", "melancholy", "grief", "sorrow"],
        "anxiety": ["anxious", "worried", "nervous", "panic", "fear", "scared", "tense"],
        "anger": ["angry", "mad", "furious", "irritated", "frustrated", "rage"],
        "fear": ["afraid", "terrified", "scared", "frightened", "fearful", "phobic"],
        "hopelessness": ["hopeless", "helpless", "worthless", "pointless", "meaningless"],
        "confusion": ["confused", "lost", "uncertain", "unclear", "bewildered"],
        "stress": ["stressed", "overwhelmed", "pressure", "burden", "exhausted"]
    }
    
    def detect_emotion(self, text: str) -> Optional[str]:
        """
        Detect primary emotional context.
        
        Args:
            text: Input text
            
        Returns:
            Primary emotional context or None
        """
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, indicators in self.EMOTIONAL_INDICATORS.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        
        return None


class SpeechToTextProcessor:
    """Processes voice input to text."""
    
    def __init__(self):
        """Initialize speech-to-text processor."""
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.warning("Speech recognition not available")
        
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
    
    async def process_audio(self, audio_data: bytes) -> str:
        """
        Convert audio data to text.
        
        Args:
            audio_data: Audio data in bytes
            
        Returns:
            Transcribed text
        """
        if not self.recognizer:
            raise ValueError("Speech recognition not available")
        
        try:
            # Convert bytes to AudioData (simplified - would need proper audio handling)
            # This is a placeholder implementation
            audio_file = sr.AudioFile(audio_data)
            with audio_file as source:
                audio = self.recognizer.record(source)
            
            # Use Google Speech Recognition (free tier)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Speech-to-text conversion successful: {len(text)} characters")
            return text
            
        except sr.UnknownValueError:
            raise ValueError("Could not understand audio")
        except sr.RequestError as e:
            raise ValueError(f"Speech recognition service error: {e}")


class VisionAnalyzer:
    """Analyzes images for mental health context."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize vision analyzer."""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required for vision analysis")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required for vision analysis")
        
        openai.api_key = self.api_key
    
    async def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze image for mental health context.
        
        Args:
            image_data: Image data in bytes
            
        Returns:
            Analysis results
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Use GPT-4 Vision for analysis
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image for mental health context. Look for signs of distress, self-harm, or concerning content. Provide a brief, professional assessment."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            analysis = response.choices[0].message.content
            
            # Extract key information
            return {
                "description": analysis,
                "safety_concerns": self._extract_safety_concerns(analysis),
                "emotional_indicators": self._extract_emotional_indicators(analysis),
                "confidence": 0.8  # Placeholder confidence
            }
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return {
                "description": "Image analysis unavailable",
                "safety_concerns": [],
                "emotional_indicators": [],
                "confidence": 0.0
            }
    
    def _extract_safety_concerns(self, analysis: str) -> List[str]:
        """Extract safety concerns from analysis."""
        concerns = []
        concern_keywords = ["self-harm", "distress", "concerning", "warning", "danger"]
        
        analysis_lower = analysis.lower()
        for keyword in concern_keywords:
            if keyword in analysis_lower:
                concerns.append(f"Potential {keyword} detected in image")
        
        return concerns
    
    def _extract_emotional_indicators(self, analysis: str) -> List[str]:
        """Extract emotional indicators from analysis."""
        indicators = []
        emotion_keywords = ["sad", "happy", "angry", "fearful", "distressed", "calm"]
        
        analysis_lower = analysis.lower()
        for keyword in emotion_keywords:
            if keyword in analysis_lower:
                indicators.append(keyword)
        
        return indicators


class InputAnalysisTool:
    """Main input analysis tool with multimodal support."""
    
    def __init__(self, enable_vision: bool = True, enable_speech: bool = True):
        """
        Initialize input analysis tool.
        
        Args:
            enable_vision: Whether to enable vision analysis
            enable_speech: Whether to enable speech-to-text
        """
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = MedicalEntityExtractor()
        self.urgency_assessor = UrgencyAssessor()
        self.emotion_detector = EmotionalContextDetector()
        
        # Initialize optional components
        self.speech_processor = None
        self.vision_analyzer = None
        
        if enable_speech and SPEECH_RECOGNITION_AVAILABLE:
            self.speech_processor = SpeechToTextProcessor()
        
        if enable_vision and OPENAI_AVAILABLE:
            try:
                self.vision_analyzer = VisionAnalyzer()
            except Exception as e:
                logger.warning(f"Vision analyzer initialization failed: {e}")
        
        logger.info("Input Analysis Tool initialized")
    
    async def analyze_input(self, user_input: UserInput) -> AnalyzedInput:
        """
        Analyze user input with multimodal support.
        
        Args:
            user_input: User input to analyze
            
        Returns:
            Analyzed input with extracted information
        """
        try:
            # Process different input types
            if user_input.type == InputType.TEXT:
                text = str(user_input.content)
            elif user_input.type == InputType.VOICE:
                if not self.speech_processor:
                    raise ValueError("Speech processing not available")
                text = await self.speech_processor.process_audio(user_input.content)
            elif user_input.type == InputType.IMAGE:
                if not self.vision_analyzer:
                    raise ValueError("Vision analysis not available")
                
                # Analyze image
                image_analysis = await self.vision_analyzer.analyze_image(user_input.content)
                text = image_analysis["description"]
                
                # Add image analysis to metadata
                user_input.metadata["image_analysis"] = image_analysis
            else:
                raise ValueError(f"Unsupported input type: {user_input.type}")
            
            # Perform text analysis
            intent = self.intent_classifier.classify_intent(text)
            medical_entities = self.entity_extractor.extract_entities(text)
            urgency_level = self.urgency_assessor.assess_urgency(text, intent)
            emotional_context = self.emotion_detector.detect_emotion(text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(text, intent, medical_entities)
            
            return AnalyzedInput(
                text=text,
                intent=intent,
                medical_entities=medical_entities,
                urgency_level=urgency_level,
                confidence=confidence,
                emotional_context=emotional_context
            )
            
        except Exception as e:
            logger.error(f"Input analysis failed: {e}")
            
            # Return basic analysis on error
            return AnalyzedInput(
                text=str(user_input.content) if user_input.type == InputType.TEXT else "Analysis failed",
                intent="general_inquiry",
                medical_entities=[],
                urgency_level=3,
                confidence=0.1,
                emotional_context=None
            )
    
    def _calculate_confidence(self, text: str, intent: str, entities: List[str]) -> float:
        """Calculate confidence in the analysis."""
        base_confidence = 0.7
        
        # Adjust based on text length
        if len(text) < 10:
            base_confidence -= 0.2
        elif len(text) > 100:
            base_confidence += 0.1
        
        # Adjust based on entities found
        if entities:
            base_confidence += min(0.2, len(entities) * 0.05)
        
        # Adjust based on intent clarity
        if intent != "general_inquiry":
            base_confidence += 0.1
        
        return min(1.0, max(0.1, base_confidence))
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get tool capabilities."""
        return {
            "text_analysis": True,
            "speech_to_text": self.speech_processor is not None,
            "vision_analysis": self.vision_analyzer is not None,
            "intent_classification": True,
            "entity_extraction": True,
            "urgency_assessment": True,
            "emotion_detection": True
        }
