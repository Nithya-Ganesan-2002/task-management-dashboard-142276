"""
Pydantic models for User authentication and Task management APIs.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# PUBLIC_INTERFACE
class UserSignupRequest(BaseModel):
    """Schema for submitting user signup information."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (minimum 6 chars)")

# PUBLIC_INTERFACE
class UserLoginRequest(BaseModel):
    """Schema for submitting user login credentials."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

# PUBLIC_INTERFACE
class UserResponse(BaseModel):
    """Schema for returning authenticated user info."""
    user_id: str = Field(..., description="Unique identifier for the user")
    email: EmailStr = Field(..., description="User email address")
    access_token: str = Field(..., description="JWT access token for the session")

# PUBLIC_INTERFACE
class TaskBase(BaseModel):
    """Base model for a task (shared fields)."""
    title: str = Field(..., min_length=1, max_length=128, description="Task title")
    description: Optional[str] = Field(None, max_length=4096, description="Optional task description")

# PUBLIC_INTERFACE
class TaskCreateRequest(TaskBase):
    """Schema for creating a new task."""

# PUBLIC_INTERFACE
class TaskUpdateRequest(BaseModel):
    """Schema for updating a task (partial fields allowed)."""
    title: Optional[str] = Field(None, min_length=1, max_length=128, description="New title for the task")
    description: Optional[str] = Field(None, max_length=4096, description="New description for the task")
    completed: Optional[bool] = Field(None, description="Update completion status")

# PUBLIC_INTERFACE
class TaskResponse(TaskBase):
    """Response schema for a task."""
    id: int = Field(..., description="Task unique identifier")
    user_id: str = Field(..., description="Owner (user) ID")
    completed: bool = Field(..., description="Completion status")
    created_at: str = Field(..., description="ISO timestamp (created)")
    updated_at: str = Field(..., description="ISO timestamp (last updated)")
