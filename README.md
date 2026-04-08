---
title: Code Security Review OpenEnv
emoji: 🛡️
colorFrom: gray
colorTo: purple
sdk: docker
pinned: false
tags:
  - openenv
---

# Code Security Review — OpenEnv Environment

An RL environment for training AI agents to perform real-world code security review.
Agents analyze code from production pull requests across a **two-phase** multi-step
workflow: first discovering the hidden file, then identifying the vulnerability.

Built by **Inmodel Labs** for the Meta PyTorch OpenEnv Hackathon.

---

## Environment Overview

| Field | Value |
|---|---|
| Tasks | 3 (easy → medium → hard) |
| Languages | Python, JavaScript |
| Action space | Phase 1: `{"request_file": true}` / Phase 2: Structured JSON (6 fields) |
| Reward range | 0.0 – 1.0 (clamped) |
| Steps per episode | 2 (max) |

---

## Tasks

| ID | Language | Bug Class | Difficulty |
|---|---|---|---|
| `python-off-by-one` | Python | Off-by-one index error | Easy |
| `js-auth-privilege` | JavaScript | Logic flaw — privilege escalation | Medium |
| `python-pickle-deserialization` | Python | Insecure deserialization (RCE) | Hard |

---

## Two-Phase Episode Walkthrough

The agent operates in a **2-step sequential workflow** that mirrors a real AppSec triage process:

**Step 1 — File Discovery** (`+0.20`)
The agent receives only the PR title and file path. The code is hidden. The agent must request access:
```json
{"request_file": true}
```
The environment unlocks the code snippet and returns it in the observation.

**Step 2 — Security Review** (up to `+0.80`)
The agent analyses the code and submits a structured JSON finding:
```json
{
  "bug_identified": true,
  "bug_location": "line 3 — range(len(transactions) + 1)",
  "bug_type": "off-by-one",
  "bug_description": "Off-by-one error causes IndexError on last iteration...",
  "severity": "medium",
  "suggested_fix": "Change range(len(transactions) + 1) to range(len(transactions))"
}
```

---

## Action Space

### Phase 1 — File Request
```json
{"request_file": true}
```

### Phase 2 — Bug Review
| Field | Type | Values |
|---|---|---|
| `bug_identified` | bool | `true` / `false` |
| `bug_location` | string | location description |
| `bug_type` | string | `off-by-one` \| `logic-error` \| `security-vulnerability` \| `none` |
| `bug_description` | string | detailed vulnerability explanation |
| `severity` | string | `none` \| `low` \| `medium` \| `high` \| `critical` |
| `suggested_fix` | string | how to fix the bug |

## Observation Space

```json
{
  "task_id": "python-pickle-deserialization",
  "language": "Python",
  "difficulty": "hard",
  "code_snippet": "<FILE CONTENTS HIDDEN - Submit {\"request_file\": true} to view>",
  "context": "Background worker loading serialized state via network payload",
  "pr_title": "Add state persistence layer for distributed workers",
  "file_path": "worker/state.py"
}
```
After `request_file`, `code_snippet` contains the actual source code.

---

## Reward Breakdown

| Step | Component | Max Score |
|---|---|---|
| 1 | File request granted | 0.20 |
| 2 | Bug identified | 0.20 |
| 2 | Bug type correct | 0.20 |
| 2 | Bug location correct | 0.10 |
| 2 | Description quality | 0.25 |
| 2 | Fix quality | 0.15 |
| 2 | Severity correct | 0.10 |
| **Total** | | **1.00** |

The grader penalises keyword stuffing — incoherent keyword dumps score ≤ 0.20 on the description component.
Episode total reward is **clamped to [0.0, 1.0]**.

**Example Calculation:**
Agent requests file (+0.20), correctly identifies bug (+0.20), correct type (+0.20),
finds 50% location keywords (+0.05), writes good description (+0.20),
suggests partial fix (+0.08), correct severity (+0.10) = total `0.20+0.20+0.20+0.05+0.20+0.08+0.10 = 1.00` → clamped to `1.00`.

---

## Edge Cases

- **At step 0:** `reset()` must be called first. Calling `step()` without a reset triggers auto-reset.
- **Phase 1 skip:** If the agent skips `request_file` and submits a review directly on step 1, it receives no intermediate reward and the code snippet used for grading may be hidden.
- **Max step limit:** Episode ends at `done=True` when a bug review is submitted or `max_steps=2` is reached.
- **At done=True:** Calling `step()` returns `reward=0.0`, `done=True`, and `info["error"]` indicating the episode is complete.

---

## Baseline Scores

| Task | Difficulty | Model | Score | Steps | Notes |
|------|-----------|-------|-------|-------|-------|
| python-off-by-one | easy | Llama-3.3-70B-Instruct | 0.883 | 2 | File request + review |
| js-auth-privilege | medium | Llama-3.3-70B-Instruct | 0.900 | 2 | File request + review |
| python-pickle-deserialization | hard | Llama-3.3-70B-Instruct | TBD | 2 | Requires RCE/deserialization knowledge |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/reset?task_id=<id>` | Reset environment, returns observation |
| POST | `/step` | Submit action (Phase 1 or Phase 2), returns reward |
| GET | `/state` | Current episode state |
| GET | `/tasks` | List all tasks |

---

## Setup

### Docker

```bash
docker build -t code-security-review .
docker run -p 8000:8000 code-security-review
```

### Local

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

---

## Running Inference

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct"
export HF_TOKEN="hf_your_token_here"
export ENV_URL="http://localhost:8000"

python inference.py
```
