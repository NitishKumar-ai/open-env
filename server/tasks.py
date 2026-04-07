# OpenEnv Tasks for Code Security Review
# These tasks are designed to test AI agents' ability to identify common security vulnerabilities.

TASKS = {
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
            "iteration", "boundary", "array", "transactions", "last"
        ],
        "fix_patterns": [
            "range(len(transactions))",
            "enumerate(transactions)",
            "for tx in transactions",
            "len(transactions)",
            "0, len(transactions)"
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
            "logic", "operator", "operator mistake", "boolean", "disjunction", 
            "escalation", "bypass", "checkAdmin", "admin", "role", "active", 
            "isActive", "should be and", "should be &&", "or", "security barrier"
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
            "interpolated", "f-string", "format", "string", "concatenation",
            "exfiltrate", "malicious", "union", "tautology", "attack",
            "vulnerability", "sanitization", "validation", "parameterized", "query"
        ],
        "fix_patterns": [
            "execute(query, (search_term,))",
            "bind variables",
            "parameterized query",
            "query parameters",
            "DBAPI parameter"
        ],
    },
}
