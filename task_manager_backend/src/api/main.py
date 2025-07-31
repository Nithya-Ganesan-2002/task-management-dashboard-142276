"""
FastAPI main app for Task Management Backend.

Implements:
- User signup & login (Supabase Auth REST)
- Task CRUD endpoints (Supabase table storage)
- OpenAPI docs, CORS

Env vars required:
- SUPABASE_URL (supabase project url)
- SUPABASE_KEY (service role api key)
"""

from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
import requests

from .models import (
    UserSignupRequest, UserLoginRequest, UserResponse,
    TaskCreateRequest, TaskUpdateRequest, TaskResponse
)
from .supabase_client import get_supabase_client

import os

app = FastAPI(
    title="Task Manager API",
    description="RESTful API to manage users and tasks with Supabase backend.",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "User signup and login"},
        {"name": "tasks", "description": "CRUD operations for user tasks"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod, restrict allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", SUPABASE_KEY)
SUPABASE_AUTH_BASE = f"{SUPABASE_URL}/auth/v1"


# --- Auth/JWT Dependency ---

# Using HTTPBearer for Authorization: Bearer {jwt}
bearer_scheme = HTTPBearer()

# PUBLIC_INTERFACE
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Dependency for extracting current user from JWT Bearer token using Supabase.

    Raises 401 if invalid.
    """
    token = credentials.credentials
    # Validate token with Supabase (using /user endpoint)
    resp = requests.get(
        f"{SUPABASE_AUTH_BASE}/user",
        headers={"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {token}"}
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user = resp.json()
    if not user or not user.get("id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

# --- ROUTES ---

@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

# ------- AUTH ROUTES --------

@app.post("/signup", response_model=UserResponse, status_code=201, tags=["auth"])
def signup(payload: UserSignupRequest, request: Request):
    """
    Signup a new user via Supabase Auth.

    - **email**: User's email
    - **password**: User's password

    Returns user profile and token if successful.

    ---
    """
    # signup endpoint per https://supabase.com/docs/reference/auth/sign-up
    resp = requests.post(
        f"{SUPABASE_AUTH_BASE}/signup",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={
            "email": payload.email,
            "password": payload.password,
            "data": {},
            "redirect_to": os.environ.get("SITE_URL")
        }
    )
    if resp.status_code >= 400:
        return JSONResponse(status_code=400, content={"detail": resp.json().get("msg", "Signup failed")})
    data = resp.json()
    user = data.get("user") or data
    session = data.get("session") or data
    return UserResponse(
        user_id=user.get("id"),
        email=user.get("email"),
        access_token=session.get("access_token", "")  # return access token if already confirmed
    )

@app.post("/login", response_model=UserResponse, tags=["auth"])
def login(payload: UserLoginRequest):
    """
    Login a user via Supabase Auth.

    - **email**: User's email
    - **password**: User's password

    Returns user profile and access token.
    """
    resp = requests.post(
        f"{SUPABASE_AUTH_BASE}/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={
            "email": payload.email,
            "password": payload.password
        }
    )
    if resp.status_code >= 400:
        return JSONResponse(status_code=400, content={"detail": resp.json().get("msg", "Login failed")})
    data = resp.json()
    user = data.get("user")
    access_token = data.get("access_token")
    if not user or not access_token:
        raise HTTPException(status_code=400, detail="Invalid login response from Supabase")
    return UserResponse(
        user_id=user["id"],
        email=user["email"],
        access_token=access_token
    )

# ------- TASK ROUTES --------

@app.post("/tasks/", response_model=TaskResponse, status_code=201, tags=["tasks"])
def create_task(task: TaskCreateRequest, current_user: dict = Depends(get_current_user)):
    """
    Create a new task for the authenticated user.

    - **title**: Task title
    - **description**: Task details

    Returns created task.
    """
    client = get_supabase_client()
    # Insert into "tasks" table (schema: id, title, description, completed, user_id)
    resp = client.table("tasks").insert({
        "title": task.title,
        "description": task.description,
        "completed": False,
        "user_id": current_user["id"]
    }).execute()
    if resp.error:
        raise HTTPException(status_code=400, detail=resp.error.message)
    item = resp.data[0]
    return TaskResponse(
        id=item["id"],
        title=item["title"],
        description=item.get("description"),
        completed=item["completed"],
        user_id=item["user_id"],
        created_at=item["created_at"],
        updated_at=item["updated_at"]
    )

@app.get("/tasks/", response_model=List[TaskResponse], tags=["tasks"])
def list_tasks(current_user: dict = Depends(get_current_user)):
    """
    Get all tasks owned by the authenticated user.
    """
    client = get_supabase_client()
    resp = client.table("tasks").select("*").eq("user_id", current_user["id"]).order("created_at", desc=False).execute()
    if resp.error:
        raise HTTPException(status_code=400, detail=resp.error.message)
    return [TaskResponse(
        id=item["id"],
        title=item["title"],
        description=item.get("description"),
        completed=item["completed"],
        user_id=item["user_id"],
        created_at=item["created_at"],
        updated_at=item["updated_at"]
    ) for item in resp.data]

@app.get("/tasks/{task_id}/", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """
    Fetch details of a specific task by its ID (must belong to user).
    """
    client = get_supabase_client()
    resp = client.table("tasks").select("*").eq("id", task_id).eq("user_id", current_user["id"]).single().execute()
    if resp.error or not resp.data:
        raise HTTPException(status_code=404, detail="Task not found")
    item = resp.data
    return TaskResponse(
        id=item["id"],
        title=item["title"],
        description=item.get("description"),
        completed=item["completed"],
        user_id=item["user_id"],
        created_at=item["created_at"],
        updated_at=item["updated_at"]
    )

@app.put("/tasks/{task_id}/", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: int, task: TaskUpdateRequest, current_user: dict = Depends(get_current_user)):
    """
    Update a task's fields (patch) for the authenticated user.
    """
    client = get_supabase_client()
    update_dict = {k: v for k, v in task.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No update fields provided")
    resp = client.table("tasks").update(update_dict).eq("id", task_id).eq("user_id", current_user["id"]).execute()
    if resp.error or not resp.data:
        raise HTTPException(status_code=404, detail="Task not found or update failed")
    item = resp.data[0]
    return TaskResponse(
        id=item["id"],
        title=item["title"],
        description=item.get("description"),
        completed=item["completed"],
        user_id=item["user_id"],
        created_at=item["created_at"],
        updated_at=item["updated_at"]
    )

@app.delete("/tasks/{task_id}/", status_code=204, tags=["tasks"])
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a task (must belong to user).
    """
    client = get_supabase_client()
    resp = client.table("tasks").delete().eq("id", task_id).eq("user_id", current_user["id"]).execute()
    if resp.error:
        raise HTTPException(status_code=404, detail=resp.error.message)
    return JSONResponse(status_code=204, content=None)

@app.patch("/tasks/{task_id}/complete/", response_model=TaskResponse, tags=["tasks"])
def mark_task_complete(task_id: int, completed: bool = True, current_user: dict = Depends(get_current_user)):
    """
    Mark task as complete/incomplete.
    """
    client = get_supabase_client()
    resp = client.table("tasks").update({"completed": completed}).eq("id", task_id).eq("user_id", current_user["id"]).execute()
    if resp.error or not resp.data:
        raise HTTPException(status_code=404, detail="Task not found or update failed")
    item = resp.data[0]
    return TaskResponse(
        id=item["id"],
        title=item["title"],
        description=item.get("description"),
        completed=item["completed"],
        user_id=item["user_id"],
        created_at=item["created_at"],
        updated_at=item["updated_at"]
    )
