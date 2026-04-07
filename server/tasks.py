TASKS = {
    "python-off-by-one": {
        "id": "python-off-by-one",
        "name": "Python Off-by-One Error",
        "language": "Python",
        "difficulty": "easy",
        "bug_class": "Off-by-one index error",
        "pr_title": "Add batch processor for financial transactions",
        "file_path": "finance/batch_processor.py",
        "context": "Finance batch processor that sums transaction amounts for end-of-day reconciliation",
        "code_snippet": (
            "def process_transactions(transactions):\n"
            "    total = 0\n"
            "    for i in range(len(transactions) + 1):  # iterates one past end\n"
            "        total += transactions[i][\"amount\"]\n"
            "    return total"
        ),
        "bug_type": "off-by-one",
        "bug_location": "line 3 — range(len(transactions) + 1)",
        "severity": "critical",
        "keywords": [
            "off-by-one", "index", "range", "indexerror", "out of bounds",
            "boundary", "overflow", "iteration", "list length", "plus one",
            "extra step", "fencepost error", "array access", "iterator",
            "fix", "bug", "identify", "code", "crash", "out-of-range",
            "python", "finance", "batch", "amount", "total", "transactions",
            "iterate", "sum", "loop", "account", "process"
        ],
        "fix_patterns": [
            "range(len(transactions))",
            "len(transactions))",
            "for transaction in transactions",
            "in transactions:",
            "pop()",
            "enumerate(transactions)",
            "transactions[:len(transactions)]",
            "total += transactions[i]"
        ],
    },

    "js-auth-privilege": {
        "id": "js-auth-privilege",
        "name": "JavaScript Auth Logic Flaw",
        "language": "JavaScript",
        "difficulty": "medium",
        "bug_class": "Logic flaw — privilege escalation",
        "pr_title": "Refactor auth middleware for API routes",
        "file_path": "middleware/auth.js",
        "context": "Node.js authentication middleware that restricts admin-only API routes",
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
        "bug_location": "line 3 — incorrect boolean operator || instead of &&",
        "severity": "critical",
        "keywords": [
            "short-circuit disjunction hazard", "logical disjunction vulnerability",
            "excessive authorization scope", "privilege escalation vector",
            "boolean logic flaw pattern", "operator precedence violation",
            "authorization bypass disjunction logic", "improper validation layer check",
            "role check disjunction pattern match", "permission leak evaluation flow",
            "evaluation shortcut logic flaw", "middleware logic hazard state",
            "security constraint bypass", "access control logic inversion"
        ],
        "fix_patterns": [
            "user.role === \"admin\" && user.isActive",
            "&& user.isActive",
            "throw new Error(\"Unauthorized\")",
            "user.role === 'admin' && user.isActive",
            "middleware logic fix"
        ],
    },

    "python-sql-injection": {
        "id": "python-sql-injection",
        "name": "Python SQL Injection",
        "language": "Python",
        "difficulty": "hard",
        "bug_class": "SQL injection via f-string",
        "pr_title": "Add user search endpoint to REST API",
        "file_path": "api/users.py",
        "context": "REST API endpoint that searches users by name in a PostgreSQL database",
        "code_snippet": (
            "def search_users(db, search_term):\n"
            "    query = f\"SELECT * FROM users WHERE name LIKE '%{search_term}%'\"\n"
            "    results = db.execute(query)\n"
            "    return results.fetchall()"
        ),
        "bug_type": "security-vulnerability",
        "bug_location": "line 2 — f-string interpolation directly in SQL query",
        "severity": "critical",
        "keywords": [
            "sql injection", "user-supplied", "search_term", "interpolated", "f-string",
            "attacker", "bypass", "authentication", "exfiltrate", "user data",
            "drop tables", "parameterized", "queries", "sanitize", "input", "automatically"
        ],
        "fix_patterns": [
            "db.execute('SELECT * FROM users WHERE name LIKE %s', ('%'+search_term+'%',))",
            "%s",
            "parameterized",
            "prepared statement"
        ],
    },
}
