import os
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
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
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "project": "Code Security Review - OpenEnv",
        "version": "1.0.0",
        "organization": "Inmodel Labs",
    }


@app.get("/tasks", response_model=List[TaskInfo])
def list_tasks():
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
):
    """Reset the environment and return the first observation."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    obs = env.reset(task_id=task_id, seed=seed)
    return ResetResponse(observation=obs)


@app.post("/step", response_model=StepResult)
def step(action: CodeReviewAction):
    """Submit a code review action and receive a reward signal."""
    result = env.step(action)
    return result


@app.get("/state", response_model=StateResponse)
def state():
    """Return the current environment state."""
    return env.state()


def main():
    """Run the environment server."""
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
