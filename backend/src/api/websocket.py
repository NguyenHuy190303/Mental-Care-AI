"""
WebSocket handlers for real-time chat functionality.
"""

import json
import logging
import uuid
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db_session
from ..models.database import User
from ..models.core import UserInput, InputType
from .auth import verify_token

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
    
    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        """
        Accept WebSocket connection and store user session.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            session_id: Session ID
        """
        await websocket.accept()
        connection_id = f"{user_id}:{session_id}"
        self.active_connections[connection_id] = websocket
        self.user_sessions[user_id] = session_id
        
        logger.info(f"WebSocket connected: user_id={user_id}, session_id={session_id}")
    
    def disconnect(self, user_id: str, session_id: str):
        """
        Remove WebSocket connection.
        
        Args:
            user_id: User ID
            session_id: Session ID
        """
        connection_id = f"{user_id}:{session_id}"
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        logger.info(f"WebSocket disconnected: user_id={user_id}, session_id={session_id}")
    
    async def send_personal_message(self, message: dict, user_id: str, session_id: str):
        """
        Send message to specific user session.
        
        Args:
            message: Message to send
            user_id: User ID
            session_id: Session ID
        """
        connection_id = f"{user_id}:{session_id}"
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                # Remove broken connection
                self.disconnect(user_id, session_id)
    
    async def send_error(self, error_message: str, user_id: str, session_id: str):
        """
        Send error message to user.
        
        Args:
            error_message: Error message
            user_id: User ID
            session_id: Session ID
        """
        error_response = {
            "type": "error",
            "message": error_message,
            "timestamp": str(uuid.uuid4())
        }
        await self.send_personal_message(error_response, user_id, session_id)
    
    def get_active_connections_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has active connection."""
        return user_id in self.user_sessions


# Global connection manager
manager = ConnectionManager()


async def get_user_from_token(token: str, db: AsyncSession) -> User:
    """
    Get user from JWT token for WebSocket authentication.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token_data = verify_token(token)
    
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


async def handle_websocket_message(
    message_data: dict,
    user: User,
    session_id: str,
    websocket: WebSocket
) -> Optional[dict]:
    """
    Process incoming WebSocket message.
    
    Args:
        message_data: Parsed message data
        user: Authenticated user
        session_id: Session ID
        websocket: WebSocket connection
        
    Returns:
        Response message or None
    """
    message_type = message_data.get("type")
    
    if message_type == "chat_message":
        return await handle_chat_message(message_data, user, session_id)
    elif message_type == "ping":
        return {"type": "pong", "timestamp": message_data.get("timestamp")}
    elif message_type == "typing":
        return await handle_typing_indicator(message_data, user, session_id)
    else:
        logger.warning(f"Unknown message type: {message_type}")
        return {
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }


async def handle_chat_message(
    message_data: dict,
    user: User,
    session_id: str
) -> dict:
    """
    Handle chat message from user.
    
    Args:
        message_data: Message data
        user: User object
        session_id: Session ID
        
    Returns:
        Response message
    """
    content = message_data.get("content", "").strip()
    if not content:
        return {
            "type": "error",
            "message": "Message content cannot be empty"
        }
    
    # Create UserInput object
    user_input = UserInput(
        user_id=str(user.id),
        session_id=session_id,
        type=InputType.TEXT,
        content=content,
        metadata=message_data.get("metadata", {})
    )
    
    # TODO: Process message through Linear Mental Health Agent
    # For now, return acknowledgment
    return {
        "type": "message_received",
        "message_id": str(uuid.uuid4()),
        "content": content,
        "timestamp": user_input.timestamp.isoformat(),
        "status": "processing"
    }


async def handle_typing_indicator(
    message_data: dict,
    user: User,
    session_id: str
) -> Optional[dict]:
    """
    Handle typing indicator.
    
    Args:
        message_data: Message data
        user: User object
        session_id: Session ID
        
    Returns:
        None (typing indicators are not echoed back)
    """
    is_typing = message_data.get("is_typing", False)
    logger.debug(f"User {user.username} typing: {is_typing}")
    
    # Could broadcast to other participants in group chats
    # For now, just log the event
    return None


async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    session_id: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    WebSocket endpoint for real-time chat.
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
        session_id: Session ID (optional, will generate if not provided)
        db: Database session
    """
    try:
        # Authenticate user
        user = await get_user_from_token(token, db)
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Accept connection
        await manager.connect(websocket, str(user.id), session_id)
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "session_id": session_id,
            "user_id": str(user.id),
            "username": user.username,
            "message": "Connected to Mental Health Agent"
        }
        await manager.send_personal_message(welcome_message, str(user.id), session_id)
        
        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process message
                response = await handle_websocket_message(
                    message_data, user, session_id, websocket
                )
                
                # Send response if any
                if response:
                    await manager.send_personal_message(response, str(user.id), session_id)
                
            except json.JSONDecodeError:
                await manager.send_error(
                    "Invalid JSON format", str(user.id), session_id
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_error(
                    "Internal server error", str(user.id), session_id
                )
    
    except HTTPException as e:
        # Authentication failed
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        logger.warning(f"WebSocket authentication failed: {e.detail}")
    
    except WebSocketDisconnect:
        if 'user' in locals() and 'session_id' in locals():
            manager.disconnect(str(user.id), session_id)
        logger.info("WebSocket disconnected normally")
    
    except Exception as e:
        if 'user' in locals() and 'session_id' in locals():
            manager.disconnect(str(user.id), session_id)
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
