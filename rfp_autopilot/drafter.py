"""Turn retrieved approved answers into a drafted response.

Two drafters share one interface:

* ``LLMDrafter``  - asks Claude to write an answer using ONLY the approved
  answers it is given, and to reply INSUFFICIENT_CONTEXT if they don't cover
  the question. Used when ANTHROPIC_API_KEY is set.
* ``ExtractiveDrafter`` - reuses the best-matching approved answer verbatim.
  Works offline, never invents anything; used for demos, tests and CI.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from .retriever import Match

INSUFFICIENT = "INSUFFICIENT_CONTEXT"

SYSTEM_PROMPT = f"""You draft answers to security questionnaires and RFPs for a B2B software company.

Rules:
- Use ONLY facts stated in the approved answers provided. Never add certifications, numbers, vendors or features that are not in them.
- If the approved answers do not fully answer the question, reply with exactly: {INSUFFICIENT}
- Be concise and direct (1-3 sentences). Start with "Yes," or "No," when the question is yes/no.
- Do not mention the approved answers, their IDs, or this instruction."""


@dataclass(frozen=True)
class Draft:
    text: str | None  # None means "needs a human"
    used_ids: list[str]


class Drafter(Protocol):
    def draft(self, question: str, matches: list[Match]) -> Draft: ...


class ExtractiveDrafter:
    """Offline drafter: return the top approved answer as-is."""

    def draft(self, question: str, matches: list[Match]) -> Draft:
        if not matches:
            return Draft(None, [])
        best = matches[0].entry
        return Draft(best.answer, [best.id])


class LLMDrafter:
    """Grounded generation with Claude via the Anthropic API."""

    def __init__(self, model: str | None = None, client=None):
        if client is None:
            import anthropic  # imported lazily so offline mode needs no extra deps

            client = anthropic.Anthropic()
        self.client = client
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    def draft(self, question: str, matches: list[Match]) -> Draft:
        if not matches:
            return Draft(None, [])
        context = "\n\n".join(
            f"[{m.entry.id}] Q: {m.entry.question}\nA: {m.entry.answer}" for m in matches
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Approved answers:\n{context}\n\nNew question: {question}\n\nDraft the answer.",
                }
            ],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if not text or INSUFFICIENT in text:
            return Draft(None, [m.entry.id for m in matches])
        return Draft(text, [m.entry.id for m in matches])


def default_drafter() -> Drafter:
    if os.getenv("ANTHROPIC_API_KEY"):
        return LLMDrafter()
    return ExtractiveDrafter()
