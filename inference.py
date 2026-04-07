"""
Baseline inference script for Code Security Review OpenEnv.
Compliant with mandatory STDOUT format: [START], [STEP], [END].

Required environment variables:
    API_BASE_URL   — LLM API endpoint
    MODEL_NAME     — Model identifier
    HF_TOKEN       — Hugging Face / API key
    ENV_BASE_URL   — Running environment URL (default: http://localhost:7860)
"""

import os
import json
import time
import re
from typing import List, Optional
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

import requests
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK    = "code-review-env"

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

SYSTEM_PROMPT = """You are a senior security-focused code reviewer.

When given a code snippet, carefully analyse it for bugs and security issues.

Respond with ONLY a valid JSON object — no markdown, no explanation outside the JSON.

Schema:
{
  "bug_identified": true or false,
  "bug_location": "exact location (function name, line description, variable, expression)",
  "bug_type": "off-by-one | logic-error | security-vulnerability | null-dereference | none",
  "bug_description": "detailed explanation of why this is a bug and the impact",
  "severity": "none | low | medium | high | critical",
  "suggested_fix": "the corrected code snippet or a precise description of the fix"
}"""

# ── Logging Helpers ───────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def env_post(path: str, data: Optional[dict] = None, params: Optional[dict] = None) -> dict:
    url = f"{ENV_BASE_URL}{path}"
    resp = requests.post(url, json=data or {}, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_json_from_llm(text: str) -> dict:
    """Robustly extract JSON from LLM output."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def build_prompt(obs: dict) -> str:
    lines = [
        f"Language: {obs['language']}",
        f"Task: {obs['task_description']}",
        "",
        f"```{obs['language']}",
        obs["code_snippet"],
        "```",
    ]
    if obs.get("previous_feedback"):
        lines += ["", f"Previous feedback: {obs['previous_feedback']}",
                  "Revise your analysis accordingly."]
    return "\n".join(lines)


# ── Task runner ───────────────────────────────────────────────────────────────

def run_task(difficulty: str) -> dict:
    reset_resp = env_post("/reset", params={"difficulty": difficulty})
    obs = reset_resp["observation"]
    task_id = obs['task_id']

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    rewards = []
    steps_taken = 0
    done = False
    last_error = None

    while not done and steps_taken < obs["max_steps"]:
        steps_taken += 1
        prompt = build_prompt(obs)

        # ── LLM call ──────────────────────────────────────────────────────────
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.1,
                max_tokens=600,
            )
            raw = response.choices[0].message.content
            action_dict = parse_json_from_llm(raw)
            action_str = json.dumps(action_dict)
            last_error = None
        except Exception as exc:
            last_error = str(exc)
            action_dict = {
                "bug_identified": False,
                "bug_location": "error",
                "bug_type": "none",
                "bug_description": last_error,
                "severity": "none",
                "suggested_fix": "",
            }
            action_str = "{}"

        # ── Step env ──────────────────────────────────────────────────────────
        step_resp = env_post("/step", data=action_dict)
        reward = step_resp["reward"]
        done   = step_resp["done"]
        obs    = step_resp["observation"]
        
        rewards.append(reward)
        log_step(step=steps_taken, action=action_str, reward=reward, done=done, error=last_error)

    # Calculate final score (normalized to [0, 1])
    # Total reward is cumulative in this env, but we cap it at 1.0 for the score
    total_reward = sum(rewards)
    score = min(max(total_reward, 0.0), 1.0)
    success = score >= 0.8

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    
    return {
        "task_id": task_id,
        "score": score,
        "success": success
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    tasks = ["easy", "medium", "hard"]
    results = []

    for difficulty in tasks:
        try:
            r = run_task(difficulty)
            results.append(r)
        except Exception as exc:
            # print(f"DEBUG: Task failed: {exc}", flush=True)
            log_end(success=False, steps=0, score=0.0, rewards=[])

    if results:
        avg = sum(r["score"] for r in results) / len(results)
        # Optional: summary for human review (will not interfere with [END] parsers)
        # print(f"\n[SUMMARY] avg_score={avg:.3f}")

if __name__ == "__main__":
    main()
