"""
Multi-Assistant Command Center API

FastAPI endpoints for enhanced multi-assistant coordination and group chat functionality.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from triad.services import HistoryPersistenceService
from triad.agents.core import Agent
from triad.agents.registry import get_available_agents
from triad.agents.rooms import RoomManager


router = APIRouter(prefix="/multi-assistant", tags=["Multi-Assistant"])

# Service instances (in production, these would be managed by dependency injection)
history_service = HistoryPersistenceService()
room_manager = RoomManager()


class MultiAssistantSessionRequest(BaseModel):
    """Request to create a multi-assistant session."""
    session_name: str = Field(..., description="Name for the session")
    assistant_types: List[str] = Field(..., description="List of assistant types to include")
    room_config: Dict[str, Any] = Field(default_factory=dict, description="Room configuration")
    initial_message: Optional[str] = Field(None, description="Initial message to start the session")


class MultiAssistantSessionResponse(BaseModel):
    """Response for multi-assistant session creation."""
    session_id: str
    session_name: str
    active_assistants: List[str]
    room_name: str
    status: str
    created_at: str


class GroupChatMessageRequest(BaseModel):
    """Request to send a message to group chat."""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="Message content")
    sender: str = Field(default="user", description="Message sender")


class GroupChatMessageResponse(BaseModel):
    """Response for group chat message."""
    message_id: int
    session_id: str
    responses: List[Dict[str, Any]]
    timestamp: float


class SessionStatsResponse(BaseModel):
    """Response for session statistics."""
    session_info: Dict[str, Any]
    message_count: int
    command_count: int
    assistant_interaction_count: int
    active_assistants: List[str]


@router.post("/sessions", response_model=MultiAssistantSessionResponse)
async def create_multi_assistant_session(request: MultiAssistantSessionRequest) -> MultiAssistantSessionResponse:
    """Create a new multi-assistant session with group chat."""
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        room_name = f"session-{session_id}"
        
        # Get available agent types
        available_agents = get_available_agents()
        
        # Validate requested assistant types
        invalid_types = [t for t in request.assistant_types if t not in available_agents]
        if invalid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown assistant types: {invalid_types}. Available: {list(available_agents.keys())}"
            )
        
        # Create room for the session
        room = await room_manager.create_room(room_name, request.room_config)
        
        # Initialize agents for the session
        session_agents = []
        for agent_type in request.assistant_types:
            agent_class = available_agents[agent_type]
            agent = agent_class()
            session_agents.append(agent.name)
            
            # Subscribe agent to the room
            await room.add_agent(agent)
        
        # Store session in history service
        await history_service.create_multi_assistant_session(
            session_id=session_id,
            session_name=request.session_name,
            active_assistants=session_agents,
            room_config=request.room_config
        )
        
        # Send initial message if provided
        if request.initial_message:
            await history_service.store_chat_message(
                room=room_name,
                sender="system",
                content=f"Session '{request.session_name}' started with assistants: {', '.join(session_agents)}",
                role="system"
            )
            
            await history_service.store_chat_message(
                room=room_name,
                sender="user",
                content=request.initial_message,
                role="user"
            )
        
        return MultiAssistantSessionResponse(
            session_id=session_id,
            session_name=request.session_name,
            active_assistants=session_agents,
            room_name=room_name,
            status="active",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionStatsResponse)
async def get_session_info(session_id: str) -> SessionStatsResponse:
    """Get information and statistics for a multi-assistant session."""
    try:
        stats = await history_service.get_session_stats(session_id)
        
        if not stats.get("session_info"):
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get active assistants from session info
        session_info = stats["session_info"]
        active_assistants = []
        if session_info.get("active_assistants"):
            import json
            active_assistants = json.loads(session_info["active_assistants"])
        
        return SessionStatsResponse(
            session_info=stats["session_info"],
            message_count=stats["message_count"],
            command_count=stats["command_count"],
            assistant_interaction_count=stats["assistant_interaction_count"],
            active_assistants=active_assistants
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.post("/sessions/{session_id}/messages", response_model=GroupChatMessageResponse)
async def send_group_chat_message(
    session_id: str, 
    request: GroupChatMessageRequest
) -> GroupChatMessageResponse:
    """Send a message to a multi-assistant group chat session."""
    try:
        room_name = f"session-{session_id}"
        
        # Check if session exists
        stats = await history_service.get_session_stats(session_id)
        if not stats.get("session_info"):
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Store user message
        message_id = await history_service.store_chat_message(
            room=room_name,
            sender=request.sender,
            content=request.message,
            role="user"
        )
        
        # Get room and broadcast message to agents
        room = room_manager.get_room(room_name)
        if not room:
            raise HTTPException(status_code=404, detail="Session room not found")
        
        # Broadcast message to all agents in the room
        from triad.agents.core import Message
        message = Message(
            room=room_name,
            sender=request.sender,
            content=request.message,
            role="user",
            ts=datetime.now(timezone.utc).timestamp()
        )
        
        # Collect responses from agents (simplified - in real implementation, 
        # this would be handled asynchronously)
        responses = []
        for agent in room.agents:
            try:
                # Simulate agent response (in real implementation, this would be async)
                response_content = f"Response from {agent.name} to: '{request.message}'"
                
                # Store agent response
                await history_service.store_chat_message(
                    room=room_name,
                    sender=agent.name,
                    content=response_content,
                    role="assistant"
                )
                
                responses.append({
                    "agent": agent.name,
                    "content": response_content,
                    "timestamp": datetime.now(timezone.utc).timestamp()
                })
                
            except Exception as e:
                responses.append({
                    "agent": agent.name,
                    "error": f"Agent response error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).timestamp()
                })
        
        return GroupChatMessageResponse(
            message_id=message_id,
            session_id=session_id,
            responses=responses,
            timestamp=datetime.now(timezone.utc).timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Get message history for a multi-assistant session."""
    try:
        room_name = f"session-{session_id}"
        
        messages = await history_service.get_chat_history(
            room=room_name,
            limit=limit,
            offset=offset
        )
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(messages),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.delete("/sessions/{session_id}")
async def end_session(session_id: str) -> Dict[str, str]:
    """End a multi-assistant session."""
    try:
        room_name = f"session-{session_id}"
        
        # Check if session exists
        stats = await history_service.get_session_stats(session_id)
        if not stats.get("session_info"):
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Store session end message
        await history_service.store_chat_message(
            room=room_name,
            sender="system",
            content="Session ended",
            role="system"
        )
        
        # Clean up room
        room_manager.remove_room(room_name)
        
        return {
            "status": "ended",
            "session_id": session_id,
            "message": "Session ended successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get("/available-assistants")
async def get_available_assistants() -> Dict[str, Any]:
    """Get list of available assistant types for multi-assistant sessions."""
    try:
        available_agents = get_available_agents()
        
        assistants = []
        for agent_type, agent_class in available_agents.items():
            # Create temporary instance to get info
            temp_agent = agent_class()
            assistants.append({
                "type": agent_type,
                "name": temp_agent.name,
                "role": temp_agent.role.__dict__ if hasattr(temp_agent, 'role') else {},
                "description": temp_agent.__class__.__doc__ or "No description available"
            })
        
        return {
            "available_assistants": assistants,
            "total_count": len(assistants)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available assistants: {str(e)}")


@router.get("/sessions")
async def list_active_sessions(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """List active multi-assistant sessions.""" 
    try:
        # This is a simplified implementation - in production, you'd maintain 
        # an active sessions registry
        
        # For now, return empty list since we don't have a persistent session store
        return {
            "active_sessions": [],
            "total_count": 0,
            "limit": limit,
            "offset": offset,
            "note": "Session listing not fully implemented - use specific session endpoints"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")