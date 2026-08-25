"""
evaluator.py
------------
LLM-as-judge.

Evaluates each rubric checkpoint separately so that smaller local
models such as Gemma 2B can reliably follow the required format.
"""

import json
import re

from rubric import CHECKPOINTS, rubric_as_prompt_block, checkpoint_ids
from llm_client import call_llm


EVALUATOR_SYSTEM_PROMPT = """You are a strict content quality reviewer.

You evaluate a beginner lesson against ONE specific rubric checkpoint.

Rules:
- The checkpoint either PASSES or FAILS.
- No partial credit.
- If you are unsure, mark it as FAIL.
- Base your judgment only on the lesson text.
- Give a short, specific reason.
- Respond with ONLY valid JSON.
- Do not use markdown.
- Do not add any text before or after the JSON.

Your response must have exactly this format:

{
  "pass": true,
  "reason": "Short specific reason"
}

or:

{
  "pass": false,
  "reason": "Short specific reason"
}
"""


def build_prompt(topic: str, lesson: str, checkpoint_id: str) -> str:
    """
    Build a prompt for evaluating one checkpoint at a time.
    """

    return f"""Topic being taught:
{topic}

RUBRIC CHECKPOINTS:
{rubric_as_prompt_block()}

CHECKPOINT TO EVALUATE:
{checkpoint_id}

LESSON TO EVALUATE:
---
{lesson}
---

Evaluate ONLY the checkpoint:

{checkpoint_id}

Return ONLY this JSON structure:

{{
  "pass": true,
  "reason": "one short, specific sentence"
}}

The "pass" value must be either true or false.
"""


def _extract_json(text: str) -> dict:
    """
    Extract JSON from the model response.
    Handles occasional markdown fences or extra text.
    """

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    text = text.strip()

    # Try direct JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the first JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Evaluator did not return valid JSON.\nRaw output:\n{text}"
    )


def evaluate_single_checkpoint(
    topic: str,
    lesson: str,
    checkpoint_id: str
) -> dict:
    """
    Evaluate one checkpoint.
    """

    prompt = build_prompt(
        topic=topic,
        lesson=lesson,
        checkpoint_id=checkpoint_id
    )

    raw = call_llm(
        system=EVALUATOR_SYSTEM_PROMPT,
        user=prompt,
        max_tokens=300
    )

    try:
        result = _extract_json(raw)
    except ValueError as e:
        raise ValueError(
            f"Could not evaluate checkpoint '{checkpoint_id}'.\n"
            f"Raw output:\n{raw}"
        ) from e

    # Make sure the model returned the expected fields
    if "pass" not in result:
        raise ValueError(
            f"Evaluator response for '{checkpoint_id}' "
            f"is missing the 'pass' field.\n"
            f"Raw output:\n{raw}"
        )

    if "reason" not in result:
        result["reason"] = "No reason provided."

    # Force pass to a proper boolean
    value = result["pass"]

    if isinstance(value, str):
        value = value.lower().strip()

        if value == "true":
            result["pass"] = True
        elif value == "false":
            result["pass"] = False
        else:
            result["pass"] = False

    else:
        result["pass"] = bool(value)

    return {
        "pass": result["pass"],
        "reason": str(result["reason"])
    }


def evaluate_lesson(topic: str, lesson: str) -> dict:
    """
    Evaluate the complete lesson against every checkpoint.

    Returns:
      {
        "overall_pass": bool,
        "results": {
            checkpoint_id: {
                "pass": bool,
                "reason": str
            }
        },
        "failed_checks": [...]
      }
    """

    results = {}

    print("\nEvaluating lesson against rubric checkpoints...")

    for checkpoint_id in checkpoint_ids():

        print(f"  Evaluating: {checkpoint_id}")

        try:
            result = evaluate_single_checkpoint(
                topic=topic,
                lesson=lesson,
                checkpoint_id=checkpoint_id
            )

            results[checkpoint_id] = result

            status = "PASS" if result["pass"] else "FAIL"

            print(f"    -> {status}: {result['reason']}")

        except Exception as e:

            # If the small model fails to produce a valid response,
            # treat that checkpoint as failed rather than crashing
            # the entire pipeline.
            print(f"    -> ERROR: {e}")

            results[checkpoint_id] = {
                "pass": False,
                "reason": "Evaluator could not reliably evaluate this checkpoint."
            }

    failed_checks = [
        checkpoint_id
        for checkpoint_id in checkpoint_ids()
        if not results[checkpoint_id]["pass"]
    ]

    overall_pass = len(failed_checks) == 0

    print("\nEvaluation complete.")

    if overall_pass:
        print("Overall result: PASS")
    else:
        print("Overall result: FAIL")
        print("Failed checkpoints:", failed_checks)

    return {
        "overall_pass": overall_pass,
        "results": results,
        "failed_checks": failed_checks,
    }
