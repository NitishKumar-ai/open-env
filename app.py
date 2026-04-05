import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import CodeReviewAction, CodeReviewState, StepResponse, ResetResponse
from .environment import CodeReviewEnvironment

app = FastAPI(
    title="Code Security Review — OpenEnv",
    description=(
        "RL environment for training AI agents to detect bugs and security "
        "vulnerabilities in code. Compatible with the OpenEnv spec."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CodeReviewEnvironment()


@app.get("/health")
def health():
    return {"status": "ok", "env": "code-review-env", "version": "1.0.0"}


@app.post("/reset", response_model=ResetResponse)
def reset(difficulty: str = Query(default="easy", description="easy | medium | hard")):
    """Reset the environment and return the first observation."""
    obs = env.reset(difficulty=difficulty)
    return ResetResponse(observation=obs)


@app.post("/step", response_model=StepResponse)
def step(action: CodeReviewAction):
    """Submit a code review action and receive a reward signal."""
    try:
        obs, reward, done, info = env.step(action)
        return StepResponse(observation=obs, reward=reward, done=done, info=info)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/state", response_model=CodeReviewState)
def state():
    """Return the current environment state."""
    return env.state()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    enable_web = os.environ.get("ENABLE_WEB_INTERFACE", "false").lower() == "true"
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
