from typing import Dict, Any, Tuple, Optional
from .models import CodeReviewAction, CodeReviewObservation, CodeReviewState

MAX_STEPS = 3

# TASK DEFINITIONS


TASKS: Dict[str, dict] = {

    # EASY 
    "easy": {
        "id": "task_easy_001",
        "difficulty": "easy",
        "language": "python",
        "description": (
            "This function is supposed to sum all elements in a list. "
            "Find any bugs and suggest a fix."
        ),
        "code": (
            "def sum_elements(arr):\n"
            '    """Return the sum of all elements."""\n'
            "    total = 0\n"
            "    for i in range(1, len(arr) + 1):  # iterates over indices\n"
            "        total += arr[i]\n"
            "    return total"
        ),
        "ground_truth": {
            "bug_identified": True,
            "bug_type_keywords": [
                "off-by-one", "off by one", "index error", "indexerror",
                "out of bounds", "out of range", "index out",
            ],
            "location_keywords": [
                "range(1, len(arr) + 1)", "len(arr) + 1", "len(arr)+1",
                "range", "loop", "index", "arr[i]",
            ],
            "description_keywords": [
                "index", "range", "len", "off-by-one", "off by one",
                "IndexError", "out of bounds", "+1", "exceed", "arr[i]",
                "zero", "start",
            ],
            "fix_keywords": [
                "range(len(arr))", "range(0, len(arr))",
                "for i in range(len", "for element in arr",
                "arr[i]" , "len(arr))",
            ],
            "severity_valid": ["high", "medium"],
        },
    },

    #MEDIUM 
    "medium": {
        "id": "task_medium_001",
        "difficulty": "medium",
        "language": "python",
        "description": (
            "This authentication function controls admin access. "
            "Find the logical security bug."
        ),
        "code": (
            "def authenticate_user(username, password, request_admin=False):\n"
            '    """Authenticate user and return access level."""\n'
            "    user = db.find_user(username)\n"
            "    if not user or user.password_hash != hash_password(password):\n"
            '        return {"authenticated": False, "level": "none"}\n'
            "\n"
            "    # Elevate to admin if caller requests it OR user has admin role\n"
            "    if request_admin or user.role == 'admin':   # <-- review this\n"
            '        return {"authenticated": True, "level": "admin"}\n'
            "\n"
            '    return {"authenticated": True, "level": "user"}'
        ),
        "ground_truth": {
            "bug_identified": True,
            "bug_type_keywords": [
                "logic", "logic error", "logical", "privilege escalation",
                "authorization", "authentication bypass", "access control",
            ],
            "location_keywords": [
                "request_admin or", "or user.role", "or", "condition",
                "if request_admin", "or user.role == 'admin'",
            ],
            "description_keywords": [
                "or", "and", "privilege", "escalation", "bypass", "admin",
                "role", "caller", "request_admin", "logic", "elevation",
                "any caller", "arbitrary",
            ],
            "fix_keywords": [
                "and", "request_admin and user.role", "and user.role == 'admin'",
                "and user.role", "both",
            ],
            "severity_valid": ["critical", "high"],
        },
    },

    # ── HARD ──────────────────────────────────
    "hard": {
        "id": "task_hard_001",
        "difficulty": "hard",
        "language": "python",
        "description": (
            "This function fetches records from a database using user-supplied input. "
            "Identify the security vulnerability."
        ),
        "code": (
            "def fetch_records(user_id: str, sort_column: str):\n"
            '    """Fetch user records sorted by a given column."""\n'
            "    conn = get_db_connection()\n"
            "    cursor = conn.cursor()\n"
            "\n"
            "    query = (\n"
            '        f"SELECT id, name, email FROM users "\n'
            '        f"WHERE user_id = {user_id} "\n'
            '        f"ORDER BY {sort_column}"\n'
            "    )\n"
            "    cursor.execute(query)\n"
            "    rows = cursor.fetchall()\n"
            "    conn.close()\n"
            "    return rows"
        ),
        "ground_truth": {
            "bug_identified": True,
            "bug_type_keywords": [
                "sql injection", "injection", "sqli", "sql",
                "security vulnerability", "security", "second-order",
            ],
            "location_keywords": [
                "f\"", "f-string", "format", "user_id", "sort_column",
                "query", "ORDER BY", "WHERE user_id",
            ],
            "description_keywords": [
                "sql injection", "injection", "parameterized", "f-string",
                "format string", "user input", "sanitize", "escape",
                "malicious", "attack", "tautology", "union", "drop",
                "ORDER BY", "sort_column", "arbitrary",
            ],
            "fix_keywords": [
                "parameterized", "?", "%s", "cursor.execute(query, (",
                "cursor.execute(query, [", "prepared statement",
                "whitelist", "allowlist", "ALLOWED_COLUMNS",
                "sanitize", "if sort_column not in",
            ],
            "severity_valid": ["critical"],
        },
    },

    # ── EXPERT ────────────────────────────────
    "expert": {
        "id": "task_expert_001",
        "difficulty": "expert",
        "language": "java",
        "description": (
            "This Java class implements a token bucket rate limiter. "
            "Identify the logic bug that could allow users to bypass the rate limit."
        ),
        "code": (
            "import java.util.concurrent.atomic.AtomicLong;\n\n"
            "public class TokenBucketRateLimiter {\n"
            "    private final long maxTokens;\n"
            "    private final long refillRatePerSecond;\n"
            "    private AtomicLong currentTokens;\n"
            "    private AtomicLong lastRefillTimestamp;\n\n"
            "    public TokenBucketRateLimiter(long maxTokens, long refillRatePerSecond) {\n"
            "        this.maxTokens = maxTokens;\n"
            "        this.refillRatePerSecond = refillRatePerSecond;\n"
            "        this.currentTokens = new AtomicLong(maxTokens);\n"
            "        this.lastRefillTimestamp = new AtomicLong(System.currentTimeMillis());\n"
            "    }\n\n"
            "    /**\n"
            "     * Checks if the requested number of tokens is available.\n"
            "     * Decrements the bucket if allowed.\n"
            "     */\n"
            "    public synchronized boolean allowRequest(int tokensNeeded) {\n"
            "        refill();\n"
            "        if (currentTokens.get() >= tokensNeeded) {\n"
            "            currentTokens.addAndGet(-tokensNeeded);\n"
            "            return true;\n"
            "        }\n"
            "        return false;\n"
            "    }\n\n"
            "    private void refill() {\n"
            "        long now = System.currentTimeMillis();\n"
            "        long timeElapsedMs = now - lastRefillTimestamp.get();\n"
            "        \n"
            "        // Calculate how many tokens to add based on time elapsed\n"
            "        long tokensToAdd = (timeElapsedMs / 1000) * refillRatePerSecond;\n\n"
            "        if (tokensToAdd > 0) {\n"
            "            // Hint: Look closely at how the tokens are updated here.\n"
            "            // Consider what happens if a user stops making requests for a long time.\n"
            "            currentTokens.addAndGet(tokensToAdd);\n"
            "            lastRefillTimestamp.set(now);\n"
            "        }\n"
            "    }\n"
            "}"
        ),
        "ground_truth": {
            "bug_identified": True,
            "bug_type_keywords": [
                "logic", "limit", "overflow", "cap", "bound", "maximum", "exceed",
                "logic error", "capacity",
            ],
            "location_keywords": [
                "currentTokens.addAndGet", "refill()", "tokensToAdd",
                "currentTokens.get()", "addAndGet(tokensToAdd)",
            ],
            "description_keywords": [
                "exceed", "maxTokens", "cap", "limit", "bound",
                "overflow", "infinite", "burst", "accumulate",
            ],
            "fix_keywords": [
                "Math.min", "min(", "set(", "if (currentTokens.get() > maxTokens)",
                "compareAndSet", "cap",
            ],
            "severity_valid": ["high", "medium"],
        },
    },

    # ── EXPERT 2 (C++) ────────────────────────
    "expert2": {
        "id": "task_expert_002",
        "difficulty": "expert2",
        "language": "cpp",
        "description": (
            "This C++ class implements an event dispatcher. "
            "Identify the concurrency bug that can occur when an event is dispatched."
        ),
        "code": (
            "#include <iostream>\n"
            "#include <vector>\n"
            "#include <functional>\n"
            "#include <mutex>\n"
            "#include <algorithm>\n"
            "#include <string>\n\n"
            "class EventDispatcher {\n"
            "public:\n"
            "    using Callback = std::function<void(const std::string&)>;\n\n"
            "    void subscribe(int listener_id, Callback cb) {\n"
            "        std::lock_guard<std::mutex> lock(mut_);\n"
            "        listeners_.push_back({listener_id, cb});\n"
            "    }\n\n"
            "    void unsubscribe(int listener_id) {\n"
            "        std::lock_guard<std::mutex> lock(mut_);\n"
            "        listeners_.erase(\n"
            "            std::remove_if(listeners_.begin(), listeners_.end(),\n"
            "                [listener_id](const Listener& l) { return l.id == listener_id; }),\n"
            "            listeners_.end()\n"
            "        );\n"
            "    }\n\n"
            "    void dispatch(const std::string& event_data) {\n"
            "        std::lock_guard<std::mutex> lock(mut_);\n"
            "        for (const auto& listener : listeners_) {\n"
            "            // Hint: What happens if a listener decides to call unsubscribe() \n"
            "            // from inside their own callback function when an event fires?\n"
            "            listener.cb(event_data);\n"
            "        }\n"
            "    }\n\n"
            "private:\n"
            "    struct Listener {\n"
            "        int id;\n"
            "        Callback cb;\n"
            "    };\n    \n"
            "    std::vector<Listener> listeners_;\n"
            "    std::mutex mut_;\n"
            "};"
        ),
        "ground_truth": {
            "bug_identified": True,
            "bug_type_keywords": [
                "deadlock", "concurrency", "lock", "recursive", "reentrant", "hang",
                "iterator validation", "undefined behavior"
            ],
            "location_keywords": [
                "listener.cb", "unsubscribe", "dispatch", "mut_", "std::lock_guard",
                "lock(mut_)"
            ],
            "description_keywords": [
                "deadlock", "already locked", "same thread", "recursive_mutex",
                "reentrant", "hangs", "blocks", "invalidate", "iterator"
            ],
            "fix_keywords": [
                "std::recursive_mutex", "copy", "local copy", "copy the vector",
                "unlock before", "queue", "deferred"
            ],
            "severity_valid": ["high", "critical"],
        },
    },
}



