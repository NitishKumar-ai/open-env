# OpenEnv Submission Checklist
> Complete every item before final submission. A single ❌ in any **DISQUALIFYING** section means you cannot submit.

---

## HOW TO USE THIS CHECKLIST

1. Work through each section **in order** — earlier sections unblock later ones.
2. Mark each item `[x]` when confirmed, or add a note if it needs fixing.
3. Any item marked **🚨 DISQUALIFYING** must be `[x]` before submission or you will be automatically rejected.
4. After all items are checked, run the final validator command at the bottom.

---

## SECTION 1 — REAL-WORLD TASK SIMULATION

> Weight: 30% of total score. Judges will ask: "Would a practitioner actually use this?"

### 1.1 Domain Validity

- [ ] **The environment simulates a task that real humans do professionally or daily.** Examples that pass: email triage, code review, data cleaning, customer support ticket routing, document summarisation, scheduling assistant, content moderation, form validation, compliance checking. Examples that fail: CartPole, GridWorld, Snake, made-up puzzles.
- [ ] The task domain is stated clearly in the README's first paragraph — a reader understands the real-world context within 3 sentences.
- [ ] The environment would be useful for evaluating or training AI agents on a real skill, not just for demonstrating API integration.

### 1.2 Domain Depth

- [ ] The environment models at least the core mechanic of the real task (e.g. for email triage: an inbox, email metadata, categories, urgency signals — not just "send a string and get a string back").
- [ ] Action and observation spaces reflect what a human would actually do and see in this task.
- [ ] The hardest task (task 3) would challenge a frontier model (GPT-4o / Claude 3.5 Sonnet level) — it is not trivially solved by pattern matching.

---

## SECTION 2 — OPENENV SPEC COMPLIANCE

> Weight: part of the 15% code quality score. **All 🚨 items are disqualifying.**

### 2.1 Typed Models

- [ ] `Observation` is a Pydantic `BaseModel` with typed fields. No `dict`, no `Any` unless explicitly documented.
- [ ] `Action` is a Pydantic `BaseModel` with typed fields.
- [ ] `Reward` is a `float` or a Pydantic model containing a `float` value field.
- [ ] All three models are importable from a single module (e.g. `from my_env import Observation, Action`).
- [ ] Every field has a type annotation. No bare `Optional` without a type parameter.

### 2.2 Core API Methods

- [ ] 🚨 `reset()` is implemented and returns an `Observation` (or an object containing one).
- [ ] 🚨 `step(action: Action)` is implemented and returns `(observation, reward, done, info)` or a structured equivalent.
- [ ] 🚨 `state()` is implemented and returns the current full environment state (serialisable dict or Pydantic model).
- [ ] `reset()` produces a **clean, reproducible initial state** — calling it twice with the same seed gives the same starting observation.
- [ ] `step()` after `done=True` either raises a clean error or resets automatically (document which).
- [ ] `info` dict (or equivalent) is non-empty and useful — at minimum contains the current task name and step count.

### 2.3 `openenv.yaml`

- [ ] 🚨 `openenv.yaml` exists in the project root.
- [ ] Contains `name:` field (string, slug-safe).
- [ ] Contains `version:` field (semver, e.g. `0.1.0`).
- [ ] Contains `description:` field (1–2 sentences).
- [ ] Contains `tasks:` list with at least 3 entries, each having `name:`, `difficulty:`, and `description:`.
- [ ] Contains `observation_space:` description block.
- [ ] Contains `action_space:` description block.
- [ ] Passes `openenv validate` without errors (run this command and paste output into your notes).

```bash
# Run this and confirm zero errors:
openenv validate openenv.yaml
```

---

## SECTION 3 — MINIMUM 3 TASKS WITH AGENT GRADERS

> Weight: 25% of total score. All 🚨 items are disqualifying.

### 3.1 Task Definitions

- [ ] 🚨 Exactly 3 or more tasks are defined.
- [ ] Task 1 is labelled **easy** and a baseline LLM can score ≥ 0.6 on it with no fine-tuning.
- [ ] Task 2 is labelled **medium** and presents a genuine multi-step challenge.
- [ ] Task 3 is labelled **hard** and a strong frontier model scores < 0.8 on it without domain-specific prompting.
- [ ] Each task has a concise, unambiguous objective statement that a human tester can understand without reading the code.

### 3.2 Grader Requirements

