import sqlite3
import statistics
from collections import defaultdict
from typing import Iterable, Any

def letter_point(score: float) -> float:
    """Map numeric score to grade points (adjust to your school scale if needed)."""
    if score is None:
        return 0.0
    try:
        s = float(score)
    except Exception:
        return 0.0
    if s >= 70: return 4.0
    if s >= 60: return 3.5
    if s >= 50: return 3.0
    if s >= 45: return 2.5
    if s >= 40: return 2.0
    return 0.0

def _pick_value(mapping: dict, candidates: Iterable[str]):
    """Return first present value from mapping for a list of candidate keys (case-insensitive)."""
    # direct check first
    for k in candidates:
        if k in mapping and mapping[k] is not None:
            return mapping[k]
    # case-insensitive fallback
    low = {k.lower(): k for k in mapping.keys()}
    for cand in candidates:
        c = cand.lower()
        if c in low:
            return mapping[low[c]]
    return None

def _normalize_scores_rows(rows: Iterable[Any]):
    """
    Normalize DB rows to dicts with keys: code, units, component, score.
    Accepts: list of dicts, sqlite3.Row, or tuples (heuristic).
    """
    normalized = []
    for r in rows:
        if r is None:
            continue

        # dict-like (or sqlite3.Row which is mapping-like)
        if isinstance(r, dict) or isinstance(r, sqlite3.Row):
            rd = dict(r)
        elif isinstance(r, (list, tuple)):
            # Heuristics for tuple shapes:
            # Common useful shapes:
            # 1) (code, title, units, component, score, created_at)
            # 2) (code, units, component, score)
            # 3) (component, score, code, title, units)
            # We'll try a few likely patterns; if none match we fill best-effort.
            rd = {}
            if len(r) >= 5:
                rd['code'] = r[0]
                rd['title'] = r[1]
                rd['units'] = r[2]
                rd['component'] = r[3]
                rd['score'] = r[4]
            elif len(r) == 4:
                rd['code'] = r[0]
                rd['units'] = r[1]
                rd['component'] = r[2]
                rd['score'] = r[3]
            elif len(r) == 3:
                rd['component'] = r[0]
                rd['score'] = r[1]
                rd['code'] = r[2]
            else:
                # fallback: map index-> generic names
                for i, val in enumerate(r):
                    rd[f'col{i}'] = val
        else:
            # unknown row type — skip
            continue

        # now pick normalized fields from rd using many candidate names
        code = _pick_value(rd, ["code", "Course Code", "course_code", "c.code"])
        units = _pick_value(rd, ["units", "Course Units", "course_units", "c.units", "units"])
        component = _pick_value(rd, ["component", "Component", "comp"])
        score = _pick_value(rd, ["score", "Score", "value", "s.score"])

        # normalize types
        try:
            if units is None:
                units_num = 0
            else:
                units_num = int(float(units))
        except Exception:
            units_num = 0

        try:
            score_num = None if score is None else float(score)
        except Exception:
            score_num = None

        normalized.append({
            "code": code,
            "units": units_num,
            "component": (component.lower() if isinstance(component, str) else None),
            "score": score_num
        })

    return normalized

def current_gpa(scores_rows: Iterable[Any]) -> float:
    """
    Compute current GPA from rows that include course code, units, component, and score.
    Accepts rows returned by your get_scores (or other shapes) — it's robust.
    """
    rows = _normalize_scores_rows(scores_rows)

    # group by course code, and collect component lists
    per_course = defaultdict(lambda: defaultdict(list))  # per_course[code][component] = [scores]
    units_map = {}

    for r in rows:
        code = r.get("code") or "__unknown__"
        comp = r.get("component") or "other"
        per_course[code][comp].append(r.get("score"))
        # keep last nonzero units encountered
        if r.get("units"):
            units_map[code] = int(r.get("units"))

    total_points = 0.0
    total_units = 0

    for code, comps in per_course.items():
        # exam average (if any)
        exam_list = [s for s in comps.get("exam", []) if s is not None]
        exam_avg = statistics.mean(exam_list) if exam_list else None

        # CA = everything that is not exam
        ca_list = []
        for k, vals in comps.items():
            if k != "exam":
                ca_list.extend([s for s in vals if s is not None])
        ca_avg = statistics.mean(ca_list) if ca_list else None

        # decide final numeric score for course
        if exam_avg is None and ca_avg is None:
            # nothing to compute
            continue
        if exam_avg is None:
            final = ca_avg
        elif ca_avg is None:
            final = exam_avg
        else:
            final = 0.6 * exam_avg + 0.4 * ca_avg

        gp = letter_point(final)
        u = units_map.get(code, 0) or 0
        total_points += gp * u
        total_units += u

    return round(total_points / total_units, 2) if total_units else 0.0

def projected_gpa(scores_rows: Iterable[Any]) -> float:
    """
    Placeholder projected GPA. For now it mirrors current_gpa.
    You can later implement projection logic (e.g., assume pending exams = current CA avg).
    """
    return current_gpa(scores_rows)


# ------- Example quick test (run in python REPL) -------
# sample = [
#     {"Course Code": "CSC101", "Course Units": 3, "Component": "test", "Score": 15},
#     {"Course Code": "CSC101", "Course Units": 3, "Component": "exam", "Score": 65},
#     {"code": "CSC102", "units": 2, "component": "assignment", "score": 12},
#     ("CSC103","Data Structures",3,"exam", 70)
# ]
# print(projected_gpa(sample))
