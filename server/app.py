"""Main FastAPI application for Code Security Review.

Exposes RESTful endpoints conforming to standard OpenEnv compliance specifications 
dictating interactions for agent evaluation.
"""

import os
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from server.models import CodeReviewAction, StepResult, ResetResponse, StateResponse, TaskInfo
from server.tasks import TASKS
from server.environment import CodeSecurityEnv

app = FastAPI(
    title="Code Security Review — OpenEnv",
    description="An RL environment for training AI agents to perform code security review.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CodeSecurityEnv()


@app.get("/")
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "project": "Code Security Review - OpenEnv",
        "version": "1.0.0",
        "organization": "Inmodel Labs",
    }


@app.get("/tasks", response_model=List[TaskInfo])
def list_tasks() -> List[TaskInfo]:
    """List all available tasks."""
    return [
        TaskInfo(
            id=t["id"],
            language=t["language"],
            bug_class=t["bug_class"],
            difficulty=t["difficulty"],
        )
        for t in TASKS.values()
    ]


@app.post("/reset", response_model=ResetResponse)
def reset(
    task_id: str = Query(default="python-off-by-one", description="Task ID to reset to"),
    seed: Optional[int] = Query(default=None, description="Optional seed for reproducibility")
) -> ResetResponse:
    """Reset the environment and return the first observation."""
    if task_id not in TASKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task '{task_id}' not found."
        )
    
    try:
        obs = env.reset(task_id=task_id, seed=seed)
        return ResetResponse(observation=obs)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System breakdown during environment reset: {e}"
        )


@app.post("/step", response_model=StepResult)
def step(action: CodeReviewAction) -> StepResult:
    """Submit a code review action and receive a reward signal."""
    try:
        return env.step(action)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing agent action logic: {e}"
        )


@app.get("/state", response_model=StateResponse)
def state() -> StateResponse:
    """Return the current environment state."""
    try:
        return env.state()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing global runtime state tracking: {e}"
        )


def main() -> None:
    """Run the environment ASGI server natively."""
    port_default = os.environ.get("PORT", "8000")
    try:
         port = int(port_default)
    except ValueError:
         port = 8000

    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
