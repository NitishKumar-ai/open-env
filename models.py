from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class CodeReviewAction(BaseModel):
    """Action taken by the agent: a structured code review."""
    bug_identified: bool = Field(..., description="Whether a bug was found")
    bug_location: str = Field(..., description="Location of the bug (function, line, variable)")
    bug_type: str = Field(..., description="Type: off-by-one | logic-error | security-vulnerability | none")
    bug_description: str = Field(..., description="Detailed explanation of why this is a bug")
    severity: str = Field(..., description="Severity: none | low | medium | high | critical")
    suggested_fix: str = Field(..., description="The corrected code or a description of how to fix it")


class CodeReviewObservation(BaseModel):
    """What the agent sees at each step."""
    code_snippet: str = Field(..., description="The code to review")
    language: str = Field(..., description="Programming language")
    task_description: str = Field(..., description="What the code is supposed to do")
    task_id: str = Field(..., description="Unique task identifier")
    difficulty: str = Field(..., description="easy | medium | hard")
    step_number: int = Field(..., description="Current step within this episode")
    max_steps: int = Field(..., description="Maximum steps allowed per episode")
    previous_feedback: Optional[str] = Field(None, description="Feedback from previous step if any")


class CodeReviewState(BaseModel):
    """Internal environment state."""
    task_id: str
    difficulty: str
    step_count: int
    done: bool
    total_reward: float
    task_complete: bool


class StepResponse(BaseModel):
    observation: CodeReviewObservation
    reward: float
    done: bool
    info: Dict[str, Any]


class ResetResponse(BaseModel):
    observation: CodeReviewObservation
