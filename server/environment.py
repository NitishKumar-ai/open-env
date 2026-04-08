"""Reinforcement Learning Environment Core.

Defines the environment logic, maintaining the current trajectory
state and mediating between incoming requests and the headless grader.
"""

import random
from typing import Optional, Dict, Any

from server.tasks import TASKS
from server.grader import grade_action
from server.models import StepResult, StateResponse, Action, Observation

ERROR_EPISODE_COMPLETED = "Episode already completed. Call /reset to start a new episode."


class CodeSecurityEnv:
    """Simulates the stateful progression of a software security assessment."""

    def __init__(self) -> None:
        """Initialize a fresh environment instance."""
        self.current_task: Optional[Dict[str, Any]] = None
        self.step_count: int = 0
        self.done: bool = False
        self.total_reward: float = 0.0
        self._task_ids = list(TASKS.keys())

    def reset(self, task_id: Optional[str] = None, seed: Optional[int] = None) -> Observation:
        """Reset the environment safely to a new or targeted initial state.
        
        Args:
            task_id: Optionally force the environment to yield a specific task definition.
            seed: Initialize standard random seed.
            
        Returns:
            An Observation baseline reflecting the new scenario context.
        """
        if seed is not None:
            random.seed(seed)
        
        if task_id and task_id in TASKS:
            self.current_task = TASKS[task_id]
        else:
            chosen_id = random.choice(self._task_ids)
            self.current_task = TASKS[chosen_id]

        self.step_count = 0
        self.done = False
        self.total_reward = 0.0

        return self._make_observation()

    def step(self, action: Action) -> StepResult:
        """Advance the environment state using a provided agent Action payload.
        
        Args:
            action: Evaluated metrics provided directly by agent decision matrices.
            
        Returns:
            A StepResult containing scalar reward metrics and end-of-episode flag.
        """
        if self.current_task is None:
            self.reset()

        if self.done:
            return StepResult(
                observation=self._make_observation(),
                reward=0.0,
                done=True,
                info={"error": ERROR_EPISODE_COMPLETED},
            )

        # Intermediate Step: Request file
        if getattr(action, "request_file", False):
            self.step_count += 1
            reward = 0.20
            self.total_reward += reward
            self.done = False
            return StepResult(
                observation=self._make_observation(),
                reward=reward,
                done=self.done,
                info={
                    "task_name": getattr(self.current_task, "get", dict().get)("name", "Unknown Task") if self.current_task else "Unknown Task",
                    "step_count": self.step_count
                },
            )

        try:
            reward, breakdown = grade_action(action.model_dump(), self.current_task)
        except Exception as e:
            reward, breakdown = 0.0, {"error": f"Evaluation error: {e}"}

        self.step_count += 1
        self.total_reward += reward
        self.done = True  # single-step environment becomes max 2-step

        return StepResult(
            observation=self._make_observation(),
            reward=reward,
            done=self.done,
            info={
                "reward_breakdown": breakdown,
                "task_name": self.current_task.get("name", "Unknown Task"),
                "step_count": self.step_count
            },
        )

    def state(self) -> StateResponse:
        """Return global analytics tracking the current environment session state."""
        current_id = self.current_task["id"] if getattr(self, "current_task", None) else ""
        return StateResponse(
            task_id=current_id,
            step=self.step_count,
            done=self.done,
            total_reward=self.total_reward,
        )

    def _make_observation(self) -> Observation:
        """Construct the contextual parameters surrounding an ongoing assessment."""
        t = self.current_task
        if not t:
            raise KeyError("Attempted observation render without an initialized active task")
        
        # Hide the snippet before Step 1
        snippet = t["code_snippet"] if self.step_count > 0 else "<FILE CONTENTS HIDDEN - Submit {\"request_file\": true} to view>"
        
        return Observation(
            task_id=t["id"],
            language=t["language"],
            difficulty=t["difficulty"],
            code_snippet=snippet,
            context=t["context"],
            pr_title=t["pr_title"],
            file_path=t["file_path"],
        )
