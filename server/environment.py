import random
from typing import Optional, Dict, Tuple

from server.tasks import TASKS
from server.grader import grade_action
from server.models import CodeObservation, StepResult, StateResponse, Action, Observation

class CodeSecurityEnv:
    def __init__(self):
        self.current_task: Optional[dict] = None
        self.step_count: int = 0
        self.done: bool = False
        self.total_reward: float = 0.0
        self._task_ids = list(TASKS.keys())

    def reset(self, task_id: Optional[str] = None, seed: Optional[int] = None) -> Observation:
        if seed is not None:
            random.seed(seed)
        
        if task_id and task_id in TASKS:
            self.current_task = TASKS[task_id]
        else:
            # Pick a task by its ID
            chosen_id = random.choice(self._task_ids)
            self.current_task = TASKS[chosen_id]

        self.step_count = 0
        self.done = False
        self.total_reward = 0.0

        return self._make_observation()

    def step(self, action: Action) -> StepResult:
        if self.current_task is None:
            # Auto-reset if called before reset()
            self.reset()

        if self.done:
            return StepResult(
                observation=self._make_observation(),
                reward=0.0,
                done=True,
                info={"error": "Episode already completed. Call /reset to start a new episode."},
            )

        # The action comes from the API as a Pydantic model (Action)
        # The grader expects a dict or the model itself.
        reward, breakdown = grade_action(action.model_dump(), self.current_task)

        self.step_count += 1
        self.total_reward += reward
        self.done = True  # single-step environment — one action per episode

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
        current_id = self.current_task["id"] if self.current_task else ""
        return StateResponse(
            task_id=current_id,
            step=self.step_count,
            done=self.done,
            total_reward=self.total_reward,
        )

    def _make_observation(self) -> Observation:
        t = self.current_task
        return Observation(
            task_id=t["id"],
            language=t["language"],
            difficulty=t["difficulty"],
            code_snippet=t["code_snippet"],
            context=t["context"],
            pr_title=t["pr_title"],
            file_path=t["file_path"],
        )
