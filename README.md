---
title: Code Review Env
emoji: 🏃
colorFrom: red
colorTo: purple
sdk: docker
pinned: false
---
# Code Security Review — OpenEnv

> An RL environment for training AI agents to detect bugs and security
> vulnerabilities in Python code.

## Motivation

Code review is one of the highest-leverage tasks in software engineering, yet it
remains bottlenecked on human attention. This environment trains agents to catch
real bug categories — from simple off-by-one errors to critical SQL injection
vulnerabilities — using structured, deterministic reward signals.

---

## Action Space

| Field | Type | Description |
|---|---|---|
| `bug_identified` | bool | Whether a bug was found |
| `bug_location` | string | Exact location (function, expression) |
| `bug_type` | string | `off-by-one`, `logic-error`, `security-vulnerability`, `none` |
| `bug_description` | string | Explanation of the bug and its impact |
| `severity` | string | `none` / `low` / `medium` / `high` / `critical` |
| `suggested_fix` | string | Corrected code or fix description |

## Observation Space

| Field | Type | Description |
|---|---|---|
| `code_snippet` | string | The code to review |
| `language` | string | Programming language |
| `task_description` | string | What the code is supposed to do |
| `task_id` | string | Unique task identifier |
| `difficulty` | string | `easy` / `medium` / `hard` |
| `step_number` | int | Current step within the episode |
| `max_steps` | int | Maximum steps allowed (3) |
| `previous_feedback` | string? | Feedback from prior step |

---

## Tasks

### Easy — Off-by-one in array traversal
- **Code:** `sum_elements(arr)` iterates `range(1, len(arr)+1)` causing `IndexError`
- **Expected bug type:** `off-by-one`
- **Expected severity:** `high`
- **Baseline score:** ~0.72

### Medium — Authentication logic flaw
- **Code:** `authenticate_user()` uses `or` instead of `and` for admin check
- **Expected bug type:** `logic-error`
- **Expected severity:** `critical`
- **Baseline score:** ~0.60

### Hard — SQL injection via f-string
- **Code:** `fetch_records()` interpolates `user_id` and `sort_column` directly into SQL
- **Expected bug type:** `security-vulnerability`
- **Expected severity:** `critical`
- **Baseline score:** ~0.55

---

## Reward Function

Rewards are deterministic and provide partial progress signal:

| Component | Max Score | Description |
|---|---|---|
| Bug identified | 0.20 | Correctly flags presence/absence of bug |
| Bug type | 0.20 | Correct category of bug |
| Bug location | 0.10 | Precise location identified |
| Description quality | 0.25 | Keyword density in explanation |
| Fix quality | 0.15 | Correct fix keywords present |
| Severity | 0.10 | Correct severity level |
| **Total** | **1.00** | |

---

## Setup

### 1. Build and run Docker

```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

### 2. Run inference baseline

```bash
# Set your environment variables
export HF_TOKEN=hf_your_token_here
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export API_BASE_URL=https://router.huggingface.co/v1
export ENV_BASE_URL=http://localhost:7860

# Install dependencies
pip install -r requirements.txt

# Run
python inference.py
```

### 3. Validate (OpenEnv CLI)

```bash
openenv validate
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/reset?difficulty=easy` | Reset environment |
| POST | `/step` | Submit a review action |
| GET | `/state` | Current episode state |

---

## Baseline Scores

| Task | Difficulty | Reward |
|---|---|---|
| Off-by-one detection | Easy | ~0.72 |
| Auth logic flaw | Medium | ~0.60 |
| SQL injection | Hard | ~0.55 |
| **Average** | | **~0.62** |

---

## Project Structure

```
code-review-env/
├── Dockerfile
├── openenv.yaml
├── requirements.txt
├── inference.py
├── README.md
└── server/
    ├── __init__.py
    ├── app.py          # FastAPI endpoints
    ├── environment.py  # Tasks + grader logic
    └── models.py       # Pydantic action/observation/state
```
