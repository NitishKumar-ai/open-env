from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


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
    observation: Optional[CodeObservation] = None
    reward: float
    done: bool
    info: Dict[str, Any]


# ── State ─────────────────────────────────────────────────────────────────────

class StateResponse(BaseModel):
    """Internal environment state exposed via /state."""
    task_id: str
    step: int
    done: bool
    total_reward: float


# ── API Helpers ───────────────────────────────────────────────────────────────

class ResetResponse(BaseModel):
    observation: CodeObservation


class TaskInfo(BaseModel):
    id: str
    language: str
    bug_class: str
    difficulty: str

Action = CodeReviewAction
Observation = CodeObservation
Reward = float
