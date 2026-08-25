"""
orchestrator.py
----------------
The generate -> evaluate -> regenerate loop.

Termination guarantee: MAX_RETRIES caps the number of regeneration
attempts. If the lesson still fails after MAX_RETRIES, the loop stops
anyway and returns the BEST attempt seen (fewest failed checkpoints),
clearly flagged as "did not pass" rather than silently shipping a
failing lesson or looping forever.
"""

from datetime import datetime, timezone

from generator import generate_lesson
from evaluator import evaluate_lesson
from rubric import CHECKPOINTS, RUBRIC_VERSION
import memory

MAX_RETRIES = 2  # total attempts = 1 initial + MAX_RETRIES retries


def run_pipeline(topic: str) -> dict:
    warnings_block = memory.standing_warnings(CHECKPOINTS)

    attempts = []
    lesson = None
    retry_feedback = None
    previous_lesson = None
    final_result = None

    for attempt_num in range(1, MAX_RETRIES + 2):  # e.g. 1, 2, 3 for MAX_RETRIES=2
        lesson = generate_lesson(
            topic=topic,
            standing_warnings=warnings_block,
            retry_feedback=retry_feedback,
            previous_lesson=previous_lesson,
        )
        eval_result = evaluate_lesson(topic, lesson)

        attempt_record = {
            "attempt": attempt_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lesson": lesson,
            "eval_results": eval_result["results"],
            "failed_checks": eval_result["failed_checks"],
            "overall_pass": eval_result["overall_pass"],
        }
        attempts.append(attempt_record)

        if eval_result["overall_pass"]:
            final_result = attempt_record
            break

        # Build targeted feedback for the next attempt
        retry_feedback = "\n".join(
            f"- [{cid}] {eval_result['results'][cid]['reason']}"
            for cid in eval_result["failed_checks"]
        )
        previous_lesson = lesson

    if final_result is None:
        # Never passed within the attempt budget -> ship the least-bad attempt, flagged.
        final_result = min(attempts, key=lambda a: len(a["failed_checks"]))
        shipped_without_passing = True
    else:
        shipped_without_passing = False

    rejection_log = _build_rejection_log(attempts)

    memory.record_run(
        topic=topic,
        rejection_log=rejection_log,
        final_verdict="PASS" if not shipped_without_passing else "FAILED_AFTER_MAX_RETRIES",
        attempts_used=len(attempts),
    )

    return {
        "topic": topic,
        "rubric_version": RUBRIC_VERSION,
        "final_lesson": final_result["lesson"],
        "final_verdict": "PASS" if not shipped_without_passing else "FAILED_AFTER_MAX_RETRIES",
        "attempts_used": len(attempts),
        "rejection_log": rejection_log,
        "standing_warnings_applied": warnings_block,
    }


def _build_rejection_log(attempts):
    """
    Human-readable log: for every FAILED attempt, what failed, why, and
    (implicitly, via the next attempt's diff) what changed. The final
    passing attempt is included too, marked PASS, for a complete audit trail.
    """
    log = []
    for a in attempts:
        log.append({
            "attempt": a["attempt"],
            "verdict": "PASS" if a["overall_pass"] else "FAIL",
            "failed_checks": a["failed_checks"],
            "reasons": {
                cid: a["eval_results"][cid]["reason"]
                for cid in a["failed_checks"]
            },
        })
    return log
