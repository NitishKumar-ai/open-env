# Code Security Review — OpenEnv Environment

An RL environment for training AI agents to perform real-world code security review.
Agents analyze code snippets from production pull requests and identify bugs,
vulnerabilities, and security issues.

Built by **Inmodel Labs** for the Meta PyTorch OpenEnv Hackathon.

---

## Environment Overview

| Field | Value |
|---|---|
| Tasks | 3 (easy → medium → hard) |
| Languages | Python, JavaScript |
| Action space | Structured JSON (6 fields) |
| Reward range | 0.0 – 1.0 |
| Steps per episode | 1 |

---

## Tasks

| ID | Language | Bug Class | Difficulty |
|---|---|---|---|
| `python-off-by-one` | Python | Off-by-one index error | Easy |
| `js-auth-privilege` | JavaScript | Logic flaw — privilege escalation | Medium |
| `python-sql-injection` | Python | SQL injection via f-string | Hard |

---

## Action Space

The agent submits a JSON action with these fields:

```json
{
  "bug_identified": true,
  "bug_location": "line 3 — range(len(transactions) + 1)",
  "bug_type": "logic-error",
  "bug_description": "Off-by-one error causes IndexError on last iteration...",
  "severity": "medium",
  "suggested_fix": "Change range(len(transactions) + 1) to range(len(transactions))"
}
```

## Observation Space

```json
{
  "task_id": "python-sql-injection",
  "language": "Python",
  "difficulty": "hard",
  "code_snippet": "def search_users(db, search_term):\n    ...",
  "context": "REST API endpoint that searches users by name",
  "pr_title": "Add user search endpoint to REST API",
  "file_path": "api/users.py"
}
```

---

## Reward Breakdown

| Component | Max Score |
|---|---|
| Bug identified | 0.20 |
| Bug type correct | 0.20 |
| Bug location correct | 0.10 |
| Description quality | 0.25 |
| Fix quality | 0.15 |
| Severity correct | 0.10 |
| **Total** | **1.00** |

The grader penalises keyword stuffing — incoherent keyword dumps score ≤ 0.20.

**Example Calculation:**
If the agent correctly identifies a bug (+0.20), misidentifies the type (+0.0), finds 50% of the location keywords (+0.05), writes a detailed and coherent description matching most keywords (+0.25), suggests a partially correct fix (+0.08), and gets the severity correct (+0.10), the total reward for that step would be `0.20 + 0.0 + 0.05 + 0.25 + 0.08 + 0.10 = 0.68`.

---

## Edge Cases

- **At step 0:** `reset()` must be called to initialize the state. If `step()` is called before `reset()`, the environment automatically calls `reset()` internally and evaluates the action on a random task.
- **Max step limit:** The maximum step limit is 1. Calling `step()` evaluates the action and immediately sets `done=True`.
- **At done=True:** Calling `step()` returns `reward=0.0`, `done=True`, and a clean error message in the `info` dict `("Episode already completed. Call /reset...")` indicating the episode is complete without auto-resetting.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/reset?task_id=<id>` | Reset environment, returns observation |
| POST | `/step` | Submit action, returns reward |
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
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your-api-key"
export ENV_URL="http://localhost:8000"

python inference.py
```
