"""
rubric.py
---------
Defines the evaluation rubric as a set of HARD pass/fail checkpoints.

Design principle: every checkpoint must be answerable with a binary
yes/no by an evaluator (LLM-as-judge) looking ONLY at the lesson text.
No "rate 1-5", no partial credit. This is deliberate — partial-credit
rubrics let mediocre content slide through by averaging. A hard gate
forces every dimension to actually be satisfied.

Each checkpoint has:
  - id: stable key used in logs / memory
  - description: what the evaluator is checking
  - guidance: extra instruction to reduce evaluator ambiguity
  - critical: if True, failing this check alone fails the whole lesson
              (all checks here are critical by design, but the flag
              exists so the rubric can evolve to have soft checks later)
"""

RUBRIC_VERSION = 1

CHECKPOINTS = [
    {
        "id": "grounded_accurate",
        "description": "Every factual claim about RAG is technically accurate and not misleading.",
        "guidance": (
            "Fail if the lesson misstates how retrieval-augmented generation works "
            "(e.g. confuses it with fine-tuning, claims it 'trains' the model, "
            "gets the retrieve-then-generate order wrong, or invents features)."
        ),
        "critical": True,
    },
    {
        "id": "beginner_language",
        "description": "Language is accessible to a 12th-grade graduate with limited English vocabulary and no prior AI/ML background.",
        "guidance": (
            "Fail if sentences are long/complex, if uncommon English words are used "
            "without simpler alternatives, or if the tone assumes a technical or "
            "native-English-speaking reader."
        ),
        "critical": True,
    },
    {
        "id": "no_unexplained_jargon",
        "description": "Every technical term used is defined in plain language the first time it appears.",
        "guidance": (
            "Fail if terms like 'embedding', 'vector', 'retrieval', 'LLM', 'corpus', "
            "'semantic search', 'hallucination', etc. appear without an immediate, "
            "simple explanation in the same or next sentence."
        ),
        "critical": True,
    },
    {
        "id": "teaches_by_example",
        "description": "The lesson includes at least one concrete, relatable example or analogy that illustrates the concept.",
        "guidance": (
            "Fail if the lesson is purely abstract/definitional with no worked example, "
            "story, or analogy a beginner can hold onto."
        ),
        "critical": True,
    },
    {
        "id": "covers_key_points",
        "description": (
            "The lesson covers all of: (1) what RAG is, (2) why it matters / what problem it solves, "
            "(3) the retrieval step, (4) the generation step, (5) at least one real use case."
        ),
        "guidance": "Fail if any of the five required points is missing or only vaguely implied.",
        "critical": True,
    },
    {
        "id": "coherent_flow",
        "description": "The lesson has a logical teaching order and no internal contradictions.",
        "guidance": (
            "Fail if ideas are introduced before they're explained, if the lesson "
            "contradicts itself, or if it jumps between ideas without transitions."
        ),
        "critical": True,
    },
    {
        "id": "standalone",
        "description": "A learner with zero background can finish the lesson and understand the topic without needing outside resources.",
        "guidance": (
            "Fail if the lesson assumes prior knowledge of ML/AI concepts it doesn't itself explain, "
            "or references external material as a prerequisite."
        ),
        "critical": True,
    },
]


def rubric_as_prompt_block() -> str:
    """Render the rubric as a numbered block to inject into the evaluator prompt."""
    lines = []
    for i, cp in enumerate(CHECKPOINTS, 1):
        lines.append(
            f"{i}. [{cp['id']}] {cp['description']}\n   Guidance: {cp['guidance']}"
        )
    return "\n".join(lines)


def checkpoint_ids():
    return [cp["id"] for cp in CHECKPOINTS]
