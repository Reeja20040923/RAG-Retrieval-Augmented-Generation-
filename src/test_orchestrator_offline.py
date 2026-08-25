"""
test_orchestrator_offline.py
-----------------------------
Sanity-checks the orchestrator's control flow (loop, retry feedback,
termination, memory writes) WITHOUT calling a real LLM. Useful for CI
and for verifying logic in a network-restricted sandbox.

It monkeypatches llm_client.call_llm with a scripted fake that:
  - on the generator call: returns a canned "bad" lesson on attempt 1
    (missing an example) and a canned "good" lesson on attempt 2
  - on the evaluator call: returns JSON that fails 'teaches_by_example'
    for the bad lesson and passes everything for the good lesson
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import llm_client
from rubric import checkpoint_ids

CALLS = {"count": 0}


def fake_call_llm(system: str, user: str, max_tokens: int = 1500) -> str:
    CALLS["count"] += 1
    is_evaluator = "RUBRIC CHECKPOINTS" in user

    if is_evaluator:
        bad = "MISSING_EXAMPLE_DRAFT" in user
        results = {}
        for cid in checkpoint_ids():
            if bad and cid == "teaches_by_example":
                results[cid] = {"pass": False, "reason": "No concrete example or analogy given."}
            else:
                results[cid] = {"pass": True, "reason": "Meets the requirement."}
        return json.dumps(results)
    else:
        # Generator call
        if "A previous draft of this lesson FAILED review" in user:
            return "GOOD_DRAFT: RAG explained simply, with a library-and-librarian analogy included."
        else:
            return "MISSING_EXAMPLE_DRAFT: RAG explained simply but with no example at all."


def main():
    llm_client.call_llm = fake_call_llm

    from orchestrator import run_pipeline

    result = run_pipeline("RAG (Retrieval-Augmented Generation) [OFFLINE TEST]")

    print("=== OFFLINE TEST RESULT ===")
    print("Verdict:", result["final_verdict"])
    print("Attempts used:", result["attempts_used"])
    print("Total LLM calls made:", CALLS["count"])
    print("\nRejection log:")
    print(json.dumps(result["rejection_log"], indent=2))

    assert result["final_verdict"] == "PASS", "Expected the loop to recover on retry and pass"
    assert result["attempts_used"] == 2, "Expected exactly 2 attempts: fail then pass"
    assert result["rejection_log"][0]["failed_checks"] == ["teaches_by_example"]
    assert result["rejection_log"][1]["verdict"] == "PASS"
    print("\nAll assertions passed. Orchestrator loop logic is correct.")


if __name__ == "__main__":
    main()
