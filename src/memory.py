"""
memory.py
---------
Persistent memory across runs, stored as JSON on disk (swap for a DB
in production — the interface is the same).

Two things are remembered:

1. RUN HISTORY — every run's rejection log, forever. This is the audit
   trail: what topic, what failed, what changed on retry, did it ship.

2. FAILURE PATTERNS — a running tally of which checkpoint IDs fail most
   often, across ALL runs (not just this topic). When a checkpoint has
   failed >= PATTERN_THRESHOLD times historically, its guidance gets
   injected as an extra "watch out for this" instruction into the
   GENERATOR's system prompt on future runs — before evaluation even
   happens. That's the self-evolving loop: the system doesn't just fix
   the current lesson, it gets better at not making the same mistake
   next time, on a different topic.

This is intentionally simple (JSON file, no vector DB) because the
signal we need to persist is small and structured — this isn't a case
where embedding-based retrieval buys anything.
"""

import json
import os
from datetime import datetime, timezone

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
HISTORY_PATH = os.path.join(MEMORY_DIR, "run_history.json")
PATTERNS_PATH = os.path.join(MEMORY_DIR, "failure_patterns.json")

PATTERN_THRESHOLD = 2  # a checkpoint must fail this many times (lifetime) to trigger a standing warning


def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def _save(path, data):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_history():
    return _load(HISTORY_PATH, [])


def load_patterns():
    return _load(PATTERNS_PATH, {})


def record_run(topic: str, rejection_log: list, final_verdict: str, attempts_used: int):
    """Append this run's outcome to permanent history."""
    history = load_history()
    history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "final_verdict": final_verdict,
        "attempts_used": attempts_used,
        "rejection_log": rejection_log,
    })
    _save(HISTORY_PATH, history)

    # Update lifetime failure-pattern tally
    patterns = load_patterns()
    for entry in rejection_log:
        for failed_id in entry.get("failed_checks", []):
            patterns[failed_id] = patterns.get(failed_id, 0) + 1
    _save(PATTERNS_PATH, patterns)


def standing_warnings(rubric_checkpoints) -> str:
    """
    Build a text block of 'watch out for X' warnings for checkpoints
    that have historically failed often across past runs (any topic).
    Injected into the generator's system prompt BEFORE generation,
    so the system tries to avoid known failure modes proactively.
    """
    patterns = load_patterns()
    lookup = {cp["id"]: cp for cp in rubric_checkpoints}
    warnings = []
    for check_id, count in sorted(patterns.items(), key=lambda x: -x[1]):
        if count >= PATTERN_THRESHOLD and check_id in lookup:
            cp = lookup[check_id]
            warnings.append(
                f"- This system has historically failed '{cp['id']}' {count} time(s) across past lessons. "
                f"{cp['guidance']}"
            )
    if not warnings:
        return ""
    return (
        "LEARNED FROM PAST RUNS (avoid repeating these mistakes):\n"
        + "\n".join(warnings)
    )
