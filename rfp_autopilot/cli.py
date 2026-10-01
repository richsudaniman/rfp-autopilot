"""Command-line entry point.

    python -m rfp_autopilot questionnaire.xlsx --library data/answer_library.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .drafter import ExtractiveDrafter, LLMDrafter, default_drafter
from .library import load_library
from .pipeline import STATUS_SME, Thresholds, process_workbook
from .retriever import Retriever


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Draft answers to a security questionnaire / RFP from approved past answers.")
    p.add_argument("questionnaire", type=Path, help="Input .xlsx with a 'Question' column")
    p.add_argument("--library", type=Path, default=Path("data/answer_library.csv"), help="CSV of approved answers")
    p.add_argument("-o", "--output", type=Path, help="Output .xlsx (default: <input>_answered.xlsx)")
    p.add_argument("--sheet", help="Worksheet name (default: first sheet)")
    p.add_argument("--header-row", type=int, default=1)
    p.add_argument("--min-match", type=float, default=Thresholds.min_match,
                   help="Below this similarity the question is flagged for SME review instead of drafted")
    p.add_argument("--high", type=float, default=Thresholds.high, help="Similarity needed for High confidence")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true", help="Reuse best approved answer verbatim (no LLM)")
    mode.add_argument("--llm", action="store_true", help="Force LLM drafting (needs ANTHROPIC_API_KEY)")
    args = p.parse_args(argv)

    output = args.output or args.questionnaire.with_name(f"{args.questionnaire.stem}_answered.xlsx")
    drafter = ExtractiveDrafter() if args.offline else LLMDrafter() if args.llm else default_drafter()

    library = load_library(args.library)
    report = process_workbook(
        args.questionnaire, output, Retriever(library), drafter,
        Thresholds(min_match=args.min_match, high=args.high),
        sheet=args.sheet, header_row=args.header_row,
    )

    print(f"Library: {len(library)} approved answers | Drafter: {type(drafter).__name__}")
    print(report.summary())
    flagged = [r for r in report.results if r.status == STATUS_SME]
    if flagged:
        print("\nFlagged for SME review:")
        for r in flagged:
            print(f"  row {r.row}: {r.question}")
    print(f"\nSaved -> {output}")
    return 0
