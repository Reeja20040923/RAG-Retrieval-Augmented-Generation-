"""
generator.py
------------
Generates a beginner lesson. On retries, receives the specific
rejection reasons from the evaluator and is instructed to fix exactly
those, not to rewrite from scratch — this keeps regeneration targeted
instead of a random re-roll that might fix one thing and break another.
"""

from llm_client import call_llm

GENERATOR_SYSTEM_PROMPT = """You are a patient, encouraging teacher writing a first lesson for a
learner who just finished 12th grade in India, is not from an English-medium school, has a
limited English vocabulary, and has never studied AI, machine learning, or programming before.
This is likely their very first exposure to this topic.

Rules for how you write:
- Use short, simple sentences. Avoid complex grammar.
- Every technical term must be explained in plain words the moment it first appears.
- Use at least one everyday analogy or concrete example (something from daily life in India
  is great, e.g. a library, a shopkeeper, an exam, a recipe book).
- Cover, in order: what the topic is, why it matters, how it works step by step, and one
  real use case.
- Do not assume the reader knows any prior AI/ML concept.
- Be factually accurate. Do not invent details.
- Keep it self-contained: someone should finish reading and understand the topic without
  needing to look anything else up.
"""


def build_prompt(topic: str, standing_warnings: str = "", retry_feedback: str | None = None,
                  previous_lesson: str | None = None) -> str:
    parts = [f"Write a beginner lesson on: {topic}"]

    if standing_warnings:
        parts.append("\n" + standing_warnings)

    if retry_feedback and previous_lesson:
        parts.append(
            "\nA previous draft of this lesson FAILED review. Here is that draft:\n"
            f"---\n{previous_lesson}\n---\n"
            "Here is exactly what failed and why:\n"
            f"{retry_feedback}\n"
            "Rewrite the lesson to fix these specific problems. Keep what already worked; "
            "do not introduce new issues."
        )

    return "\n".join(parts)


def generate_lesson(topic: str, standing_warnings: str = "", retry_feedback: str | None = None,
                     previous_lesson: str | None = None) -> str:
    prompt = build_prompt(topic, standing_warnings, retry_feedback, previous_lesson)
    return call_llm(system=GENERATOR_SYSTEM_PROMPT, user=prompt, max_tokens=1500)
