"""
main.py
-------
CLI entry point.

Usage:
    python main.py "RAG (Retrieval-Augmented Generation)"

Writes two files to ../outputs/:
    lesson.md          -> the final lesson (passing, or best-effort if it never passed)
    rejection_log.json -> full attempt-by-attempt log: what failed, why, verdict per attempt
"""

import sys
import json
import os

from orchestrator import run_pipeline

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


def main():
    if len(sys.argv) < 2:
        print('Usage: python main.py "<topic>"')
        sys.exit(1)

    topic = sys.argv[1]
    print(f"Generating lesson for topic: {topic}")
    print("Running generate -> evaluate -> regenerate loop...\n")

    result = run_pipeline(topic)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    lesson_path = os.path.join(OUTPUT_DIR, "lesson.md")
    with open(lesson_path, "w") as f:
        f.write(f"# {topic}\n\n{result['final_lesson']}\n")

    log_path = os.path.join(OUTPUT_DIR, "rejection_log.json")
    with open(log_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Verdict: {result['final_verdict']}")
    print(f"Attempts used: {result['attempts_used']}")
    print(f"Lesson written to: {lesson_path}")
    print(f"Rejection log written to: {log_path}")

    if result["standing_warnings_applied"]:
        print("\nApplied learned warnings from past runs:")
        print(result["standing_warnings_applied"])


if __name__ == "__main__":
    main()
