"""Pydantic v2 models representing actions, observations, and state payloads."""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

# ── Agent Action ──────────────────────────────────────────────────────────────

class CodeReviewAction(BaseModel):
    """Action taken by the agent: a structured code review."""
    
    bug_identified: bool = Field(..., description="Whether a bug was found")
    bug_location: str = Field(..., description="Location of the bug (function, line, variable)")
    bug_type: str = Field(..., description="Type: off-by-one | logic-error | security-vulnerability | none")
    bug_description: str = Field(..., description="Detailed explanation of why this is a bug")
    severity: str = Field(..., description="Severity: none | low | medium | high | critical")
    suggested_fix: str = Field(..., description="The corrected code or a description of how to fix it")

# ── Observation ───────────────────────────────────────────────────────────────

class CodeObservation(BaseModel):
    """What the agent sees at each step."""
    
    task_id: str = Field(..., description="Unique task identifier")
    language: str = Field(..., description="Programming language")
    difficulty: str = Field(..., description="Level: easy | medium | hard")
    code_snippet: str = Field(..., description="The code to review")
    context: str = Field(..., description="Production context describing what the code does")
    pr_title: str = Field(..., description="Pull request title submitted by developer")
    file_path: str = Field(..., description="File path of the code in the repository")

# ── Step Result ───────────────────────────────────────────────────────────────

class StepResult(BaseModel):
    """Result returned from env.step()."""
    
    observation: Optional[CodeObservation] = Field(None, description="Observation if not terminal")
    reward: float = Field(..., description="Reward generated for the preceding action")
    done: bool = Field(..., description="Terminal state flag")
    info: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")

# ── State ─────────────────────────────────────────────────────────────────────

class StateResponse(BaseModel):
    """Internal environment state exposed via /state."""
    
    task_id: str = Field(..., description="Current running task")
    step: int = Field(..., description="Current evaluation step")
    done: bool = Field(..., description="Whether the episode resides in a terminal state")
    total_reward: float = Field(..., description="Sum of step rewards over the episode")

# ── API Helpers ───────────────────────────────────────────────────────────────

class ResetResponse(BaseModel):
    """Response wrapper returned strictly on environment resets."""
    
    observation: CodeObservation = Field(..., description="Initial environment observation upon reset")

class TaskInfo(BaseModel):
    """Metadata regarding an available task scenario."""
    
    id: str = Field(..., description="Task UUID or unique string identifier")
    language: str = Field(..., description="Source code language for the flaw context")
    bug_class: str = Field(..., description="The classification parameter of the embedded bug")
    difficulty: str = Field(..., description="The difficulty tier indicator (e.g. easy, medium)")

Action = CodeReviewAction
Observation = CodeObservation
Reward = float
