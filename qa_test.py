import requests
import json

BASE_URL = "http://localhost:7860"

def run_tests():
    checks = []

    # 1. GET /
    try:
        r = requests.get(f"{BASE_URL}/")
        passed = r.status_code == 200 and r.json().get("status") == "ok"
        checks.append({
            "id": 1, "name": "GET / health check", "passed": passed,
            "expected": 'HTTP 200 and {"status": "ok"}', "got": f"HTTP {r.status_code} {r.text}"
        })
    except Exception as e:
        checks.append({"id": 1, "name": "GET / health check", "passed": False, "expected": "200 OK", "got": str(e)})

    # 15. GET /state before reset (Edge case)
    try:
        r = requests.get(f"{BASE_URL}/state")
        # Should not crash
        checks.append({
            "id": 15, "name": "GET /state before any reset", "passed": r.status_code == 200,
            "expected": "HTTP 200 (No crash)", "got": f"HTTP {r.status_code} {r.text}"
        })
    except Exception as e:
        checks.append({"id": 15, "name": "GET /state before any reset", "passed": False, "expected": "200 OK", "got": str(e)})

    # 2. POST /reset
    try:
        r = requests.post(f"{BASE_URL}/reset")
        data = r.json().get("observation", {})
        required = ["task_id", "language", "difficulty", "code_snippet", "context", "pr_title", "file_path"]
        passed = all(k in data for k in required)
        checks.append({
            "id": 2, "name": "POST /reset fields check", "passed": passed,
            "expected": f"JSON with {required}", "got": list(data.keys())
        })
    except Exception as e:
        checks.append({"id": 2, "name": "POST /reset fields check", "passed": False, "expected": "Fields", "got": str(e)})

    # 16. POST /reset no task_id
    try:
        r = requests.post(f"{BASE_URL}/reset")
        checks.append({
            "id": 16, "name": "POST /reset no task_id (Random)", "passed": r.status_code == 200,
            "expected": "HTTP 200", "got": f"HTTP {r.status_code}"
        })
    except Exception as e:
        checks.append({"id": 16, "name": "POST /reset no task_id (Random)", "passed": False, "expected": "200 OK", "got": str(e)})

    # 3-5. POST /reset?task_id=...
    for tid in ["python-off-by-one", "js-auth-privilege", "python-sql-injection"]:
        try:
            num = {"python-off-by-one": 3, "js-auth-privilege": 4, "python-sql-injection": 5}[tid]
            r = requests.post(f"{BASE_URL}/reset?task_id={tid}")
            passed = r.status_code == 200 and r.json()["observation"]["task_id"] == tid
            checks.append({
                "id": num, "name": f"POST /reset for {tid}", "passed": passed,
                "expected": f"HTTP 200 with task_id={tid}", "got": f"HTTP {r.status_code} {r.json()['observation']['task_id'] if passed else r.text}"
            })
        except Exception as e:
            checks.append({"id": num, "name": f"POST /reset for {tid}", "passed": False, "expected": "200 OK", "got": str(e)})

    # 6. GET /state
    try:
        r = requests.get(f"{BASE_URL}/state")
        data = r.json()
        required = ["task_id", "step", "done", "total_reward"]
        passed = all(k in data for k in required)
        checks.append({
            "id": 6, "name": "GET /state fields check", "passed": passed,
            "expected": f"JSON with {required}", "got": list(data.keys())
        })
    except Exception as e:
        checks.append({"id": 6, "name": "GET /state fields check", "passed": False, "expected": "Fields", "got": str(e)})

    # 7. POST /step with PROVIDED action
    try:
        requests.post(f"{BASE_URL}/reset?task_id=python-sql-injection")
        action = {
            "bug_identified": True,
            "bug_location": "line 2 f-string",
            "bug_type": "security-vulnerability",
            "bug_description": "SQL injection via f-string",
            "severity": "critical",
            "suggested_fix": "use parameterized query"
        }
        r = requests.post(f"{BASE_URL}/step", json=action)
        res = r.json()
        reward = res.get("reward", -1.0)
        done = res.get("done", False)
        passed = 0.0 <= reward <= 1.0 and done is True
        checks.append({
            "id": 7, "name": "POST /step valid action", "passed": passed,
            "expected": "Reward [0,1] and done=true", "got": f"reward={reward}, done={done}"
        })
    except Exception as e:
        checks.append({"id": 7, "name": "POST /step valid action", "passed": False, "expected": "Result", "got": str(e)})

    # 14. Call POST /step twice (Edge Case)
    try:
        # Step already called in task 7
        action = {"bug_identified": False, "bug_location": "", "bug_type": "none", "bug_description": "", "severity": "none", "suggested_fix": ""}
        r = requests.post(f"{BASE_URL}/step", json=action)
        res = r.json()
        passed = r.status_code == 200 and "error" in res.get("info", {})
        checks.append({
            "id": 14, "name": "POST /step twice in same episode", "passed": passed,
            "expected": "HTTP 200 and error in info", "got": f"HTTP {r.status_code}, info={res.get('info')}"
        })
    except Exception as e:
        checks.append({"id": 14, "name": "POST /step twice in same episode", "passed": False, "expected": "Handled error", "got": str(e)})

    # 8. Perfect action for SQL
    try:
        requests.post(f"{BASE_URL}/reset?task_id=python-sql-injection")
        perfect_action = {
            "bug_identified": True,
            "bug_location": "line 2 f-string interpolation in SQL query construction",
            "bug_type": "security-vulnerability",
            "bug_description": "SQL injection vulnerability where user-supplied search_term is directly interpolated into the SQL query via f-string. An attacker can inject malicious SQL to bypass authentication, exfiltrate all user data, or drop tables. The fix is to use parameterized queries which sanitize user input automatically.",
            "severity": "critical",
            "suggested_fix": "Use db.execute('SELECT * FROM users WHERE name LIKE %s', ('%'+search_term+'%',)) instead of f-string interpolation"
        }
        r = requests.post(f"{BASE_URL}/step", json=perfect_action)
        reward = r.json().get("reward", 0.0)
        checks.append({
            "id": 8, "name": "PERFECT action SQL", "passed": reward >= 0.85,
            "expected": "Reward >= 0.85", "got": f"reward={reward}"
        })
    except Exception as e:
        checks.append({"id": 8, "name": "PERFECT action SQL", "passed": False, "expected": ">=0.85", "got": str(e)})

    # 9. Keyword stuffed
    try:
        requests.post(f"{BASE_URL}/reset?task_id=python-sql-injection")
        stuffed_action = {
            "bug_identified": True,
            "bug_location": "sql",
            "bug_type": "security-vulnerability",
            "bug_description": "sql injection sql injection sql injection parameterized f-string sanitize escape malicious attack tautology union drop sql injection sql injection",
            "severity": "critical",
            "suggested_fix": "fix"
        }
        r = requests.post(f"{BASE_URL}/step", json=stuffed_action)
        reward = r.json().get("reward", 1.0)
        checks.append({
            "id": 9, "name": "KEYWORD STUFFED action", "passed": reward <= 0.20,
            "expected": "Reward <= 0.20", "got": f"reward={reward}"
        })
    except Exception as e:
        checks.append({"id": 9, "name": "KEYWORD STUFFED action", "passed": False, "expected": "<=0.20", "got": str(e)})

    # 10. Bug identified false
    try:
        requests.post(f"{BASE_URL}/reset")
        action = {"bug_identified": False, "bug_location": "", "bug_type": "none", "bug_description": "", "severity": "none", "suggested_fix": ""}
        r = requests.post(f"{BASE_URL}/step", json=action)
        reward = r.json().get("reward", 1.0)
        checks.append({
            "id": 10, "name": "Identify=False empty fields", "passed": reward == 0.0,
            "expected": "Reward exactly 0.0", "got": f"reward={reward}"
        })
    except Exception as e:
        checks.append({"id": 10, "name": "Identify=False empty fields", "passed": False, "expected": "0.0", "got": str(e)})

    # 11. Partial credit severity
    try:
        # Off-by-one is severity critical (I set it to critical).
        # Let's say I submit 'low' severity.
        requests.post(f"{BASE_URL}/reset?task_id=python-off-by-one")
        action = {
            "bug_identified": True, "bug_location": "range", "bug_type": "off-by-one",
            "bug_description": "off-by-one error in range function call",
            "severity": "low", # Wrong severity
            "suggested_fix": "range(len(x))"
        }
        r = requests.post(f"{BASE_URL}/step", json=action)
        info = r.json().get("info", {})
        breakdown = info.get("reward_breakdown", {})
        sev_score = breakdown.get("severity", -1.0)
        # It should be 0.0 (wrong) but the total should still have partial credit from other components
        reward = r.json().get("reward", 0.0)
        checks.append({
            "id": 11, "name": "Partial credit (wrong severity)", "passed": 0.0 < reward < 1.0,
            "expected": "Reward between 0 and 1 (partial credit)", "got": f"reward={reward}, severity_component={sev_score}"
        })
    except Exception as e:
        checks.append({"id": 11, "name": "Partial credit (wrong severity)", "passed": False, "expected": "Partial credit", "got": str(e)})

    # 12-13. Breakdown keys and components
    try:
        requests.post(f"{BASE_URL}/reset")
        action = {"bug_identified": True, "bug_location": "test", "bug_type": "test", "bug_description": "test test test test test test test test test test test test test test test test test test test test", "severity": "none", "suggested_fix": "test test test"}
        r = requests.post(f"{BASE_URL}/step", json=action)
        info = r.json().get("info", {})
        breakdown = info.get("reward_breakdown", {})
        required = ["bug_identified", "bug_type", "bug_location", "description_quality", "fix_quality", "severity"]
        checks.append({
            "id": 12, "name": "Reward breakdown keys", "passed": all(k in breakdown for k in required),
            "expected": f"Breakdown with {required}", "got": list(breakdown.keys())
        })
        
        max_vals = {
            "bug_identified": 0.20, "bug_type": 0.20, "bug_location": 0.10,
            "description_quality": 0.25, "fix_quality": 0.15, "severity": 0.10
        }
        passed_range = all(0.0 <= breakdown.get(k, -1) <= max_vals[k] for k in max_vals)
        checks.append({
            "id": 13, "name": "Component score ranges", "passed": passed_range,
            "expected": "All components <= max", "got": breakdown
        })
    except Exception as e:
        checks.append({"id": 12, "name": "Breakdown checks", "passed": False, "expected": "Breakdown", "got": str(e)})

    # Sort and print
    checks.sort(key=lambda x: x["id"])
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"[{c['id']}] {c['name']} — {status}")
        print(f"     Expected: {c['expected']}")
        print(f"     Got: {c['got']}")
        print("")

    passed_count = sum(1 for c in checks if c["passed"])
    disqual = "YES" if passed_count < 7 else "NO" # Disqualified if Part 1 fails
    print(f"TOTAL: {passed_count}/16 passed")
    print(f"DISQUALIFICATION RISK: {disqual}")
    # Estimate score based on points
    score = (passed_count / 16) * 100
    print(f"ESTIMATED SCORE: {round(score)}/100")

if __name__ == "__main__":
    run_tests()
