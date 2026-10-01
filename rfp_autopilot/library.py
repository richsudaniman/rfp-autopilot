"""Load the library of approved, previously-used answers."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REQUIRED_COLUMNS = {"id", "question", "answer"}


@dataclass(frozen=True)
class ApprovedAnswer:
    id: str
    question: str
    answer: str
    category: str = ""
    source: str = ""  # where this answer was approved (doc name, SOC 2 report, etc.)
    aliases: tuple[str, ...] = ()  # other ways buyers have asked the same question

    @property
    def phrasings(self) -> tuple[str, ...]:
        return (self.question, *self.aliases)


def load_library(path: str | Path) -> list[ApprovedAnswer]:
    """Read a CSV with columns: id, question, answer[, aliases, category, source].

    ``aliases`` is an optional pipe-separated list of alternate phrasings.
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
        entries = [
            ApprovedAnswer(
                id=row["id"].strip(),
                question=row["question"].strip(),
                answer=row["answer"].strip(),
                category=(row.get("category") or "").strip(),
                source=(row.get("source") or "").strip(),
                aliases=tuple(a.strip() for a in (row.get("aliases") or "").split("|") if a.strip()),
            )
            for row in reader
            if (row.get("question") or "").strip() and (row.get("answer") or "").strip()
        ]
    if not entries:
        raise ValueError(f"{path} contains no usable answers")
    ids = [e.id for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} contains duplicate ids")
    return entries
