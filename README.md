# Self-Evaluating Lesson Content Generator

An agentic AI system that generates beginner-friendly lessons, evaluates them against a strict pass/fail rubric, and regenerates the lesson with targeted feedback when evaluation checkpoints fail.

Built for: **GenAI Engineer – Content Systems**

Submission topic: **Introduction to RAG (Retrieval-Augmented Generation)**

The target learner is a student who has just completed 12th grade in India, has a non-English-medium background, and has zero prior AI/ML exposure.

---

## 🚀 Key Features

- Agentic **Generate → Evaluate → Regenerate** workflow
- 7 hard pass/fail evaluation checkpoints
- Checkpoint-by-checkpoint LLM evaluation
- Targeted regeneration based on evaluator feedback
- Local LLM execution using **Ollama**
- **Gemma 2B** model support
- Persistent failure-pattern memory
- Retry budget to prevent infinite loops
- JSON-based run history and rejection logs
- Offline workflow testing without an API key
- Deliberate-error demonstration for evaluator testing

---

## 🧠 Agentic Workflow

The system follows an iterative generate-evaluate-regenerate loop:

```text
                    User Topic
                        │
                        ▼
                ┌───────────────┐
                │    Generator  │
                └───────┬───────┘
                        │
                        ▼
                  Generated Lesson
                        │
                        ▼
                ┌───────────────┐
                │   Evaluator   │
                └───────┬───────┘
                        │
                7 Rubric Checks
                        │
                        ▼
                  All Passed?
                   /       \
                 YES        NO
                  │          │
                  ▼          ▼
            Final Lesson   Feedback
                              │
                              ▼
                         Regenerate
                              │
                              └──────► Evaluate Again


🤖 LLM Configuration

The project uses:

Ollama for local LLM execution
Gemma 2B as the language model

This removes the need for Anthropic API credits and allows the project to run locally.

🔍 Evaluator Design

The evaluator checks the generated lesson against 7 strict checkpoints.

Instead of asking a lightweight model such as Gemma 2B to return all seven evaluations in one large JSON response, the evaluator checks one checkpoint at a time.

Python then combines all checkpoint results to determine the overall verdict.

This approach improves structured-output reliability with smaller local models.

📋 The 7 Rubric Checkpoints
Checkpoint	What it checks
grounded_accurate	No factual errors about how RAG works
beginner_language	Accessible to a limited-English, non-technical reader
no_unexplained_jargon	Technical terms are explained on first use
teaches_by_example	Contains at least one concrete example or analogy
covers_key_points	Covers what RAG is, why it matters, retrieval, generation, and a use case
coherent_flow	Logical order with no contradictions
standalone	Can be understood without external resources

🔄 Targeted Regeneration

When the evaluator identifies failed checkpoints, the failed checkpoint IDs and evaluator reasons are passed back to the generator.

The generator receives:

Previous lesson
Failed checkpoint(s)
Evaluator feedback
Original topic

🧠 Persistent Failure-Pattern Memory

The system maintains lightweight JSON-based memory.

It records:

memory/run_history.json
memory/failure_patterns.json

📁 Project Structure
rag-lesson-generator/
│
├── src/
│   ├── main.py
│   ├── orchestrator.py
│   ├── generator.py
│   ├── evaluator.py
│   ├── rubric.py
│   ├── memory.py
│   ├── llm_client.py
│   └── test_orchestrator_offline.py
│
├── outputs/
│   ├── lesson.md
│   └── rejection_log.json
│
├── memory/
│   ├── run_history.json
│   └── failure_patterns.json
│
├── requirements.txt
└── README.md

File Responsibilities
File	Purpose
main.py	CLI entry point
orchestrator.py	Controls generate → evaluate → regenerate workflow
generator.py	Generates and regenerates lessons
evaluator.py	Evaluates each rubric checkpoint
rubric.py	Defines the 7 evaluation checkpoints
memory.py	Maintains persistent run/failure information
llm_client.py	Connects the application to Ollama
test_orchestrator_offline.py	Tests workflow logic using mocked LLM responses
