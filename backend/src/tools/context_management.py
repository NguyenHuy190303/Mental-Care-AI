"""
Context Management System for conversation history and user profiles.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib

from ..models.core import UserContext, UserInput, AgentResponse
from ..database.encryption import encrypt_user_data, decrypt_user_data
from .chromadb_integration import ChromaDBManager

logger = logging.getLogger(__name__)


class ConversationCompressor:
    """Compresses conversation history while preserving important context."""
    
    def __init__(self, max_history_length: int = 5000):
        """
        Initialize conversation compressor.
        
        Args:
            max_history_length: Maximum length of compressed history
        """
        self.max_history_length = max_history_length
    
    def compress_conversation(
        self,
        messages: List[Dict[str, Any]],
        preserve_recent: int = 3
    ) -> str:
        """
        Compress conversation history.
        
        Args:
            messages: List of conversation messages
            preserve_recent: Number of recent messages to preserve in full
            
        Returns:
            Compressed conversation string
        """
        if not messages:
            return ""
        
        # Sort messages by timestamp
        sorted_messages = sorted(
            messages,
            key=lambda x: x.get("timestamp", datetime.min)
        )
        
        # Preserve recent messages
        recent_messages = sorted_messages[-preserve_recent:] if preserve_recent > 0 else []
        older_messages = sorted_messages[:-preserve_recent] if preserve_recent > 0 else sorted_messages
        
        # Compress older messages
        compressed_parts = []
        
        if older_messages:
            # Extract key themes and topics
            themes = self._extract_themes(older_messages)
            compressed_parts.append(f"Previous conversation themes: {', '.join(themes)}")
            
            # Summarize key concerns
            concerns = self._extract_concerns(older_messages)
            if concerns:
                compressed_parts.append(f"Key concerns discussed: {', '.join(concerns)}")
            
            # Note any crisis or urgent situations
            crisis_mentions = self._extract_crisis_mentions(older_messages)
            if crisis_mentions:
                compressed_parts.append(f"Crisis situations mentioned: {', '.join(crisis_mentions)}")
        
        # Add recent messages in full
        if recent_messages:
            compressed_parts.append("Recent conversation:")
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:500]  # Limit length
                timestamp = msg.get("timestamp", "")
                compressed_parts.append(f"{role}: {content} [{timestamp}]")
        
        compressed = "\n".join(compressed_parts)
        
        # Ensure it doesn't exceed max length
        if len(compressed) > self.max_history_length:
            compressed = compressed[:self.max_history_length] + "..."
        
        return compressed
    
    def _extract_themes(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract main themes from messages."""
        themes = set()
        
        theme_keywords = {
            "depression": ["depressed", "sad", "down", "depression"],
            "anxiety": ["anxious", "worried", "panic", "anxiety"],
            "relationships": ["relationship", "partner", "family", "friends"],
            "work_stress": ["work", "job", "career", "stress", "workplace"],
            "sleep_issues": ["sleep", "insomnia", "tired", "exhausted"],
            "medication": ["medication", "pills", "prescription", "side effects"],
            "therapy": ["therapy", "therapist", "counseling", "treatment"]
        }
        
        for message in messages:
            content = message.get("content", "").lower()
            for theme, keywords in theme_keywords.items():
                if any(keyword in content for keyword in keywords):
                    themes.add(theme)
        
        return list(themes)
    
    def _extract_concerns(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract key concerns from messages."""
        concerns = set()
        
        concern_patterns = [
            "worried about", "concerned about", "struggling with",
            "having trouble", "difficulty with", "problems with"
        ]
        
        for message in messages:
            content = message.get("content", "").lower()
            for pattern in concern_patterns:
                if pattern in content:
                    # Extract the concern (simplified)
                    start_idx = content.find(pattern) + len(pattern)
                    concern_text = content[start_idx:start_idx+50].strip()
                    if concern_text:
                        concerns.add(concern_text.split('.')[0])
        
        return list(concerns)[:5]  # Limit to top 5 concerns
    
    def _extract_crisis_mentions(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract crisis-related mentions."""
        crisis_mentions = set()
        
        crisis_keywords = [
            "suicide", "self-harm", "crisis", "emergency", "hopeless",
            "worthless", "end my life", "hurt myself"
        ]
        
        for message in messages:
            content = message.get("content", "").lower()
            for keyword in crisis_keywords:
                if keyword in content:
                    crisis_mentions.add(keyword)
        
        return list(crisis_mentions)


class UserProfileManager:
    """Manages user profiles and preferences."""
    
    def __init__(self):
        """Initialize user profile manager."""
        self.default_profile = {
            "preferences": {
                "communication_style": "empathetic",
                "detail_level": "moderate",
                "crisis_sensitivity": "high"
            },
            "history_summary": {
                "main_concerns": [],
                "treatment_history": [],
                "medication_history": [],
                "crisis_episodes": []
            },
            "demographics": {
                "age_range": None,
                "location": None,
                "timezone": None
            },
            "privacy_settings": {
                "data_retention_days": 90,
                "share_anonymous_data": False,
                "emergency_contact": None
            }
        }
    
    def create_profile(self, user_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create new user profile.
        
        Args:
            user_id: User identifier
            initial_data: Initial profile data
            
        Returns:
            Created profile
        """
        profile = self.default_profile.copy()
        
        if initial_data:
            profile.update(initial_data)
        
        profile["created_at"] = datetime.utcnow().isoformat()
        profile["last_updated"] = datetime.utcnow().isoformat()
        profile["user_id"] = user_id
        
        return profile
    
    def update_profile(
        self,
        current_profile: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile with new information.
        
        Args:
            current_profile: Current profile data
            updates: Updates to apply
            
        Returns:
            Updated profile
        """
        updated_profile = current_profile.copy()
        
        # Deep merge updates
        for key, value in updates.items():
            if key in updated_profile and isinstance(updated_profile[key], dict) and isinstance(value, dict):
                updated_profile[key].update(value)
            else:
                updated_profile[key] = value
        
        updated_profile["last_updated"] = datetime.utcnow().isoformat()
        
        return updated_profile
    
    def extract_profile_updates(
        self,
        user_input: UserInput,
        agent_response: AgentResponse
    ) -> Dict[str, Any]:
        """
        Extract profile updates from conversation.
        
        Args:
            user_input: User input
            agent_response: Agent response
            
        Returns:
            Profile updates
        """
        updates = {}
        content = str(user_input.content).lower()
        
        # Extract demographic information
        if "years old" in content or "age" in content:
            # Simple age extraction (would be more sophisticated in production)
            import re
            age_match = re.search(r'(\d+)\s*years?\s*old', content)
            if age_match:
                age = int(age_match.group(1))
                if 18 <= age <= 100:
                    updates["demographics"] = {"age_range": f"{age//10*10}-{age//10*10+9}"}
        
        # Extract treatment mentions
        treatment_keywords = ["therapy", "therapist", "counseling", "psychiatrist", "psychologist"]
        if any(keyword in content for keyword in treatment_keywords):
            if "history_summary" not in updates:
                updates["history_summary"] = {}
            if "treatment_history" not in updates["history_summary"]:
                updates["history_summary"]["treatment_history"] = []
            
            for keyword in treatment_keywords:
                if keyword in content and keyword not in updates["history_summary"]["treatment_history"]:
                    updates["history_summary"]["treatment_history"].append(keyword)
        
        # Extract medication mentions
        medication_keywords = ["medication", "pills", "prescription", "antidepressant", "anxiety medication"]
        if any(keyword in content for keyword in medication_keywords):
            if "history_summary" not in updates:
                updates["history_summary"] = {}
            if "medication_history" not in updates["history_summary"]:
                updates["history_summary"]["medication_history"] = []
            
            for keyword in medication_keywords:
                if keyword in content and keyword not in updates["history_summary"]["medication_history"]:
                    updates["history_summary"]["medication_history"].append(keyword)
        
        return updates


class SessionContextManager:
    """Manages session-specific context and state."""
    
    def __init__(self, session_timeout_hours: int = 24):
        """
        Initialize session context manager.
        
        Args:
            session_timeout_hours: Hours after which session expires
        """
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Create new session context.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session context
        """
        context = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0,
            "current_topic": None,
            "urgency_level": 3,
            "emotional_state": None,
            "conversation_flow": [],
            "pending_actions": [],
            "session_metadata": {}
        }
        
        self.active_sessions[session_id] = context
        return context
    
    def update_session_context(
        self,
        session_id: str,
        user_input: UserInput,
        analyzed_input: Optional[Any] = None,
        agent_response: Optional[AgentResponse] = None
    ) -> Dict[str, Any]:
        """
        Update session context with new interaction.
        
        Args:
            session_id: Session identifier
            user_input: User input
            analyzed_input: Analyzed input data
            agent_response: Agent response
            
        Returns:
            Updated session context
        """
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = self.create_session_context(
                user_input.user_id, session_id
            )
        
        context = self.active_sessions[session_id]
        context["last_activity"] = datetime.utcnow()
        context["message_count"] += 1
        
        # Update from analyzed input
        if analyzed_input:
            context["current_topic"] = analyzed_input.intent
            context["urgency_level"] = analyzed_input.urgency_level
            context["emotional_state"] = analyzed_input.emotional_context
        
        # Track conversation flow
        context["conversation_flow"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_input_type": user_input.type.value,
            "intent": analyzed_input.intent if analyzed_input else "unknown",
            "urgency": analyzed_input.urgency_level if analyzed_input else 3,
            "response_confidence": agent_response.confidence_level if agent_response else 0.0
        })
        
        # Keep only recent flow items
        if len(context["conversation_flow"]) > 20:
            context["conversation_flow"] = context["conversation_flow"][-20:]
        
        return context
    
    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session context if it exists and is not expired."""
        if session_id not in self.active_sessions:
            return None
        
        context = self.active_sessions[session_id]
        
        # Check if session has expired
        if datetime.utcnow() - context["last_activity"] > self.session_timeout:
            del self.active_sessions[session_id]
            return None
        
        return context
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, context in self.active_sessions.items()
            if current_time - context["last_activity"] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


class ContextManagementSystem:
    """Main context management system."""
    
    def __init__(self, chromadb_manager: Optional[ChromaDBManager] = None):
        """
        Initialize context management system.
        
        Args:
            chromadb_manager: ChromaDB manager for vector storage
        """
        self.conversation_compressor = ConversationCompressor()
        self.profile_manager = UserProfileManager()
        self.session_manager = SessionContextManager()
        self.chromadb_manager = chromadb_manager
        
        logger.info("Context Management System initialized")
    
    async def get_user_context(
        self,
        user_id: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> UserContext:
        """
        Get comprehensive user context.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            conversation_history: Recent conversation history
            
        Returns:
            User context object
        """
        # Get or create session context
        session_context = self.session_manager.get_session_context(session_id)
        if not session_context:
            session_context = self.session_manager.create_session_context(user_id, session_id)
        
        # Compress conversation history
        compressed_history = ""
        if conversation_history:
            compressed_history = self.conversation_compressor.compress_conversation(
                conversation_history
            )
        
        # Get user profile (would typically load from database)
        user_profile = self.profile_manager.create_profile(user_id)
        
        # Create user context
        user_context = UserContext(
            user_id=user_id,
            session_id=session_id,
            compressed_history=compressed_history,
            user_profile=user_profile,
            session_context=session_context,
            last_updated=datetime.utcnow()
        )
        
        return user_context
    
    async def update_context(
        self,
        user_context: UserContext,
        user_input: UserInput,
        analyzed_input: Optional[Any] = None,
        agent_response: Optional[AgentResponse] = None
    ) -> UserContext:
        """
        Update user context with new interaction.
        
        Args:
            user_context: Current user context
            user_input: User input
            analyzed_input: Analyzed input data
            agent_response: Agent response
            
        Returns:
            Updated user context
        """
        # Update session context
        updated_session_context = self.session_manager.update_session_context(
            user_context.session_id,
            user_input,
            analyzed_input,
            agent_response
        )
        
        # Extract profile updates
        profile_updates = self.profile_manager.extract_profile_updates(
            user_input,
            agent_response
        )
        
        # Update user profile
        updated_profile = user_context.user_profile.copy()
        if profile_updates:
            updated_profile = self.profile_manager.update_profile(
                updated_profile,
                profile_updates
            )
        
        # Store context in vector database if available
        if self.chromadb_manager:
            await self._store_context_vector(user_context, user_input, agent_response)
        
        # Create updated context
        updated_context = UserContext(
            user_id=user_context.user_id,
            session_id=user_context.session_id,
            compressed_history=user_context.compressed_history,
            user_profile=updated_profile,
            session_context=updated_session_context,
            last_updated=datetime.utcnow()
        )
        
        return updated_context
    
    async def _store_context_vector(
        self,
        user_context: UserContext,
        user_input: UserInput,
        agent_response: Optional[AgentResponse]
    ):
        """Store context in vector database for similarity search."""
        try:
            if not self.chromadb_manager:
                return
            
            user_collection = self.chromadb_manager.get_user_contexts_collection()
            
            # Create context text for embedding
            context_text = f"User input: {user_input.content}"
            if agent_response:
                context_text += f" Agent response: {agent_response.content[:200]}"
            
            # Add context metadata
            metadata = {
                "user_id": user_context.user_id,
                "session_id": user_context.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "input_type": user_input.type.value,
                "urgency_level": getattr(user_input, "urgency_level", 3),
                "emotional_context": user_context.session_context.get("emotional_state")
            }
            
            await user_collection.add_user_context(
                user_context.user_id,
                user_context.session_id,
                context_text,
                metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to store context vector: {e}")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        self.session_manager.cleanup_expired_sessions()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get context management system statistics."""
        return {
            "active_sessions": len(self.session_manager.active_sessions),
            "compression_max_length": self.conversation_compressor.max_history_length,
            "session_timeout_hours": self.session_manager.session_timeout.total_seconds() / 3600,
            "vector_storage_enabled": self.chromadb_manager is not None
        }
