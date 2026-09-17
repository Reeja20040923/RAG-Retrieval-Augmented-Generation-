"""
llm_client.py
-------------
Single choke point for all LLM calls.

Uses Ollama to run the LLM locally.
No Anthropic API key or cloud credits are required.
"""

import os
import ollama

# Ollama model
MODEL = os.environ.get("LLM_MODEL", "gemma:2b")


def call_llm(system: str, user: str, max_tokens: int = 1500) -> str:
    """Calls the local Ollama LLM and returns the response text."""

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system
                },
                {
                    "role": "user",
                    "content": user
                }
            ],
        )

        return response["message"]["content"]

    except Exception as e:
        raise RuntimeError(
            f"Failed to call Ollama. Make sure Ollama is running "
            f"and the model '{MODEL}' is installed.\n\n"
            f"Original error: {e}"
        ) from e