# GRADER


def grade_action(action: CodeReviewAction, task: dict) -> Tuple[float, Dict]:
    """
    Score the agent's review on a 0.0–1.0 scale.

    Breakdown:
      bug_identified   0.20
      bug_type         0.20
      bug_location     0.10
      bug_description  0.25  (keyword density, capped)
      suggested_fix    0.15  (keyword density, capped)
      severity         0.10
      ─────────────────────
      Total            1.00
    """
    gt = task["ground_truth"]
    score = 0.0
    breakdown: Dict[str, float] = {}

    # 1. Bug identification
    if action.bug_identified == gt["bug_identified"]:
        score += 0.20
        breakdown["bug_identified"] = 0.20
    else:
        breakdown["bug_identified"] = 0.00
        if not action.bug_identified:
            return 0.0, {
                "breakdown": breakdown,
                "total_score": 0.0,
                "feedback": "No bug identified — one definitely exists. Look more carefully.",
            }

    # 2. Bug type
    bug_type_lower = action.bug_type.lower()
    type_match = any(kw in bug_type_lower for kw in gt["bug_type_keywords"])
    if type_match:
        score += 0.20
        breakdown["bug_type"] = 0.20
    else:
        breakdown["bug_type"] = 0.00

    # 3. Bug location
    loc_lower = action.bug_location.lower()
    loc_match = any(kw.lower() in loc_lower for kw in gt["location_keywords"])
    if loc_match:
        score += 0.10
        breakdown["bug_location"] = 0.10
    else:
        breakdown["bug_location"] = 0.00

    # 4. Description quality (keyword density, capped at 0.25)
    desc_lower = action.bug_description.lower()
    desc_hits = sum(1 for kw in gt["description_keywords"] if kw.lower() in desc_lower)
    desc_score = round(min(0.25, desc_hits * 0.07), 3)
    score += desc_score
    breakdown["bug_description"] = desc_score

    # 5. Fix quality (keyword density, capped at 0.15)
    fix_lower = action.suggested_fix.lower()
    fix_hits = sum(1 for kw in gt["fix_keywords"] if kw.lower() in fix_lower)
    fix_score = round(min(0.15, fix_hits * 0.08), 3)
    score += fix_score
    breakdown["suggested_fix"] = fix_score

    # 6. Severity
    if action.severity.lower() in gt["severity_valid"]:
        score += 0.10
        breakdown["severity"] = 0.10
    else:
        breakdown["severity"] = 0.00

    total = round(min(1.0, score), 3)

    # Build human-readable feedback
    hints = []
    if breakdown["bug_type"] == 0:
        hints.append("Reconsider the bug category — be more specific.")
    if breakdown["bug_location"] == 0:
        hints.append("Pinpoint the exact line or expression that contains the bug.")
    if breakdown["suggested_fix"] < 0.08:
        hints.append("Your fix does not address the root cause — revise it.")
    if breakdown["severity"] == 0:
        hints.append("Re-evaluate the severity level.")

    feedback = " ".join(hints) if hints else "Strong analysis — refine the fix if needed."

    return total, {"breakdown": breakdown, "total_score": total, "feedback": feedback}

