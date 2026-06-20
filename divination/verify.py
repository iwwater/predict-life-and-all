"""Verification and accuracy scoring framework for divination engines.

Enables:
- Accuracy scoring against known facts
- Regression testing for engine changes
- Profession fit validation
- Element balance calibration

Usage:
    from divination.verify import score_accuracy, run_calibration
    result = score_accuracy(chart, known_facts)
"""


# ── Known Test Cases ────────────────────────────────────────────────────────
# Format: {name, birth, known_facts, expected_*}
# These are used for calibration and regression testing.

TEST_CASES = [
    {
        "id": "case_01",
        "name": "Test: 1990-05-15 08:30",
        "birth": {
            "year": 1990, "month": 5, "day": 15, "hour": 8, "minute": 30,
            "gender": "male", "calendar": "gregorian",
        },
        "known_facts": {
            "day_master": "庚",
            "expected_strength": "中和偏弱",  # Based on 庚午 辛巳 庚辰 庚辰
            "expected_elements": {"metal": 4.2, "wood": 0.4, "water": 0.2, "fire": 3.4, "earth": 3.7},
            "expected_pattern": "印格",  # 月令巳火，透辛金，巳藏丙戊庚，透庚 — 偏印格
            "known_career": None,  # unknown for this test
        },
    },
    {
        "id": "case_02",
        "name": "Mao Zedong",
        "birth": {
            "year": 1893, "month": 12, "day": 26, "hour": 7, "minute": 0,
            "gender": "male", "calendar": "gregorian",
        },
        "known_facts": {
            "day_master": "甲",
            "known_career": "politics_law",
            "known_traits": ["领导力", "战略思维", "文学才华"],
        },
    },
    {
        "id": "case_03",
        "name": "Steve Jobs",
        "birth": {
            "year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15,
            "gender": "male", "calendar": "gregorian",
        },
        "known_facts": {
            "known_career": "creative_arts",
            "known_traits": ["创造力", "完美主义", "远见"],
        },
    },
    {
        "id": "case_04",
        "name": "Albert Einstein",
        "birth": {
            "year": 1879, "month": 3, "day": 14, "hour": 11, "minute": 30,
            "gender": "male", "calendar": "gregorian",
        },
        "known_facts": {
            "known_career": "education_academia",
            "known_traits": ["天才思维", "独立研究", "反传统"],
        },
    },
    {
        "id": "case_05",
        "name": "Oprah Winfrey",
        "birth": {
            "year": 1954, "month": 1, "day": 29, "hour": 4, "minute": 30,
            "gender": "female", "calendar": "gregorian",
        },
        "known_facts": {
            "known_career": "media_entertainment",
            "known_traits": ["沟通力", "感染力", "慈善"],
        },
    },
]


