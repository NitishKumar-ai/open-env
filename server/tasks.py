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

    "js-idor-auth": {
        "id": "js-idor-auth",
        "name": "JavaScript IDOR Authorization Bypass",
        "language": "JavaScript",
        "difficulty": "medium",
        "bug_class": "Insecure Direct Object Reference (IDOR)",
        "pr_title": "Add user profile endpoint to REST API",
        "file_path": "routes/users.js",
        "context": "Node.js/Express REST API — authenticated endpoint returning a user's account profile",
        "code_snippet": (
            "const authenticate = require('./middleware/authenticate');\n\n"
            "app.get('/users/:userId/profile', authenticate, async (req, res) => {\n"
            "    const user = await db.findUser(req.params.userId);\n"
            "    if (!user) return res.status(404).json({ error: 'User not found' });\n"
            "    return res.json(user);\n"
            "});"
        ),
        "bug_type": "logic-error",
        "bug_location": "line 4 — no check that req.user.id matches req.params.userId",
        "severity": "high",
        "keywords": [
            "idor", "insecure direct object reference", "authorization", "horizontal",
            "privilege", "escalation", "authorization check", "user id",
            "req.user", "params.userId", "ownership", "access control",
            "unauthenticated", "other user", "missing check", "object-level"
        ],
        "fix_patterns": [
            "req.user.id",
            "req.params.userId",
            "403",
            "Forbidden"
        ],
    },

    "python-pickle-deserialization": {
        "id": "python-pickle-deserialization",
        "name": "Python Pickle Deserialization",
        "language": "Python",
        "difficulty": "hard",
        "bug_class": "Insecure Deserialization",
        "pr_title": "Add distributed task caching layer for worker pool",
        "file_path": "worker/cache.py",
        "context": "Redis-backed caching decorator for worker tasks that serializes results to a shared cache",
        "code_snippet": (
            "import pickle, redis\n\n"
            "_cache = redis.Redis(host='localhost')\n\n"
            "def cached_task(key_prefix):\n"
            "    def decorator(fn):\n"
            "        def wrapper(*args, **kwargs):\n"
            "            cache_key = f'{key_prefix}:{args[0]}'\n"
            "            cached = _cache.get(cache_key)\n"
            "            if cached:\n"
            "                return pickle.loads(cached)\n"
            "            result = fn(*args, **kwargs)\n"
            "            _cache.set(cache_key, pickle.dumps(result), ex=3600)\n"
            "            return result\n"
            "        return wrapper\n"
            "    return decorator"
        ),
        "bug_type": "insecure-deserialization",
        "bug_location": "line 11 — pickle.loads(cached) deserializes untrusted Redis data without validation",
        "severity": "critical",
        "keywords": [
            "cache poisoning", "redis poisoning", "__reduce__",
            "magic method", "arbitrary bytecode", "hmac", "signing key",
            "cryptographic integrity", "deserialization gadget", "supply chain"
        ],
        "fix_patterns": [
            "hmac.new",
            "hmac.compare_digest",
            "signing_key",
        ],
        "keyword_target_override": 3.0,
    },
}
