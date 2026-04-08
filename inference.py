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
API_BASE_URL = os.environ.get("API_BASE_URL") or "https://api.openai.com/v1"
MODEL_NAME   = os.environ.get("MODEL_NAME") or "gpt-4o-mini"
API_KEY      = os.environ.get("API_KEY") or os.environ.get("HF_TOKEN")
ENV_URL      = os.environ.get("ENV_URL") or "http://localhost:7860"
BENCHMARK    = "code-security-review"

SYSTEM_PROMPT = """You are a senior security-focused code reviewer.

You are interacting with a multi-step environment. At first, the code snippet will be HIDDEN.
To request the file contents, you must output EXACTLY this JSON (no other text):
{"request_file": true}

Once you have requested the file and read the code snippet, carefully analyse it for bugs and security issues.
To submit your final review, respond with ONLY a valid JSON object matching this schema (no code blocks, no prose):
{
  "bug_identified": true or false,
  "bug_location": "exact location (function name, line description, variable, expression)",
  "bug_type": "off-by-one | logic-error | security-vulnerability | none",
  "bug_description": "detailed explanation of why this is a bug and the impact",
  "severity": "none | low | medium | high | critical",
  "suggested_fix": "description of fix (do NOT include code blocks inside this string)"
}

IMPORTANT: Your entire response must be parseable JSON. Do not wrap in markdown fences. Do not add any text outside the JSON object."""

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
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def env_post(path: str, data: Optional[dict] = None, params: Optional[dict] = None) -> dict:
    url = f"{ENV_URL}{path}"
    resp = requests.post(url, json=data or {}, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_json_from_llm(text: str) -> dict:
    """Robustly extract JSON from LLM output.
    
    Strategy: strip markdown fences, then try to find the LAST top-level
    JSON object in the text (after the LLM has potentially emitted code examples).
    """
    text = text.strip()
    # Strip ```json ... ``` and ``` ... ``` fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    # Find all top-level {...} objects in the text
    candidates = re.findall(r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", text, re.DOTALL)
    # Prefer the LAST candidate that is valid JSON (the review JSON, not a code example)
    for candidate in reversed(candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    # Final fallback: try the whole stripped text
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

def run_task(task_id: str, task_num: int, client=None) -> dict:
    cumulative_reward = 0.0
    step_num = 0
    done = False
    all_rewards = []
    success = False

    try:
        log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
        reset_resp = env_post("/reset", params={"task_id": task_id})
        obs = reset_resp["observation"]

        max_steps = 2
        error = None
        file_requested = False
        messages = []  # conversation history for LLM

        while not done and step_num < max_steps:
            step_num += 1
            prompt = build_prompt(obs)
            action_dict = {}

            # ── LLM call ──────────────────────────────────────────────────────────
            try:
                if client is None:
                    raise ValueError("OpenAI client was not initialized. Proxy evaluation cannot proceed.")
                else:
                    # Multi-turn: build conversation history
                    if not messages:
                        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                    messages.append({"role": "user", "content": prompt})

                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        temperature=0.1,
                        max_tokens=600,
                        stream=False,
                    )
                    raw = response.choices[0].message.content
                    # Add assistant reply to history for next turn
                    messages.append({"role": "assistant", "content": raw})

                    action_dict = parse_json_from_llm(raw)
                    action_str = json.dumps(action_dict)
                    error = None
            except Exception as exc:
                error = str(exc).replace("\n", " ")
                print(f"\n[CRITICAL ERROR] LLM CALL FAILED: {error}\n", flush=True)
                raise exc  # Fail fast to see the real error instead of silently falling back

            # ── Step env ──────────────────────────────────────────────────────────
            step_resp = env_post("/step", data=action_dict)
            reward = step_resp["reward"]
            done   = step_resp["done"]
            obs    = step_resp.get("observation")

            all_rewards.append(reward)
            cumulative_reward += reward

            log_step(step=step_num, action=action_str, reward=reward, done=done, error=error)

        success = cumulative_reward >= 0.8
    except Exception as exc:
        print(f"[ERROR] Exception during run_task: {exc}", flush=True)
    finally:
        clamped_score = round(min(1.0, max(0.0, cumulative_reward)), 3)
        log_end(success=success, steps=step_num, score=clamped_score, rewards=all_rewards)

    return {
        "task_num":        task_num,
        "task_id":         task_id,
        "score":           cumulative_reward,
        "success":         success,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[INFO] Initializing inference on {BENCHMARK} using {MODEL_NAME}", flush=True)

    client = None
    try:
        client = OpenAI(base_url=os.environ["API_BASE_URL"], api_key=os.environ["API_KEY"])
    except Exception as exc:
        print(f"[WARN] Client init failed: {exc}", flush=True)

    TASK_FILTER = os.environ.get("TASK")

    all_tasks = [
        ("python-off-by-one", 1, "easy"),
        ("js-idor-auth", 2, "medium"),
        ("python-pickle-deserialization", 3, "hard"),
    ]

    if TASK_FILTER:
        tasks = [t for t in all_tasks if t[2] == TASK_FILTER]
    else:
        tasks = all_tasks

    results = []

    for task_id, task_num, _ in tasks:
        try:
            r = run_task(task_id, task_num, client=client)
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
