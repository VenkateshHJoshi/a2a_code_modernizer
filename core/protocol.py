from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class AgentRole(str, Enum):
    ARCHITECT = "architect"
    BUILDER = "builder"
    QA = "qa"
    LIBRARIAN = "librarian"
    MANAGER = "manager"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

# Standardized Output for every Agent
class AgentResponse(BaseModel):
    role: AgentRole
    status: TaskStatus
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # If an agent fails, it must populate this field so the Manager can self-heal
    error_message: Optional[str] = None
    raw_content: Optional[str] = None # The actual text/code generated

    class Config:
        use_enum_values = True

# The Internal Message Packet passed between agents
class AgentMessage(BaseModel):
    sender: AgentRole
    recipient: AgentRole
    payload: Dict[str, Any]
    context_id: str