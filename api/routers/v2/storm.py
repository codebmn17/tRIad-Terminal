"""
Storm Integration API

FastAPI endpoints for Storm-based multi-agent coordination and task distribution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from triad.services import StormIntegrationService
from triad.services.storm_integration import TaskStatus, MessageType


router = APIRouter(prefix="/storm", tags=["Storm Integration"])

# Service instance (in production, this would be managed as a singleton)
storm_service = StormIntegrationService()


class TaskSubmissionRequest(BaseModel):
    """Request to submit a new distributed task."""
    task_type: str = Field(..., description="Type of task")
    description: str = Field(..., description="Human-readable task description")
    payload: Dict[str, Any] = Field(..., description="Task payload data")
    required_capabilities: List[str] = Field(default_factory=list, description="Required agent capabilities")
    priority: int = Field(default=1, ge=1, le=10, description="Task priority (1-10)")
    timeout_seconds: int = Field(default=300, ge=30, le=3600, description="Task timeout in seconds")


class TaskSubmissionResponse(BaseModel):
    """Response for task submission."""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response for task status query."""
    task_id: str
    type: str
    description: str
    status: str
    assigned_agent: Optional[str]
    created_at: float
    priority: int
    timeout_seconds: int
    result: Any = None
    error: Optional[str] = None


class CoordinationSessionRequest(BaseModel):
    """Request to create a coordination session."""
    session_id: str = Field(..., description="Unique session identifier")
    participating_agents: List[str] = Field(..., description="List of participating agent IDs")
    coordination_goal: str = Field(..., description="Goal of the coordination session")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session context")


class BroadcastMessageRequest(BaseModel):
    """Request to broadcast a message to all agents."""
    message_type: str = Field(..., description="Type of message")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    sender: str = Field(default="api", description="Message sender")


class SystemStatusResponse(BaseModel):
    """Response for system status."""
    connected_agents: int
    registered_capabilities: int
    active_tasks: int
    tasks_by_status: Dict[str, int]
    running: bool
    websocket_port: int


class AgentInfoResponse(BaseModel):
    """Response for agent information."""
    agent_id: str
    capabilities: List[str]
    load_factor: float
    last_heartbeat: float
    connected: bool
    heartbeat_age: float


async def ensure_storm_service_running():
    """Ensure Storm service is running."""
    if not storm_service.running:
        await storm_service.start()


@router.on_event("startup")
async def startup_storm_service():
    """Start Storm service on API startup."""
    await ensure_storm_service_running()


@router.on_event("shutdown")
async def shutdown_storm_service():
    """Stop Storm service on API shutdown."""
    await storm_service.stop()


@router.post("/tasks", response_model=TaskSubmissionResponse)
async def submit_task(request: TaskSubmissionRequest) -> TaskSubmissionResponse:
    """Submit a new distributed task for execution."""
    try:
        await ensure_storm_service_running()
        
        task_id = await storm_service.submit_task(
            task_type=request.task_type,
            description=request.description,
            payload=request.payload,
            required_capabilities=request.required_capabilities,
            priority=request.priority,
            timeout_seconds=request.timeout_seconds
        )
        
        return TaskSubmissionResponse(
            task_id=task_id,
            status="submitted",
            message="Task submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get the current status of a submitted task."""
    try:
        await ensure_storm_service_running()
        
        task = await storm_service.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStatusResponse(
            task_id=task.id,
            type=task.type,
            description=task.description,
            status=task.status.value,
            assigned_agent=task.assigned_agent,
            created_at=task.created_at,
            priority=task.priority,
            timeout_seconds=task.timeout_seconds,
            result=task.result,
            error=task.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str) -> Dict[str, str]:
    """Cancel a submitted task."""
    try:
        await ensure_storm_service_running()
        
        success = await storm_service.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
        
        return {
            "status": "cancelled",
            "task_id": task_id,
            "message": "Task cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/coordination", response_model=Dict[str, Any])
async def create_coordination_session(request: CoordinationSessionRequest) -> Dict[str, Any]:
    """Create a multi-agent coordination session."""
    try:
        await ensure_storm_service_running()
        
        result = await storm_service.create_coordination_session(
            session_id=request.session_id,
            participating_agents=request.participating_agents,
            coordination_goal=request.coordination_goal,
            context=request.context
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create coordination session: {str(e)}")


@router.post("/broadcast")
async def broadcast_message(request: BroadcastMessageRequest) -> Dict[str, str]:
    """Broadcast a message to all connected agents."""
    try:
        await ensure_storm_service_running()
        
        # Convert string message type to enum
        try:
            message_type = MessageType(request.message_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid message type: {request.message_type}")
        
        await storm_service.broadcast_message(
            message_type=message_type,
            payload=request.payload,
            sender=request.sender
        )
        
        return {
            "status": "broadcast",
            "message": "Message broadcast to all connected agents"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast message: {str(e)}")


@router.get("/agents", response_model=List[AgentInfoResponse])
async def get_connected_agents() -> List[AgentInfoResponse]:
    """Get list of currently connected agents."""
    try:
        await ensure_storm_service_running()
        
        agents = await storm_service.get_connected_agents()
        
        return [AgentInfoResponse(**agent) for agent in agents]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connected agents: {str(e)}")


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """Get overall Storm integration system status."""
    try:
        await ensure_storm_service_running()
        
        status = await storm_service.get_system_status()
        
        return SystemStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.post("/start")
async def start_storm_service() -> Dict[str, str]:
    """Manually start the Storm integration service."""
    try:
        if storm_service.running:
            return {
                "status": "already_running",
                "message": "Storm service is already running"
            }
        
        await storm_service.start()
        
        return {
            "status": "started",
            "message": "Storm service started successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Storm service: {str(e)}")


@router.post("/stop")
async def stop_storm_service() -> Dict[str, str]:
    """Manually stop the Storm integration service."""
    try:
        if not storm_service.running:
            return {
                "status": "already_stopped",
                "message": "Storm service is not running"
            }
        
        await storm_service.stop()
        
        return {
            "status": "stopped",
            "message": "Storm service stopped successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop Storm service: {str(e)}")


@router.get("/tasks")
async def list_active_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tasks to return")
) -> Dict[str, Any]:
    """List active tasks with optional filtering."""
    try:
        await ensure_storm_service_running()
        
        # Get all active tasks (simplified implementation)
        all_tasks = []
        for task_id, task in storm_service.active_tasks.items():
            task_info = {
                "task_id": task.id,
                "type": task.type,
                "description": task.description,
                "status": task.status.value,
                "assigned_agent": task.assigned_agent,
                "created_at": task.created_at,
                "priority": task.priority
            }
            
            # Apply filters
            if status and task.status.value != status:
                continue
            if task_type and task.type != task_type:
                continue
            
            all_tasks.append(task_info)
        
        # Sort by priority and creation time
        all_tasks.sort(key=lambda t: (-t["priority"], t["created_at"]))
        
        # Apply limit
        limited_tasks = all_tasks[:limit]
        
        return {
            "tasks": limited_tasks,
            "total_count": len(all_tasks),
            "returned_count": len(limited_tasks),
            "filters": {
                "status": status,
                "task_type": task_type
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")