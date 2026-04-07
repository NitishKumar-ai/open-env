"""
Baseline inference script for Code Security Review OpenEnv.
Compliant with mandatory STDOUT format: [START], [STEP], [END].

Required environment variables:
    API_BASE_URL   — LLM API endpoint
    MODEL_NAME     — Model identifier
    HF_TOKEN       — Hugging Face / API key
    ENV_URL        — Running environment URL (default: http://localhost:7860)
"""

import os
import json
import time
import re
import requests
from typing import List, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load .env variables
load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN") or os.environ.get("API_KEY")
ENV_URL      = os.environ.get("ENV_URL",      "http://localhost:7860")
BENCHMARK    = "code-security-review"

if not HF_TOKEN:
    raise ValueError("HF_TOKEN or API_KEY must be set.")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

SYSTEM_PROMPT = """You are a senior security-focused code reviewer.

When given a code snippet, carefully analyse it for bugs and security issues.

Respond with ONLY a valid JSON object — no markdown, no explanation outside the JSON.

Schema:
{
  "bug_identified": true or false,
  "bug_location": "exact location (function name, line description, variable, expression)",
  "bug_type": "off-by-one | logic-error | security-vulnerability | none",
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
    url = f"{ENV_URL}{path}"
    resp = requests.post(url, json=data or {}, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_json_from_llm(text: str) -> dict:
    """Robustly extract JSON from LLM output."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # If the LLM still included text around the JSON, try to find the first { and last }
    match = re.search(r"({.*})", text, re.DOTALL)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except Exception:
        return {}


def build_prompt(obs: dict) -> str:
    lines = [
        f"Language: {obs['language']}",
        f"Context: {obs.get('context', 'No context provided')}",
        f"PR Title: {obs.get('pr_title', 'No PR title')}",
        f"File Path: {obs.get('file_path', 'unknown')}",
        "",
        f"```{obs['language']}",
        obs["code_snippet"],
        "```",
    ]
    return "\n".join(lines)


# ── Task runner ───────────────────────────────────────────────────────────────

def run_task(task_id: str, task_num: int) -> dict:
    reset_resp = env_post("/reset", params={"task_id": task_id})
    obs = reset_resp["observation"]
    
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    cumulative_reward = 0.0
    step_num = 0
    max_steps = 1 
    done = False
    all_rewards = []
    error = None

    while not done and step_num < max_steps:
        step_num += 1
        prompt = build_prompt(obs)
        action_dict = {}

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
                stream=False,
            )
            raw = response.choices[0].message.content
            action_dict = parse_json_from_llm(raw)
            action_str = json.dumps(action_dict)
            error = None
        except Exception as exc:
            error = str(exc).replace("\n", " ")
            action_dict = {
                "bug_identified": False,
                "bug_location": "none",
                "bug_type": "none",
                "bug_description": f"Error: {error}",
                "severity": "none",
                "suggested_fix": "none",
            }
            action_str = "{}"

        # ── Step env ──────────────────────────────────────────────────────────
        step_resp = env_post("/step", data=action_dict)
        reward = step_resp["reward"]
        done   = step_resp["done"]
        obs    = step_resp.get("observation")
        
        all_rewards.append(reward)
        cumulative_reward += reward
        
        log_step(step=step_num, action=action_str, reward=reward, done=done, error=error)

    success = cumulative_reward >= 0.8
    log_end(success=success, steps=step_num, score=cumulative_reward, rewards=all_rewards)

    return {
        "task_num":        task_num,
        "task_id":         task_id,
        "score":           cumulative_reward,
        "success":         success,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[INFO] Initializing inference on {BENCHMARK} using {MODEL_NAME}", flush=True)

    TASK_FILTER = os.environ.get("TASK")

    all_tasks = [
        ("python-off-by-one", 1, "easy"),
        ("js-auth-privilege", 2, "medium"),
        ("python-sql-injection", 3, "hard"),
    ]

    if TASK_FILTER:
        tasks = [t for t in all_tasks if t[2] == TASK_FILTER]
    else:
        tasks = all_tasks

    results = []

    for task_id, task_num, _ in tasks:
        try:
            r = run_task(task_id, task_num)
        except Exception as exc:
            print(f"[ERROR] task_id={task_id} error={exc}", flush=True)
            r = {"task_num": task_num, "task_id": task_id, "score": 0.0, "success": False}
        results.append(r)

    if results:
        avg = round(sum(r["score"] for r in results) / len(results), 3)
        successes = sum(1 for r in results if r.get("success"))
        print(f"\n[SUMMARY] avg_reward={avg} tasks_passed={successes}/{len(results)}", flush=True)

if __name__ == "__main__":
    main()
