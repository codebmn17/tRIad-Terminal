"""
History Persistence API

FastAPI endpoints for accessing chat history, command history, and assistant interactions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from triad.services import HistoryPersistenceService


router = APIRouter(prefix="/history", tags=["History"])

# Service instance
history_service = HistoryPersistenceService()


class ChatHistoryResponse(BaseModel):
    """Response for chat history query."""
    messages: List[Dict[str, Any]]
    total_count: int
    room: Optional[str]
    limit: int
    offset: int


class CommandHistoryResponse(BaseModel):
    """Response for command history query."""
    commands: List[Dict[str, Any]]
    total_count: int
    limit: int
    filters: Dict[str, Any]


class AssistantInteractionResponse(BaseModel):
    """Response for assistant interaction history."""
    interactions: List[Dict[str, Any]]
    total_count: int
    limit: int
    filters: Dict[str, Any]


class HistoryStatsResponse(BaseModel):
    """Response for history statistics."""
    total_messages: int
    total_commands: int
    total_interactions: int
    rooms: List[str]
    date_range: Dict[str, str]


@router.get("/chat", response_model=ChatHistoryResponse)
async def get_chat_history(
    room: Optional[str] = Query(None, description="Filter by room name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    start_time: Optional[float] = Query(None, description="Start timestamp (Unix time)"),
    end_time: Optional[float] = Query(None, description="End timestamp (Unix time)")
) -> ChatHistoryResponse:
    """Get chat message history with optional filtering."""
    try:
        messages = await history_service.get_chat_history(
            room=room,
            limit=limit,
            offset=offset,
            start_time=start_time,
            end_time=end_time
        )
        
        return ChatHistoryResponse(
            messages=messages,
            total_count=len(messages),
            room=room,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.get("/commands", response_model=CommandHistoryResponse)
async def get_command_history(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    success_only: Optional[bool] = Query(None, description="Filter by success status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of commands to return")
) -> CommandHistoryResponse:
    """Get command execution history with optional filtering."""
    try:
        commands = await history_service.get_command_history(
            session_id=session_id,
            user_id=user_id,
            success_only=success_only,
            limit=limit
        )
        
        filters = {}
        if session_id:
            filters["session_id"] = session_id
        if user_id:
            filters["user_id"] = user_id
        if success_only is not None:
            filters["success_only"] = success_only
        
        return CommandHistoryResponse(
            commands=commands,
            total_count=len(commands),
            limit=limit,
            filters=filters
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get command history: {str(e)}")


@router.get("/interactions", response_model=AssistantInteractionResponse)
async def get_assistant_interactions(
    assistant_type: Optional[str] = Query(None, description="Filter by assistant type"),
    request_type: Optional[str] = Query(None, description="Filter by request type"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of interactions to return")
) -> AssistantInteractionResponse:
    """Get assistant interaction history with optional filtering."""
    try:
        interactions = await history_service.get_assistant_interactions(
            assistant_type=assistant_type,
            request_type=request_type,
            session_id=session_id,
            limit=limit
        )
        
        filters = {}
        if assistant_type:
            filters["assistant_type"] = assistant_type
        if request_type:
            filters["request_type"] = request_type
        if session_id:
            filters["session_id"] = session_id
        
        return AssistantInteractionResponse(
            interactions=interactions,
            total_count=len(interactions),
            limit=limit,
            filters=filters
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assistant interactions: {str(e)}")


@router.get("/stats", response_model=HistoryStatsResponse)
async def get_history_stats() -> HistoryStatsResponse:
    """Get overall history statistics."""
    try:
        # This is a simplified implementation - in a real system, you'd have
        # dedicated statistics queries in the service
        
        # Get sample data to calculate basic stats
        chat_sample = await history_service.get_chat_history(limit=1000)
        command_sample = await history_service.get_command_history(limit=1000)
        interaction_sample = await history_service.get_assistant_interactions(limit=1000)
        
        # Extract unique rooms
        rooms = list(set(msg.get("room", "unknown") for msg in chat_sample))
        
        # Calculate date range from messages
        all_timestamps = [msg.get("timestamp") for msg in chat_sample if msg.get("timestamp")]
        date_range = {}
        if all_timestamps:
            min_ts = min(all_timestamps)
            max_ts = max(all_timestamps)
            date_range = {
                "earliest": datetime.fromtimestamp(min_ts, timezone.utc).isoformat(),
                "latest": datetime.fromtimestamp(max_ts, timezone.utc).isoformat()
            }
        
        return HistoryStatsResponse(
            total_messages=len(chat_sample),
            total_commands=len(command_sample),
            total_interactions=len(interaction_sample),
            rooms=rooms,
            date_range=date_range
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history stats: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_history(days_old: int = Query(30, ge=1, le=365)) -> Dict[str, Any]:
    """Clean up history records older than specified days."""
    try:
        deleted_counts = await history_service.cleanup_old_records(days_old=days_old)
        
        return {
            "status": "completed",
            "days_old": days_old,
            "deleted_records": deleted_counts,
            "total_deleted": sum(deleted_counts.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup history: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str,
    include_messages: bool = Query(True, description="Include chat messages"),
    include_commands: bool = Query(True, description="Include command history"),
    include_interactions: bool = Query(True, description="Include assistant interactions"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records per type")
) -> Dict[str, Any]:
    """Get comprehensive history for a specific session."""
    try:
        session_data = {
            "session_id": session_id,
            "stats": await history_service.get_session_stats(session_id)
        }
        
        if include_messages:
            room_name = f"session-{session_id}"
            session_data["messages"] = await history_service.get_chat_history(
                room=room_name,
                limit=limit
            )
        
        if include_commands:
            session_data["commands"] = await history_service.get_command_history(
                session_id=session_id,
                limit=limit
            )
        
        if include_interactions:
            session_data["interactions"] = await history_service.get_assistant_interactions(
                session_id=session_id,
                limit=limit
            )
        
        return session_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")