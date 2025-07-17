"""
Linear Mental Health Agent - Single-threaded sequential processing agent.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

from ..models.core import (
    UserInput, AnalyzedInput, RAGResults, AgentResponse, 
    ProcessingContext, ErrorResponse, ValidationResult
)
from ..tools.rag_search_tool import RAGSearchTool
from ..tools.input_analysis_tool import InputAnalysisTool
from ..tools.context_management import ContextManagementSystem
from ..tools.medical_image_search_tool import MedicalImageSearchTool
from .chain_of_thought_engine import ChainOfThoughtEngine
from .safety_compliance_layer import SafetyComplianceLayer, SafetyLevel
from ..database import get_db_session
from ..models.database import UsageMetricCreate

logger = logging.getLogger(__name__)


class ProcessingStep:
    """Represents a step in the linear processing pipeline."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.success: bool = False
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    def start(self):
        """Mark step as started."""
        self.start_time = datetime.utcnow()
        logger.debug(f"Starting step: {self.name}")
    
    def complete(self, success: bool = True, error: Optional[str] = None, **metadata):
        """Mark step as completed."""
        self.end_time = datetime.utcnow()
        self.success = success
        self.error = error
        self.metadata.update(metadata)
        
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        logger.debug(f"Completed step: {self.name} (success={success}, duration={duration:.2f}s)")
    
    @property
    def duration(self) -> float:
        """Get step duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class LinearMentalHealthAgent:
    """
    Single-threaded linear agent for mental health support.
    
    Follows the Single-Threaded Linear Agent pattern:
    - One main agent processes requests sequentially
    - Uses specialized tools in sequence, not parallel sub-agents
    - Maintains complete context throughout the pipeline
    - Ensures consistent, explainable responses
    """
    
    def __init__(
        self,
        rag_search_tool: RAGSearchTool,
        chain_of_thought_engine: ChainOfThoughtEngine,
        safety_compliance_layer: SafetyComplianceLayer,
        input_analysis_tool: Optional[InputAnalysisTool] = None,
        context_management_system: Optional[ContextManagementSystem] = None,
        medical_image_search_tool: Optional[MedicalImageSearchTool] = None,
        enable_detailed_logging: bool = True
    ):
        """
        Initialize Linear Mental Health Agent.

        Args:
            rag_search_tool: RAG search tool for knowledge retrieval
            chain_of_thought_engine: Chain-of-thought reasoning engine
            safety_compliance_layer: Safety and compliance validation
            input_analysis_tool: Input analysis tool for multimodal processing
            context_management_system: Context management for conversation history
            medical_image_search_tool: Medical image search capabilities
            enable_detailed_logging: Whether to enable detailed step logging
        """
        self.rag_search_tool = rag_search_tool
        self.chain_of_thought_engine = chain_of_thought_engine
        self.safety_compliance_layer = safety_compliance_layer
        self.input_analysis_tool = input_analysis_tool
        self.context_management_system = context_management_system
        self.medical_image_search_tool = medical_image_search_tool
        self.enable_detailed_logging = enable_detailed_logging
        
        # Processing pipeline steps
        self.pipeline_steps = [
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
        
        logger.info("Linear Mental Health Agent initialized")
    
    async def process_request(self, user_input: UserInput) -> Tuple[AgentResponse, Dict[str, Any]]:
        """
        Process user request through the linear pipeline.
        
        Args:
            user_input: User input to process
            
        Returns:
            Tuple of (agent response, processing metadata)
        """
        # Initialize processing context
        context = ProcessingContext(user_input=user_input)
        processing_steps = []
        trace_id = str(uuid.uuid4())
        
        logger.info(f"Processing request {trace_id} for user {user_input.user_id}")
        
        try:
            # Step 1: Input Validation
            step = ProcessingStep("input_validation", "Validate user input")
            step.start()
            processing_steps.append(step)
            
            validation_result = await self._validate_input(user_input)
            if not validation_result.is_valid:
                step.complete(False, "Input validation failed")
                return await self._create_error_response(
                    "Invalid input provided",
                    validation_result.errors,
                    trace_id
                ), self._create_processing_metadata(processing_steps, trace_id)
            
            step.complete(True, validation_errors=validation_result.errors)
            
            # Step 2: Input Analysis
            step = ProcessingStep("input_analysis", "Analyze user input for intent and entities")
            step.start()
            processing_steps.append(step)

            try:
                if self.input_analysis_tool:
                    context.analyzed_input = await self.input_analysis_tool.analyze_input(user_input)
                else:
                    context.analyzed_input = await self._analyze_input(user_input)

                step.complete(True,
                    intent=context.analyzed_input.intent,
                    urgency=context.analyzed_input.urgency_level,
                    entities_count=len(context.analyzed_input.medical_entities)
                )
            except Exception as e:
                step.complete(False, f"Input analysis failed: {e}")
                return await self._create_error_response(
                    "Failed to analyze input",
                    [str(e)],
                    trace_id
                ), self._create_processing_metadata(processing_steps, trace_id)

            # Step 3: Context Retrieval
            step = ProcessingStep("context_retrieval", "Retrieve user context and conversation history")
            step.start()
            processing_steps.append(step)

            try:
                if self.context_management_system:
                    context.user_context = await self.context_management_system.get_user_context(
                        user_input.user_id,
                        user_input.session_id
                    )
                    step.complete(True, has_context=context.user_context is not None)
                else:
                    step.complete(True, has_context=False)
            except Exception as e:
                step.complete(False, f"Context retrieval failed: {e}")
                # Continue without context rather than failing
            
            # Step 4: Safety Assessment
            step = ProcessingStep("safety_assessment", "Assess input safety level")
            step.start()
            processing_steps.append(step)
            
            safety_level, safety_concerns = await self.safety_compliance_layer.assess_input_safety(
                user_input, context.analyzed_input
            )
            
            step.complete(True, 
                safety_level=safety_level.value,
                safety_concerns=safety_concerns
            )
            
            # Handle critical safety situations immediately
            if safety_level == SafetyLevel.BLOCKED:
                return await self._create_safety_response(safety_concerns, trace_id), \
                       self._create_processing_metadata(processing_steps, trace_id)
            
            # Step 5: Knowledge Retrieval
            step = ProcessingStep("knowledge_retrieval", "Retrieve relevant medical knowledge")
            step.start()
            processing_steps.append(step)

            try:
                context.rag_results = await self._retrieve_knowledge(context)
                step.complete(True,
                    documents_found=len(context.rag_results.documents),
                    citations_found=len(context.rag_results.citations),
                    avg_confidence=sum(context.rag_results.confidence_scores) / len(context.rag_results.confidence_scores) if context.rag_results.confidence_scores else 0
                )
            except Exception as e:
                step.complete(False, f"Knowledge retrieval failed: {e}")
                # Continue with empty results rather than failing
                context.rag_results = RAGResults(documents=[], citations=[], confidence_scores=[])

            # Step 6: Medical Image Search
            step = ProcessingStep("image_search", "Search for relevant medical images")
            step.start()
            processing_steps.append(step)

            try:
                if self.medical_image_search_tool and context.analyzed_input:
                    # Search for images related to medical entities
                    image_queries = context.analyzed_input.medical_entities[:3]  # Limit to top 3 entities

                    for query in image_queries:
                        images = await self.medical_image_search_tool.search_medical_images(
                            query=query,
                            max_results=2,
                            min_relevance_score=0.5
                        )
                        context.medical_images.extend(images)

                    step.complete(True, images_found=len(context.medical_images))
                else:
                    step.complete(True, images_found=0)
            except Exception as e:
                step.complete(False, f"Image search failed: {e}")
                # Continue without images
            
            # Step 7: Reasoning and Response Generation
            step = ProcessingStep("reasoning_generation", "Generate response using chain-of-thought")
            step.start()
            processing_steps.append(step)
            
            try:
                agent_response, reasoning_steps = await self.chain_of_thought_engine.generate_response(context)
                step.complete(True,
                    reasoning_steps_count=len(reasoning_steps),
                    confidence_level=agent_response.confidence_level,
                    model_used=agent_response.response_metadata.get("model_used")
                )
            except Exception as e:
                step.complete(False, f"Response generation failed: {e}")
                return await self._create_error_response(
                    "Failed to generate response",
                    [str(e)],
                    trace_id
                ), self._create_processing_metadata(processing_steps, trace_id)
            
            # Step 8: Safety Validation
            step = ProcessingStep("safety_validation", "Validate response safety and compliance")
            step.start()
            processing_steps.append(step)
            
            compliance_checks = await self.safety_compliance_layer.validate_response_safety(agent_response)
            compliance_summary = self.safety_compliance_layer.get_compliance_summary(compliance_checks)
            
            if not compliance_summary["overall_safe"]:
                logger.warning(f"Response failed safety validation: {compliance_summary['failed_checks']}")
            
            # Enhance response with safety measures
            agent_response = await self.safety_compliance_layer.enhance_response_safety(
                agent_response, safety_level
            )
            
            step.complete(True,
                compliance_rate=compliance_summary["compliance_rate"],
                failed_checks=compliance_summary["failed_checks"]
            )
            
            # Step 9: Response Formatting
            step = ProcessingStep("response_formatting", "Format final response")
            step.start()
            processing_steps.append(step)
            
            # Add processing metadata to response
            agent_response.response_metadata.update({
                "trace_id": trace_id,
                "processing_time": sum(s.duration for s in processing_steps),
                "safety_level": safety_level.value,
                "compliance_summary": compliance_summary
            })
            
            step.complete(True, response_length=len(agent_response.content))

            # Step 10: Context Update
            step = ProcessingStep("context_update", "Update user context with interaction")
            step.start()
            processing_steps.append(step)

            try:
                if self.context_management_system and context.user_context:
                    context.user_context = await self.context_management_system.update_context(
                        context.user_context,
                        user_input,
                        context.analyzed_input,
                        agent_response
                    )
                    step.complete(True, context_updated=True)
                else:
                    step.complete(True, context_updated=False)
            except Exception as e:
                step.complete(False, f"Context update failed: {e}")
                # Continue without context update

            # Log usage metrics
            await self._log_usage_metrics(user_input, agent_response, processing_steps)
            
            logger.info(f"Successfully processed request {trace_id}")
            return agent_response, self._create_processing_metadata(processing_steps, trace_id)
            
        except Exception as e:
            logger.error(f"Unexpected error processing request {trace_id}: {e}")
            return await self._create_error_response(
                "An unexpected error occurred",
                [str(e)],
                trace_id
            ), self._create_processing_metadata(processing_steps, trace_id)
    
    async def _validate_input(self, user_input: UserInput) -> ValidationResult:
        """Validate user input."""
        errors = []
        warnings = []
        
        # Check required fields
        if not user_input.content or (isinstance(user_input.content, str) and not user_input.content.strip()):
            errors.append("Input content cannot be empty")
        
        # Check content length
        if isinstance(user_input.content, str) and len(user_input.content) > 10000:
            errors.append("Input content too long (max 10,000 characters)")
        
        # Check for valid user and session IDs
        if not user_input.user_id or not user_input.session_id:
            errors.append("User ID and session ID are required")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            confidence=1.0 if len(errors) == 0 else 0.0
        )
    
    async def _analyze_input(self, user_input: UserInput) -> AnalyzedInput:
        """Analyze user input for intent and entities."""
        # Simple analysis - in production, this would use NLP models
        content = str(user_input.content).lower()
        
        # Determine intent
        intent = "general_inquiry"
        if any(word in content for word in ["crisis", "emergency", "suicide", "harm"]):
            intent = "crisis"
        elif any(word in content for word in ["sad", "depressed", "depression", "down"]):
            intent = "emotional_support"
        elif any(word in content for word in ["medication", "drug", "pill", "prescription"]):
            intent = "medication_query"
        elif any(word in content for word in ["symptom", "feel", "experience"]):
            intent = "symptom_description"
        elif any(word in content for word in ["doctor", "therapist", "treatment"]):
            intent = "medical_question"
        
        # Extract medical entities (simplified)
        medical_entities = []
        medical_terms = [
            "depression", "anxiety", "bipolar", "ptsd", "ocd", "adhd",
            "therapy", "medication", "counseling", "stress", "panic"
        ]
        for term in medical_terms:
            if term in content:
                medical_entities.append(term)
        
        # Determine urgency level
        urgency_level = 3  # Default
        if intent == "crisis":
            urgency_level = 10
        elif any(word in content for word in ["urgent", "emergency", "immediate"]):
            urgency_level = 8
        elif any(word in content for word in ["worried", "concerned", "anxious"]):
            urgency_level = 6
        
        # Detect emotional context
        emotional_context = None
        if any(word in content for word in ["sad", "depressed", "down", "hopeless"]):
            emotional_context = "sadness"
        elif any(word in content for word in ["anxious", "worried", "nervous", "panic"]):
            emotional_context = "anxiety"
        elif any(word in content for word in ["angry", "frustrated", "mad"]):
            emotional_context = "anger"
        
        return AnalyzedInput(
            text=str(user_input.content),
            intent=intent,
            medical_entities=medical_entities,
            urgency_level=urgency_level,
            confidence=0.8,  # Simplified confidence
            emotional_context=emotional_context
        )
    
    async def _retrieve_knowledge(self, context: ProcessingContext) -> RAGResults:
        """Retrieve relevant medical knowledge."""
        if not context.analyzed_input:
            return RAGResults(documents=[], citations=[], confidence_scores=[])
        
        # Build search query
        query = context.analyzed_input.text
        
        # Add medical entities to improve search
        if context.analyzed_input.medical_entities:
            query += " " + " ".join(context.analyzed_input.medical_entities)
        
        # Perform RAG search
        return await self.rag_search_tool.search(
            query=query,
            max_results=5,
            include_low_confidence=False
        )
    
    async def _create_error_response(
        self, 
        message: str, 
        errors: List[str], 
        trace_id: str
    ) -> AgentResponse:
        """Create error response."""
        return AgentResponse(
            content=f"I apologize, but I encountered an issue: {message}. Please try again or contact support if the problem persists.",
            citations=[],
            medical_images=[],
            reasoning_steps=[f"Error: {message}"],
            confidence_level=0.0,
            safety_warnings=["Error occurred during processing"],
            medical_disclaimer=self.safety_compliance_layer.medical_disclaimer_template,
            response_metadata={
                "trace_id": trace_id,
                "error": True,
                "errors": errors
            }
        )
    
    async def _create_safety_response(self, safety_concerns: List[str], trace_id: str) -> AgentResponse:
        """Create safety-focused response for blocked content."""
        return AgentResponse(
            content="I'm concerned about your safety. Please reach out to a mental health professional or crisis hotline immediately for support.",
            citations=[],
            medical_images=[],
            reasoning_steps=["Safety concerns detected", "Providing crisis resources"],
            confidence_level=1.0,
            safety_warnings=safety_concerns,
            medical_disclaimer=self.safety_compliance_layer.medical_disclaimer_template,
            response_metadata={
                "trace_id": trace_id,
                "safety_blocked": True,
                "safety_concerns": safety_concerns
            }
        )
    
    def _create_processing_metadata(self, steps: List[ProcessingStep], trace_id: str) -> Dict[str, Any]:
        """Create processing metadata summary."""
        total_duration = sum(step.duration for step in steps)
        successful_steps = sum(1 for step in steps if step.success)
        
        return {
            "trace_id": trace_id,
            "total_duration": total_duration,
            "steps_completed": len(steps),
            "steps_successful": successful_steps,
            "success_rate": successful_steps / len(steps) if steps else 0.0,
            "step_details": [
                {
                    "name": step.name,
                    "duration": step.duration,
                    "success": step.success,
                    "error": step.error,
                    "metadata": step.metadata
                }
                for step in steps
            ]
        }
    
    async def _log_usage_metrics(
        self, 
        user_input: UserInput, 
        response: AgentResponse, 
        steps: List[ProcessingStep]
    ):
        """Log usage metrics to database."""
        try:
            # Calculate metrics
            total_tokens = len(str(user_input.content).split()) + len(response.content.split())
            processing_time = sum(step.duration for step in steps) * 1000  # Convert to ms
            
            # Estimate cost (simplified)
            model_used = response.response_metadata.get("model_used", "unknown")
            estimated_cost = 0.001 * (total_tokens / 1000)  # Rough estimation
            
            # Create usage metric
            usage_metric = UsageMetricCreate(
                session_id=user_input.session_id,
                endpoint="linear_agent_process",
                model_used=model_used,
                tokens_consumed=total_tokens,
                response_time_ms=int(processing_time),
                cost_usd=estimated_cost,
                request_metadata={
                    "trace_id": response.response_metadata.get("trace_id"),
                    "intent": getattr(response, "analyzed_input", {}).get("intent"),
                    "safety_level": response.response_metadata.get("safety_level"),
                    "confidence_level": response.confidence_level
                }
            )
            
            # Log to database (would need database session)
            logger.info(f"Usage metrics: {usage_metric.dict()}")
            
        except Exception as e:
            logger.error(f"Failed to log usage metrics: {e}")
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and health information."""
        return {
            "agent_type": "LinearMentalHealthAgent",
            "status": "healthy",
            "components": {
                "rag_search_tool": "available",
                "chain_of_thought_engine": "available", 
                "safety_compliance_layer": "available"
            },
            "pipeline_steps": self.pipeline_steps,
            "detailed_logging": self.enable_detailed_logging
        }
