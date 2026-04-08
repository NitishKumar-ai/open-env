"""Review Grader System.

Implements programmatic sub-scoring logic for evaluating agent
security actions against internal semantic criteria.
"""

from typing import Tuple, Dict, Any

SCORE_BUG_IDENTIFIED = 0.20
SCORE_BUG_TYPE = 0.20
SCORE_BUG_LOCATION = 0.10
SCORE_DESC_QUALITY = 0.25
SCORE_FIX_QUALITY = 0.15
SCORE_SEV_EXACT = 0.10
SCORE_SEV_PARTIAL = 0.05

KEYWORD_HIT_TARGET = 3.0
PENALTY_THRESHOLD = 0.5
PENALTY_MULTIPLIER = 0.2


def grade_action(action: Dict[str, Any], task: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Evaluate an action against the task definition.
    
    Args:
        action: The structured payload proposed by the AI agent.
        task: The dictionary blueprint detailing the expected vulnerability.
        
    Returns:
        A tuple of the normalized aggregate reward and the individual component breakdown.
    """
    reward = 0.0
    breakdown: Dict[str, float] = {}

    try:
        # ── Component 1: Bug identified (0.20) ──────────────────────────────────
        if action.get("bug_identified"):
            reward += SCORE_BUG_IDENTIFIED
            breakdown["bug_identified"] = SCORE_BUG_IDENTIFIED
        else:
            breakdown["bug_identified"] = 0.00
            # No bug found → no partial credit for anything else
            return max(0.01, min(0.99, reward)), breakdown

        # ── Component 2: Bug type match (0.20) ──────────────────────────────────
        action_type = action.get("bug_type", "").lower().replace("-", " ").replace("_", " ")
        task_type = task["bug_type"].lower().replace("-", " ").replace("_", " ")
        if task_type in action_type or action_type in task_type:
            reward += SCORE_BUG_TYPE
            breakdown["bug_type"] = SCORE_BUG_TYPE
        else:
            breakdown["bug_type"] = 0.00

        # ── Component 3: Bug location (0.10) ────────────────────────────────────
        action_location = action.get("bug_location", "").lower()
        location_keywords = [w for w in task["bug_location"].lower().split() if len(w) > 3]
        if location_keywords:
            matched = sum(1 for kw in location_keywords if kw in action_location)
            loc_score = round(SCORE_BUG_LOCATION * (matched / len(location_keywords)), 4)
        else:
            loc_score = 0.0
        
        reward += loc_score
        breakdown["bug_location"] = loc_score

        # ── Component 4: Description quality (0.25) ──────────────────────────────
        description = action.get("bug_description", "").lower()
        desc_score = 0.0
        if len(description) >= 20:
            task_keywords = task["keywords"]
            target = task.get("keyword_target_override", KEYWORD_HIT_TARGET)
            matched_kw = [kw for kw in task_keywords if kw in description]
            desc_score = round(min(SCORE_DESC_QUALITY, SCORE_DESC_QUALITY * (len(matched_kw) / target)), 4)
        
        breakdown["description_quality"] = desc_score
        reward += desc_score

        # ── Component 5: Fix quality (0.15) ──────────────────────────────────────
        fix = action.get("suggested_fix", "").lower()
        fix_score = 0.0
        if len(fix) >= 10:
            fix_patterns = task["fix_patterns"]
            matched_fix = [p for p in fix_patterns if p.lower() in fix]
            fix_score = round(min(SCORE_FIX_QUALITY, SCORE_FIX_QUALITY * len(matched_fix)), 4)
        
        breakdown["fix_quality"] = fix_score
        reward += fix_score

        # ── Component 6: Severity (0.10) ─────────────────────────────────────────
        action_sev = action.get("severity", "").lower()
        task_sev = task["severity"].lower()
        if action_sev == task_sev:
            sev_score = SCORE_SEV_EXACT
        elif action_sev in ("high", "critical") and task_sev in ("high", "critical"):
            sev_score = SCORE_SEV_PARTIAL
        else:
            sev_score = 0.00
        
        breakdown["severity"] = sev_score
        reward += sev_score

        # ── Global Penalty: Keyword Stuffing ────────────────────────────────────
        words = description.split()
        unique_ratio = len(set(words)) / len(words) if words else 1.0
        if unique_ratio < PENALTY_THRESHOLD:
            reward *= PENALTY_MULTIPLIER
            breakdown["stuffing_penalty_multiplier"] = PENALTY_MULTIPLIER
            for k in list(breakdown.keys()):
                if k != "stuffing_penalty_multiplier":
                    breakdown[k] = round(breakdown[k] * PENALTY_MULTIPLIER, 4)

        return max(0.01, min(0.99, round(reward, 4))), breakdown

    except KeyError as exc:
        raise RuntimeError(f"Missing mandatory schema key in task definition: {exc}") from exc