# ENVIRONMENT


class CodeReviewEnvironment:
    def __init__(self):
        self._state: Optional[CodeReviewState] = None
        self._current_task: Optional[dict] = None

    def reset(self, difficulty: str = "easy") -> CodeReviewObservation:
        if difficulty not in TASKS:
            difficulty = "easy"
        task = TASKS[difficulty]
        self._current_task = task
        self._state = CodeReviewState(
            task_id=task["id"],
            difficulty=difficulty,
            step_count=0,
            done=False,
            total_reward=0.0,
            task_complete=False,
        )
        return self._build_obs(step_number=0, previous_feedback=None)

    def step(self, action: CodeReviewAction) -> Tuple[CodeReviewObservation, float, bool, Dict]:
        if self._state is None or self._state.done:
            raise ValueError("Call reset() before step().")

        self._state.step_count += 1
        reward, info = grade_action(action, self._current_task)
        self._state.total_reward = round(self._state.total_reward + reward, 3)

        # Done if agent nailed it or max steps reached
        done = reward >= 0.80 or self._state.step_count >= MAX_STEPS
        self._state.done = done
        self._state.task_complete = reward >= 0.80

        feedback = info.get("feedback") if not done else None
        obs = self._build_obs(
            step_number=self._state.step_count,
            previous_feedback=feedback,
        )
        return obs, reward, done, info

    def state(self) -> CodeReviewState:
        if self._state is None:
            return CodeReviewState(
                task_id="", difficulty="easy",
                step_count=0, done=False,
                total_reward=0.0, task_complete=False,
            )
        return self._state

    # helpers

    def _build_obs(self, step_number: int, previous_feedback: Optional[str]) -> CodeReviewObservation:
        t = self._current_task
        return CodeReviewObservation(
            code_snippet=t["code"],
            language=t["language"],
            task_description=t["description"],
            task_id=t["id"],
            difficulty=t["difficulty"],
            step_number=step_number,
            max_steps=MAX_STEPS,
            previous_feedback=previous_feedback,
        )