- [ ] 🚨 Each task has a **programmatic grader** — no human-in-the-loop, no LLM-as-judge for the primary score.
- [ ] 🚨 Every grader returns a float in **[0.0, 1.0]** — no values below 0 or above 1 ever.
- [ ] Graders are **deterministic**: given the same sequence of actions, they always return the same score.
- [ ] Graders are **reproducible**: scores do not depend on system time, random seeds not exposed to the grader, or external API calls.
- [ ] Partial credit is awarded — the grader does not return only 0.0 or 1.0 (binary graders are disqualifying for medium/hard tasks).
- [ ] The grader logic is readable: another developer can understand the scoring rubric in < 5 minutes by reading the grader function.

### 3.3 Difficulty Verification (run before submitting)

```bash
# Run baseline inference on all three tasks and record scores:
TASK=easy   python inference.py   # expected: score >= 0.6
TASK=medium python inference.py   # expected: score in 0.3–0.7
TASK=hard   python inference.py   # expected: score < 0.8
```

- [ ] Easy task baseline score is ≥ 0.6.
- [ ] Medium task baseline score is meaningfully lower than easy (at least 0.15 gap).
- [ ] Hard task baseline score is < 0.8 (if it's ≥ 0.8, make it harder).

---

## SECTION 4 — MEANINGFUL REWARD FUNCTION

> Weight: part of the 20% environment design score.

### 4.1 Dense Reward Signal

- [ ] The reward function provides **intermediate signal** — the agent gets feedback before the episode ends, not only at `done=True`.
- [ ] At least 3 distinct reward levels exist across the task trajectory (not just 0.0 at each step then 1.0 at the end).
- [ ] Progress toward task completion is reflected in the reward — an agent making progress always earns more than one doing nothing.

### 4.2 Reward Shaping

- [ ] **Clearly undesirable behaviour is penalised**: e.g. repeated identical actions, contradictory outputs, destructive operations, or exceeding step limits incur a negative reward or zero instead of positive.
- [ ] The reward function cannot be gamed by a trivial exploit (e.g. sending the longest possible string every step to maximise a length-based reward without solving the task).
- [ ] Total episode reward is bounded — the maximum possible score per episode is documented in the README.
- [ ] Reward is normalised to [0.0, 1.0] at the episode level (sum of step rewards / max possible reward, clamped).

### 4.3 Reward Documentation

- [ ] The reward formula is documented in the README with an example calculation.
- [ ] Edge cases are documented: what happens at step 0, at `done=True`, and at the max step limit.

---

## SECTION 5 — BASELINE INFERENCE SCRIPT

> Weight: part of the 15% code quality score. All 🚨 items are disqualifying.

### 5.1 File and Location

- [ ] 🚨 The script is named **exactly** `inference.py` (lowercase, no suffix variation).
- [ ] 🚨 `inference.py` is in the **root directory** of the project (not in a subdirectory).
- [ ] The script runs end-to-end without interactive input (no `input()` calls, no manual setup required).

### 5.2 Environment Variables

- [ ] 🚨 `API_BASE_URL` is read from `os.getenv("API_BASE_URL", "<your-default>")`. A default is set so the script doesn't crash when the variable is absent.
- [ ] 🚨 `MODEL_NAME` is read from `os.getenv("MODEL_NAME", "<your-default>")`.
- [ ] 🚨 `HF_TOKEN` is read from `os.getenv("HF_TOKEN")` (no default — it must be set externally; the script should fail with a clear message if absent).
- [ ] `IMAGE_NAME` / `LOCAL_IMAGE_NAME` is read from `os.getenv("IMAGE_NAME")` or `os.getenv("LOCAL_IMAGE_NAME")` if Docker-based.
- [ ] No credentials, tokens, or API keys are hardcoded in any source file.

### 5.3 OpenAI Client Usage

- [ ] 🚨 **All LLM calls use the `OpenAI` client** from `openai` package — no `requests`, no `httpx`, no `anthropic` SDK, no `transformers` pipeline.
- [ ] Client is initialised as: `client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)` where `API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")`.
- [ ] `client.chat.completions.create(...)` is used for all inference calls.
- [ ] `stream=False` is set explicitly (streaming is not expected by the evaluator).

### 5.4 Stdout Log Format — **EXACT FORMAT REQUIRED**

> Any deviation in field names, ordering, or capitalisation will break automated scoring.

- [ ] 🚨 Exactly **one `[START]` line** is emitted at the beginning of each episode, before any steps.

  ```
  [START] task=<task_name> env=<benchmark> model=<model_name>
  ```

- [ ] 🚨 Exactly **one `[STEP]` line** is emitted after each `env.step()` call, immediately after it returns.

  ```
  [STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  ```

- [ ] 🚨 Exactly **one `[END]` line** is emitted after `env.close()`, and it is **always emitted even if an exception occurs** (wrap in `finally:`).

  ```
  [END] success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>
  ```

- [ ] `reward` and all values in `rewards` are formatted to **exactly 2 decimal places** (e.g. `1.00`, `0.75`, `0.00`).
- [ ] `score` is formatted to **exactly 3 decimal places** (e.g. `0.750`).
- [ ] `done` and `success` are lowercase strings: `true` or `false` (not `True`/`False`, not `1`/`0`).
- [ ] `error` is either the raw error string or the literal string `null` (not `None`, not empty string).
- [ ] **No newlines within a single log line** — each log entry is exactly one line.
- [ ] Fields are in the exact order shown above — no reordering.
- [ ] No extra spaces, tabs, or punctuation between fields (single space separator between `key=value` pairs).

### 5.5 Reproducibility

- [ ] Running the script twice with the same `MODEL_NAME` and environment seed produces scores within ±0.05 of each other (minor LLM variance is acceptable; wild swings are not).
- [ ] The script covers all 3 tasks — either by looping over task names or via `TASK` environment variable as shown in the sample.
- [ ] `MAX_STEPS` is set to a value that allows the task to be completed (not too low) but finishes within the time limit.

### 5.6 Runtime Constraint

- [ ] 🚨 The full inference script (all 3 tasks) completes in **under 20 minutes** on a machine with 2 vCPUs and 8 GB RAM.
- [ ] Each individual task episode completes in under 5 minutes.
- [ ] No step blocks indefinitely — all `env.step()` calls have an implicit or explicit timeout.

---

## SECTION 6 — DOCKER AND CONTAINERISATION

> Weight: part of the 15% code quality score. All 🚨 items are disqualifying.

### 6.1 Dockerfile

- [ ] 🚨 A `Dockerfile` exists in the project root.
- [ ] 🚨 `docker build -t myenv .` completes without errors on a clean machine.
- [ ] 🚨 `docker run --rm myenv` starts the environment server and it responds to `reset()`.
- [ ] The base image is appropriate for the task (e.g. `python:3.11-slim`, not an oversized or obscure base).
- [ ] All Python dependencies are installed via `pip install -r requirements.txt` or equivalent inside the Dockerfile.
- [ ] The Dockerfile does **not** require internet access at runtime (all deps installed at build time).
- [ ] No secrets or API keys are baked into the Docker image.
- [ ] The container starts the environment server on a documented port (default: 8000 or 7860).
- [ ] The container exposes that port with `EXPOSE <port>` in the Dockerfile.

### 6.2 Resource Constraints

- [ ] The built image size is < 5 GB (ideally < 2 GB).
- [ ] The running container uses < 6 GB RAM at peak (leaving headroom for the 8 GB machine limit).
- [ ] The container starts up in < 60 seconds.

### 6.3 `requirements.txt` (or equivalent)

- [ ] `requirements.txt` exists in the project root.
- [ ] All dependencies have pinned versions (e.g. `openai==1.30.0`, not `openai`).
- [ ] `openai` package is listed (required for inference script).
- [ ] `pydantic` package is listed.
- [ ] `pyyaml` package is listed (for openenv.yaml parsing).

---

## SECTION 7 — HUGGING FACE SPACES DEPLOYMENT

> Weight: part of the 15% code quality score. All 🚨 items are disqualifying.

### 7.1 Space Setup

- [ ] 🚨 The HF Space is **publicly accessible** — not private or gated.
- [ ] 🚨 The Space is tagged with `openenv` in the repository tags.
- [ ] The Space type is `Docker` (not `Gradio` or `Streamlit`, unless the env server is built on one of those).
- [ ] The Space metadata in `README.md` YAML header includes `tags: [openenv]`.

### 7.2 Availability Check

- [ ] 🚨 A `GET` request to `https://your-space-url/` returns HTTP 200.
- [ ] 🚨 A `POST` to `https://your-space-url/reset` returns a valid JSON observation.
- [ ] `POST /step` with a valid action body returns `(observation, reward, done, info)`.
- [ ] `GET /state` returns the current environment state.
- [ ] The Space has been running for at least 10 minutes without crashing before submission.

### 7.3 Space Configuration

- [ ] `README.md` in the repo root has valid HF Space YAML header:

  ```yaml
  ---
  title: Your Environment Name
  emoji: 🤖
  colorFrom: blue
  colorTo: purple
  sdk: docker
  pinned: false
  tags:
    - openenv
  ---
  ```

- [ ] The Space hardware tier is sufficient to run the environment (CPU Basic is fine for most cases).
- [ ] Environment variables required at runtime are set as **Space Secrets** in the HF Space settings (not hardcoded).

---

## SECTION 8 — README DOCUMENTATION

> A well-written README is part of the 15% code quality score.

### 8.1 Required Sections

- [ ] **Environment Description** — what real-world task is simulated, why it matters, what an agent needs to learn to succeed.
- [ ] **Observation Space** — table or structured description of every field in the `Observation` model, including type, range, and meaning.
- [ ] **Action Space** — table or structured description of every field in the `Action` model, including valid values and constraints.
- [ ] **Task Descriptions** — for each task: name, difficulty label (easy/medium/hard), objective, grader description, example episode.
- [ ] **Reward Function** — formula, components, max possible reward per episode, normalisation method.
- [ ] **Setup Instructions** — exact commands to clone, build, and run locally:

  ```bash
  git clone https://huggingface.co/spaces/YOUR_USER/YOUR_ENV
  cd YOUR_ENV
  docker build -t myenv .
  docker run -p 8000:8000 myenv
  ```

- [ ] **Inference Script Usage** — exact commands with environment variables:

  ```bash
  export HF_TOKEN=hf_...
  export API_BASE_URL=https://router.huggingface.co/v1
  export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
  python inference.py
  ```

- [ ] **Baseline Scores** — a table with columns: Task | Model | Score | Steps | Notes.

### 8.2 Baseline Scores Table (paste your actual results)

| Task | Difficulty | Model | Score | Steps | Notes |
|------|-----------|-------|-------|-------|-------|
| task_1 | easy | — | — | — | |
| task_2 | medium | — | — | — | |
| task_3 | hard | — | — | — | |

- [ ] The table is filled in with real numbers from a completed inference run.
- [ ] The easy task score is ≥ 0.6.

---

## SECTION 9 — CODE QUALITY AND PROJECT STRUCTURE

### 9.1 Project Layout

- [ ] Project root contains at minimum:

  ```
  /
  ├── inference.py          ← inference script (mandatory name)
  ├── openenv.yaml          ← OpenEnv spec file
  ├── Dockerfile            ← container definition
  ├── requirements.txt      ← pinned dependencies
  ├── README.md             ← documentation
  └── src/ or myenv/       ← environment source code
      ├── env.py            ← environment class
      ├── models.py         ← Observation, Action, Reward models
      ├── tasks/            ← one file per task + grader
      └── server.py         ← HTTP server (FastAPI or equivalent)
  ```

- [ ] No large binary files (datasets > 50 MB, model weights) are committed to the repo. Use URLs or HF datasets instead.
- [ ] `.gitignore` excludes `__pycache__`, `.env`, `*.pyc`, and any local credentials.

### 9.2 Code Standards

- [ ] All Python files pass `flake8` or `ruff` with no errors (warnings are acceptable).
- [ ] All Pydantic models have docstrings or field descriptions.
- [ ] No bare `except:` clauses — exceptions are caught specifically.
- [ ] No `print()` statements in the environment code (use `logging`). `print()` is only in `inference.py` for structured stdout logs.
- [ ] Environment class has a module-level docstring explaining what it does.

### 9.3 Testing

- [ ] At minimum, a smoke test exists: instantiate the env, call `reset()`, call `step()` with a valid action, assert `done` is a bool and `reward` is a float.
- [ ] The smoke test passes:

  ```bash
  python -m pytest tests/ -v
  # or
  python test_smoke.py
  ```

---

## SECTION 10 — CREATIVITY AND NOVELTY

> Weight: 10% of total score. This section cannot disqualify you, but it can push you to the top.

- [ ] The problem domain is novel — not a re-skin of email triage or the echo example from the sample script.
- [ ] The reward design has an interesting property: e.g. multi-objective trade-offs, adversarial components, information asymmetry, sequential dependency between steps.
- [ ] The hard task has a mechanic that makes it qualitatively harder, not just quantitatively (more steps / more categories is not enough — the agent must reason differently).
- [ ] The environment would be cited or referenced by others building agents in this domain.

---

## SECTION 11 — FINAL PRE-SUBMISSION VALIDATION

Run these commands in order. All must succeed with zero errors.

### Step 1 — Validate OpenEnv spec

```bash
openenv validate openenv.yaml
```

Expected output: `✓ openenv.yaml is valid`

- [ ] ✓ PASSED

### Step 2 — Build Docker image

```bash
docker build -t myenv-final .
```

Expected: exits with code 0, image appears in `docker images`.

- [ ] ✓ PASSED

### Step 3 — Start container and health check

```bash
docker run -d -p 8000:8000 --name myenv-test myenv-final
sleep 10
curl -s http://localhost:8000/ | python3 -m json.tool
curl -s -X POST http://localhost:8000/reset | python3 -m json.tool
docker stop myenv-test && docker rm myenv-test
```

Expected: Both curl commands return valid JSON with no errors.

- [ ] ✓ PASSED

### Step 4 — Run full inference script

```bash
export HF_TOKEN=<your_token>
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

# Run all tasks (adjust loop to match your task names)
for TASK in easy medium hard; do
  MY_ENV_TASK=$TASK python inference.py
done
```

Expected: Three complete runs, each emitting `[START]`, N×`[STEP]`, and `[END]` with no Python exceptions.

- [ ] ✓ PASSED — Easy score: ______ Medium score: ______ Hard score: ______

### Step 5 — Verify log format

Pipe one run through a format checker:

```bash
MY_ENV_TASK=easy python inference.py 2>/dev/null | python3 -c "
import sys, re
lines = sys.stdin.read().splitlines()
start = sum(1 for l in lines if l.startswith('[START]'))
step  = sum(1 for l in lines if l.startswith('[STEP]'))
end   = sum(1 for l in lines if l.startswith('[END]'))
assert start == 1, f'Expected 1 [START], got {start}'
assert step  >= 1, f'Expected >=1 [STEP], got {step}'
assert end   == 1, f'Expected 1 [END], got {end}'
end_line = next(l for l in lines if l.startswith('[END]'))
assert 'success=' in end_line
assert 'steps=' in end_line
assert 'score=' in end_line
assert 'rewards=' in end_line
score_val = re.search(r'score=(\d+\.\d+)', end_line).group(1)
assert len(score_val.split('.')[1]) == 3, f'score must be 3 decimal places, got: {score_val}'
print('✓ Log format is valid')
print(f'  [START] lines: {start}')
print(f'  [STEP] lines:  {step}')
print(f'  [END] lines:   {end}')
"
```

- [ ] ✓ PASSED

### Step 6 — Verify HF Space is live

```bash
curl -s -o /dev/null -w "%{http_code}" https://YOUR-USERNAME-YOUR-ENV.hf.space/
# Must return 200
```

- [ ] ✓ PASSED — Space URL: ______________________________

### Step 7 — Verify grader scores are in [0, 1]

```bash
python3 -c "
from myenv.tasks import task_easy, task_medium, task_hard  # adjust import
# Run a few grader calls with dummy actions and assert bounds
# (adjust to your actual grader API)
print('✓ All graders return values in [0.0, 1.0]')
"
```

- [ ] ✓ PASSED

---

## DISQUALIFICATION SUMMARY

Before submitting, confirm that **every 🚨 item** below is checked. If any are unchecked, stop and fix them first.

| # | Disqualifying Item | Checked? |
|---|---|---|
| D1 | `reset()` is implemented and works | ☐ |
| D2 | `step()` is implemented and works | ☐ |
| D3 | `state()` is implemented and works | ☐ |
| D4 | `openenv.yaml` exists and passes validation | ☐ |
| D5 | Exactly 3+ tasks with programmatic graders | ☐ |
| D6 | All graders return float in [0.0, 1.0] | ☐ |
| D7 | `inference.py` is in the project root | ☐ |
| D8 | OpenAI client is used for all LLM calls | ☐ |
| D9 | `[START]` log line is exactly correct | ☐ |
| D10 | `[STEP]` log line is exactly correct | ☐ |
| D11 | `[END]` log line is always emitted (in finally) | ☐ |
| D12 | `API_BASE_URL` read from env var | ☐ |
| D13 | `MODEL_NAME` read from env var | ☐ |
| D14 | `HF_TOKEN` read from env var | ☐ |
| D15 | Dockerfile builds without errors | ☐ |
| D16 | Container starts and responds to `reset()` | ☐ |
| D17 | HF Space is public and returns HTTP 200 | ☐ |
| D18 | Full inference run completes in < 20 minutes | ☐ |

---

## SUBMISSION SIGN-OFF

When all items above are checked, fill in this block and attach it to your submission.

```
Environment Name:  ___________________________________
HF Space URL:      ___________________________________
Baseline Scores:
  - Easy task:     ______  (task name: _____________)
  - Medium task:   ______  (task name: _____________)
  - Hard task:     ______  (task name: _____________)
Inference runtime: ______ minutes
Docker image size: ______ MB
Submitted by:      ___________________________________
Date:              ___________________________________

I confirm all 18 disqualifying items are checked [yes/no]: ______
I confirm the full validator suite passes [yes/no]:         ______
```

---

*Generated for OpenEnv Hackathon submission — covers all judging criteria, pre-submission checks, and mandatory infrastructure requirements.*
