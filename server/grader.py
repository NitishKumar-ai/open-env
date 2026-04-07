from typing import Tuple, Dict


def grade_action(action: dict, task: dict) -> Tuple[float, Dict[str, float]]:
    reward = 0.0
    breakdown: Dict[str, float] = {}

    # ── Component 1: Bug identified (0.20) ──────────────────────────────────
    if action.get("bug_identified"):
        reward += 0.20
        breakdown["bug_identified"] = 0.20
    else:
        breakdown["bug_identified"] = 0.00
        # No bug found → no partial credit for anything else
        return max(0.0, min(1.0, reward)), breakdown

    # ── Component 2: Bug type match (0.20) ──────────────────────────────────
    action_type = action.get("bug_type", "").lower().replace("-", " ").replace("_", " ")
    task_type = task["bug_type"].lower().replace("-", " ").replace("_", " ")
    if task_type in action_type or action_type in task_type:
        reward += 0.20
        breakdown["bug_type"] = 0.20
    else:
        breakdown["bug_type"] = 0.00

    # ── Component 3: Bug location (0.10) ────────────────────────────────────
    action_location = action.get("bug_location", "").lower()
    location_keywords = [w for w in task["bug_location"].lower().split() if len(w) > 3]
    if location_keywords:
        matched = sum(1 for kw in location_keywords if kw in action_location)
        loc_score = round(0.10 * (matched / len(location_keywords)), 4)
    else:
        loc_score = 0.0
    reward += loc_score
    breakdown["bug_location"] = loc_score

    # ── Component 4: Description quality (0.25) ──────────────────────────────
    description = action.get("bug_description", "").lower()
    desc_score = 0.0
    if len(description) >= 20:
        task_keywords = task["keywords"]
        matched_kw = [kw for kw in task_keywords if kw in description]
        # Full points if they hit at least 3 keywords
        desc_score = round(min(0.25, 0.25 * (len(matched_kw) / 3.0)), 4)
    breakdown["description_quality"] = desc_score
    reward += desc_score

    # ── Component 5: Fix quality (0.15) ──────────────────────────────────────
    fix = action.get("suggested_fix", "").lower()
    fix_score = 0.0
    if len(fix) >= 10:
        fix_patterns = task["fix_patterns"]
        matched_fix = [p for p in fix_patterns if p.lower() in fix]
        # Match any 1 pattern for full points
        fix_score = round(min(0.15, 0.15 * len(matched_fix)), 4)
    breakdown["fix_quality"] = fix_score
    reward += fix_score

    # ── Component 6: Severity (0.10) ─────────────────────────────────────────
    action_sev = action.get("severity", "").lower()
    task_sev = task["severity"].lower()
    if action_sev == task_sev:
        sev_score = 0.10
    elif action_sev in ("high", "critical") and task_sev in ("high", "critical"):
        sev_score = 0.05
    else:
        sev_score = 0.00
    breakdown["severity"] = sev_score
    reward += sev_score

    # ── Global Penalty: Keyword Stuffing ────────────────────────────────────
    description = action.get("bug_description", "").lower()
    words = description.split()
    unique_ratio = len(set(words)) / len(words) if words else 1.0
    if unique_ratio < 0.5:
        reward *= 0.2  # Heavy global penalty
        breakdown["stuffing_penalty_multiplier"] = 0.2
        for k in list(breakdown.keys()):
            if k != "stuffing_penalty_multiplier":
                breakdown[k] = round(breakdown[k] * 0.2, 4)

    return max(0.0, min(1.0, round(reward, 4))), breakdown
