"""
Baseline inference script for Code Security Review OpenEnv.
Compliant with mandatory STDOUT format: [START], [STEP], [END].

Required environment variables (injected by grader):
    API_BASE_URL   — LiteLLM proxy endpoint
    API_KEY        — LiteLLM proxy key
    ENV_URL        — Running environment URL (default: http://localhost:7860)
    MODEL_NAME     — Model identifier (default: gpt-4o-mini)
"""

import os
import json
import re
import requests
from typing import List, Optional
from openai import OpenAI

# ── Config (NO load_dotenv – grader injects env vars directly) ────────────────
ENV_URL   = os.environ.get("ENV_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
BENCHMARK = "code-security-review"

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
    """Robustly extract JSON from LLM output."""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    candidates = re.findall(r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", text, re.DOTALL)
    for candidate in reversed(candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
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

def run_task(task_id: str, task_num: int, client: OpenAI) -> dict:
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
        messages = []

        while not done and step_num < max_steps:
            step_num += 1
            prompt = build_prompt(obs)
            action_dict = {}

            # ── LLM call (must go through grader proxy) ──────────────────────
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
            messages.append({"role": "assistant", "content": raw})

            action_dict = parse_json_from_llm(raw)
            action_str = json.dumps(action_dict)

            # ── Step env ─────────────────────────────────────────────────────
            step_resp = env_post("/step", data=action_dict)
            reward = step_resp["reward"]
            done   = step_resp["done"]
            obs    = step_resp.get("observation")

            all_rewards.append(reward)
            cumulative_reward += reward

            log_step(step=step_num, action=action_str, reward=reward, done=done, error=None)

        success = cumulative_reward >= 0.8
    except Exception as exc:
        print(f"[ERROR] task={task_id} exception: {exc}", flush=True)
    finally:
        clamped_score = round(min(0.99, max(0.01, cumulative_reward)), 3)
        log_end(success=success, steps=step_num, score=clamped_score, rewards=all_rewards)

    return {
        "task_num":        task_num,
        "task_id":         task_id,
        "score":           cumulative_reward,
        "success":         success,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Read proxy config exactly as the sample inference.py specifies
    api_base = os.getenv("API_BASE_URL", "https://api.openai.com/v1").strip()
    api_key  = os.getenv("HF_TOKEN", "").strip() or os.getenv("API_KEY", "").strip()

    # Validate — crash with a clear message if the grader didn't inject a key
    if not api_base:
        raise RuntimeError("API_BASE_URL is empty or not set")
    if not api_key:
        raise RuntimeError("Neither HF_TOKEN nor API_KEY is set")

    # Ensure base_url ends with / (httpx requires it)
    if not api_base.endswith("/"):
        api_base += "/"

    print(f"[INFO] API_BASE_URL = {api_base}", flush=True)
    print(f"[INFO] MODEL_NAME   = {MODEL_NAME}", flush=True)
    print(f"[INFO] ENV_URL      = {ENV_URL}", flush=True)

    # Clear any conflicting OPENAI_* env vars so the openai library
    # doesn't silently override our base_url / api_key
    os.environ.pop("OPENAI_BASE_URL", None)
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_API_BASE", None)

    # Initialize OpenAI client pointing at grader's LiteLLM proxy
    client = OpenAI(base_url=api_base, api_key=api_key)
    print(f"[INFO] OpenAI client initialized successfully", flush=True)

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
        r = run_task(task_id, task_num, client=client)
        results.append(r)

    if results:
        avg = round(sum(r["score"] for r in results) / len(results), 3)
        successes = sum(1 for r in results if r.get("success"))
        print(f"\n[SUMMARY] avg_reward={avg} tasks_passed={successes}/{len(results)}", flush=True)

if __name__ == "__main__":
    main()