def score_accuracy(chart, known_facts: dict) -> dict:
    """Score chart accuracy against known facts.

    Args:
        chart: ChartResult from any engine
        known_facts: Dict of known facts about the person

    Returns:
        {total_score, checks: [{name, passed, score, detail}]}
    """
    checks = []
    raw = chart.raw or {}
    elements = chart.normalized.get("elements", {})

    # Check 1: Day master correctness
    if "day_master" in known_facts:
        actual_dm = raw.get("day_master", "")
        expected_dm = known_facts["day_master"]
        passed = actual_dm == expected_dm
        checks.append({
            "name": "日主正确性",
            "passed": passed,
            "score": 10 if passed else 0,
            "detail": f"Expected {expected_dm}, got {actual_dm}",
        })

    # Check 2: Element values within tolerance
    if "expected_elements" in known_facts:
        expected = known_facts["expected_elements"]
        total_diff = 0
        detail_parts = []
        for key, exp_val in expected.items():
            actual_val = elements.get(key, 0)
            diff = abs(exp_val - actual_val)
            total_diff += diff
            if diff > 0.2:
                detail_parts.append(f"{key}: exp {exp_val}, got {actual_val} (diff {diff:.2f})")
        # Score based on total difference
        max_tolerance = len(expected) * 0.5
        elem_score = max(0, 15 * (1 - total_diff / max(max_tolerance, 1)))
        checks.append({
            "name": "五行数值准确性",
            "passed": total_diff < 1.0,
            "score": round(elem_score, 1),
            "detail": "; ".join(detail_parts) if detail_parts else "All within tolerance",
        })

    # Check 3: Pattern classification
    if "expected_pattern" in known_facts:
        pattern_data = raw.get("pattern", {})
        actual_pattern = pattern_data.get("pattern", "")
        expected = known_facts["expected_pattern"]
        # Check if the expected pattern is one of the sub-patterns or primary
        sub_patterns = pattern_data.get("sub_patterns", [])
        matches = actual_pattern == expected or expected in sub_patterns
        checks.append({
            "name": "格局分类",
            "passed": matches,
            "score": 15 if matches else 0,
            "detail": f"Expected {expected}, got {actual_pattern} (sub: {sub_patterns})",
        })

    # Check 4: Profession match
    if "known_career" in known_facts:
        try:
            from .knowledge.professions import match_professions
            fits = match_professions(chart, top_n=10)
            fit_ids = [f["profession_id"] for f in fits]
            rank = fit_ids.index(known_facts["known_career"]) if known_facts["known_career"] in fit_ids else -1
            if rank == 0:
                prof_score = 20
            elif 1 <= rank <= 2:
                prof_score = 15
            elif 3 <= rank <= 5:
                prof_score = 10
            elif rank > 5:
                prof_score = 5
            else:
                prof_score = 0
            checks.append({
                "name": "职业匹配度",
                "passed": rank >= 0,
                "score": prof_score,
                "detail": f"Career '{known_facts['known_career']}' ranked #{rank + 1}" if rank >= 0 else "Not found in top 10",
            })
        except Exception as e:
            checks.append({
                "name": "职业匹配度",
                "passed": False,
                "score": 0,
                "detail": f"Error: {e!s}",
            })

    # Check 5: Strength score reasonableness
    strength = raw.get("strength_score")
    if strength is not None:
        checks.append({
            "name": "身强评分合理性",
            "passed": 0 <= strength <= 100,
            "score": 5 if (10 <= strength <= 90) else 3,
            "detail": f"Strength score: {strength}/100",
        })

    total = sum(c["score"] for c in checks)
    max_possible = sum(
        10 if c["name"] == "日主正确性" else
        15 if c["name"] in ("五行数值准确性", "格局分类") else
        20 if c["name"] == "职业匹配度" else
        5
        for c in checks
    )

    return {
        "total_score": round(total, 1),
        "max_score": max_possible,
        "percentage": round(total / max(max_possible, 1) * 100, 1),
        "checks": checks,
        "method": chart.method,
        "engine": chart.engine,
    }


def run_calibration(test_id: str | None = None) -> list[dict]:
    """Run calibration tests against known cases.

    Args:
        test_id: Optional specific test case ID to run

    Returns:
        List of calibration results
    """
    from .contracts import Birth
    from .router import compute

    cases = TEST_CASES
    if test_id:
        cases = [c for c in TEST_CASES if c["id"] == test_id]

    results = []
    for case in cases:
        b = Birth(**case["birth"])
        try:
            # Test v2 first, fall back to v1
            try:
                chart = compute("bazi_v2", b)
            except Exception:
                chart = compute("bazi", b)

            accuracy = score_accuracy(chart, case["known_facts"])
            results.append({
                "case_id": case["id"],
                "name": case["name"],
                "method": chart.method,
                "engine": chart.engine,
                "accuracy": accuracy,
            })
        except Exception as e:
            results.append({
                "case_id": case["id"],
                "name": case["name"],
                "error": str(e),
            })

    return results


def print_calibration_report():
    """Print a formatted calibration report to stdout."""
    results = run_calibration()

    print("=" * 70)
    print("  Mystic Hub Engine Calibration Report")
    print("=" * 70)

    total_score = 0
    total_max = 0
    for r in results:
        if "error" in r:
            print(f"\n  [{r['case_id']}] {r['name']}")
            print(f"    ❌ Error: {r['error']}")
            continue

        acc = r["accuracy"]
        print(f"\n  [{r['case_id']}] {r['name']}")
        print(f"    Method: {r['method']} | Engine: {r['engine']}")
        print(f"    Score: {acc['percentage']}% ({acc['total_score']}/{acc['max_score']})")
        for check in acc["checks"]:
            icon = "✓" if check["passed"] else "✗"
            print(f"    {icon} {check['name']}: {check['score']} pts — {check['detail'][:80]}")
        total_score += acc["total_score"]
        total_max += acc["max_score"]

    if total_max > 0:
        overall = round(total_score / total_max * 100, 1)
        print(f"\n  {'─' * 60}")
        print(f"  Overall: {overall}% ({total_score}/{total_max})")
        print("=" * 70)

    return results


if __name__ == "__main__":
    print_calibration_report()
