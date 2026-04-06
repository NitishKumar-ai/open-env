"""
Baseline inference script for Code Security Review OpenEnv.

Usage:
    python inference.py

Required environment variables:
    API_BASE_URL  — LLM API endpoint  (default: HF router)
    MODEL_NAME    — Model identifier
    HF_TOKEN      — Hugging Face / API key
    ENV_BASE_URL  — Running environment URL (default: http://localhost:7860)
"""

import os
import json
import time
import re
from dotenv import load_dotenv

# Load .env variables before anything else
load_dotenv()

import requests
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

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

# ── Helpers ───────────────────────────────────────────────────────────────────

from typing import Optional

def env_post(path: str, data: Optional[dict] = None, params: Optional[dict] = None) -> dict:
    url = f"{ENV_BASE_URL}{path}"
    resp = requests.post(url, json=data or {}, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_json_from_llm(text: str) -> dict:
    """Robustly extract JSON from LLM output, stripping markdown fences."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
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

def run_task(difficulty: str, task_num: int) -> dict:
    reset_resp = env_post("/reset", params={"difficulty": difficulty})
    obs = reset_resp["observation"]

    print(f"[START] task={task_num} difficulty={difficulty} task_id={obs['task_id']} max_steps={obs['max_steps']}")

    cumulative_reward = 0.0
    step_num = 0
    done = False

    while not done and step_num < obs["max_steps"]:
        step_num += 1
        prompt = build_prompt(obs)

        # ── LLM call ──────────────────────────────────────────────────────────
        t0 = time.time()
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
        except Exception as exc:
            print(f"[ERROR] task={task_num} step={step_num} llm_error={exc}")
            action_dict = {
                "bug_identified": False,
                "bug_location": "",
                "bug_type": "none",
                "bug_description": "",
                "severity": "none",
                "suggested_fix": "",
            }
        latency = round(time.time() - t0, 2)

        # ── Step env ──────────────────────────────────────────────────────────
        step_resp = env_post("/step", data=action_dict)
        reward = step_resp["reward"]
        done   = step_resp["done"]
        obs    = step_resp["observation"]
        info   = step_resp.get("info", {})

        cumulative_reward += reward

        print(
            f"[STEP] task={task_num} step={step_num} "
            f"reward={reward:.3f} cumulative={cumulative_reward:.3f} "
            f"done={done} latency_s={latency}"
        )

    result = {
        "task_num":        task_num,
        "difficulty":      difficulty,
        "total_reward":    round(cumulative_reward, 3),
        "steps_taken":     step_num,
        "success":         cumulative_reward >= 0.8,
    }
    print(
        f"[END] task={task_num} difficulty={difficulty} "
        f"total_reward={result['total_reward']} success={result['success']}"
    )
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[INFO] model={MODEL_NAME} env={ENV_BASE_URL}")

    tasks = [
        ("easy",   1),
        ("medium", 2),
        ("hard",   3),
    ]
    results = []

    for difficulty, task_num in tasks:
        try:
            r = run_task(difficulty, task_num)
        except Exception as exc:
            print(f"[ERROR] task={task_num} difficulty={difficulty} error={exc}")
            r = {"task_num": task_num, "difficulty": difficulty,
                 "total_reward": 0.0, "success": False}
        results.append(r)

    avg = round(sum(r["total_reward"] for r in results) / len(results), 3)
    successes = sum(1 for r in results if r.get("success"))
    print(f"\n[SUMMARY] avg_reward={avg} tasks_passed={successes}/{len(results)}")
    for r in results:
        print(f"  [{r['difficulty']:6}] reward={r['total_reward']:.3f} success={r.get('success', False)}")


if __name__ == "__main__":
    main()
