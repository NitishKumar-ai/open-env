"""OpenEnv Tasks for Code Security Review.

These task specifications are designed to rigorously test autonomous AI 
agents' abilities to identify, classify, and mitigate common software
security vulnerabilities across distinct language paradigms.
"""

from typing import Dict, Any

TASKS: Dict[str, Any] = {
    "python-off-by-one": {
        "id": "python-off-by-one",
        "name": "Python Off-by-One Error",
        "language": "Python",
        "difficulty": "easy",
        "bug_class": "Index Error / Off-by-one",
        "pr_title": "Update finance batch processor for transactions",
        "file_path": "finance/processor.py",
        "context": "Process numeric transaction data for weekly reporting",
        "code_snippet": (
            "def calculate_total(transactions):\n"
            "    total = 0\n"
            "    for i in range(len(transactions) + 1):\n"
            "        total += transactions[i]\n"
            "    return total"
        ),
        "bug_type": "off-by-one",
        "bug_location": "line 3 — loop range(len(transactions) + 1) incorrectly iterates one past the end",
        "severity": "medium",
        "keywords": [
            "off-by-one", "index", "error", "range", "length", "loop", "extra", 
            "out of bounds", "indexerror", "end", "one past", "terminates", 
            "iteration", "boundary", "array", "transactions", "last",
            "overflow", "stop-condition", "size", "pointer"
        ],
        "fix_patterns": [
            "range(len(transactions))",
            "enumerate(transactions)",
            "for tx in transactions"
        ],
    },

    "js-auth-privilege": {
        "id": "js-auth-privilege",
        "name": "JavaScript Auth Logic Flaw",
        "language": "JavaScript",
        "difficulty": "medium",
        "bug_class": "Privilege Escalation / Logic Flaw",
        "pr_title": "Implement admin middleware for dashboard",
        "file_path": "middleware/auth.js",
        "context": "Node.js/Express middleware to restrict access to admin routes",
        "code_snippet": (
            "function checkAdmin(req, res, next) {\n"
            "    const user = req.user;\n"
            "    if (user.role !== \"admin\" || user.isActive) {\n"
            "        return next();\n"
            "    }\n"
            "    return res.status(403).json({ error: \"Forbidden\" });\n"
            "}"
        ),
        "bug_type": "logic-error",
        "bug_location": "line 3 — incorrect boolean operator || instead of && allows any active user",
        "severity": "critical",
        "keywords": [
            "logic", "operator", "boolean", "disjunction", "escalation", "bypass", "checkAdmin", 
            "admin", "role", "active", "isActive", "mistake", "security", "authorization",
            "middleware", "express", "res.status", "next", "auth", "permission", "user", "access"
        ],
        "fix_patterns": [
            "user.role === \"admin\" && user.isActive",
            "&& user.isActive",
            "throw new Error(\"Unauthorized\")",
            "return next"
        ],
        "keyword_target_override": 1.0,
    },

    "python-pickle-deserialization": {
        "id": "python-pickle-deserialization",
        "name": "Python Pickle Deserialization",
        "language": "Python",
        "difficulty": "hard",
        "bug_class": "Insecure Deserialization",
        "pr_title": "Add state persistence layer for distributed workers",
        "file_path": "worker/state.py",
        "context": "Background worker loading serialized state via network payload",
        "code_snippet": (
            "import pickle\n\n"
            "def load_worker_state(payload_bytes):\n"
            "    state = pickle.loads(payload_bytes)\n"
            "    return state['config']"
        ),
        "bug_type": "security-vulnerability",
        "bug_location": "line 4 — pickle.loads() executes arbitrary code during object recreation",
        "severity": "critical",
        "keywords": [
            "deserialization", "pickle", "loads", "arbitrary", "code execution", "rce",
            "injection", "untrusted", "payload", "cve", "insecure", "un-serialize",
            "malicious", "exploit", "magic methods", "reduce"
        ],
        "fix_patterns": [
            "json.loads",
            "hmac",
            "signatures",
            "safe_load"
        ],
    },
}
