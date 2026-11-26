"""Generate a clean, portfolio-ready PDF report from eval/evaluated_results.jsonl.

Uses PyMuPDF (fitz), which is already installed in this project's environment.
Run with:
    uv run python scripts/generate_eval_report_pdf.py
"""

from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "eval" / "evaluated_results_RAG2.jsonl"
OUTPUT_PDF = PROJECT_ROOT / "eval" / "RAG2_evaluation_report.pdf"
THRESHOLD = 0.70

# Colors (RGB 0..1)
NAVY = (0.10, 0.18, 0.32)
SLATE = (0.30, 0.35, 0.42)
LIGHT_BG = (0.95, 0.96, 0.98)
BORDER = (0.82, 0.85, 0.90)
GREEN = (0.09, 0.50, 0.24)
GREEN_BG = (0.89, 0.97, 0.91)
RED = (0.72, 0.14, 0.14)
RED_BG = (0.99, 0.90, 0.90)
WHITE = (1.0, 1.0, 1.0)
BLACK = (0.12, 0.12, 0.14)


def safe_text(text: str) -> str:
    """Normalize smart punctuation so built-in Helvetica renders cleanly."""
    replacements = {
        "\u2013": "-",
        "\u2014": " - ",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2011": "-",
        "\u2022": "*",
        "\u00a0": " ",
        "\u202f": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def load_results(path: Path) -> list[dict]:
    items: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def build_pdf(results: list[dict], output_path: Path) -> None:
    doc = fitz.open()
    page_w, page_h = 595.0, 842.0  # A4
    margin_x = 42.0
    content_w = page_w - 2 * margin_x

    page = doc.new_page(width=page_w, height=page_h)
    y = 40.0

    def new_page_if_needed(needed_height: float) -> None:
        nonlocal page, y
        if y + needed_height > page_h - 45.0:
            page = doc.new_page(width=page_w, height=page_h)
            y = 45.0

    # --- Header Banner ---
    banner_rect = fitz.Rect(margin_x, y, page_w - margin_x, y + 72)
    page.draw_rect(banner_rect, color=NAVY, fill=NAVY)
    page.insert_text(
        (margin_x + 16, y + 28),
        "Healthcare RAG Evaluation Report - RAG2 Improved",
        fontsize=15.5,
        fontname="hebo",
        color=WHITE,
    )
    subtitle = (
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
        f"Test Cases: {len(results)}  |  Threshold: {THRESHOLD:.2f}  |  "
        "Chatbot: Ollama qwen2.5:7b  |  Judge: Groq qwen/qwen3.8-27b"
    )
    page.insert_text(
        (margin_x + 16, y + 50),
        safe_text(subtitle),
        fontsize=8.5,
        fontname="helv",
        color=(0.85, 0.90, 0.97),
    )
    y += 90.0

    # --- Aggregate Metrics Summary ---
    page.insert_text(
        (margin_x, y),
        "1. Aggregate Metrics Summary",
        fontsize=12.5,
        fontname="hebo",
        color=NAVY,
    )
    y += 14.0

    metric_specs = [
        ("Answer Relevancy", "answer_relevancy"),
        ("Faithfulness", "faithfulness"),
        ("Contextual Relevancy", "context_relevancy"),
        ("Correctness [GEval]", "correctness"),
    ]

    # Table Header
    col_x = [margin_x, margin_x + 190, margin_x + 290, margin_x + 415]
    row_h = 22.0
    page.draw_rect(
        fitz.Rect(margin_x, y, page_w - margin_x, y + row_h),
        color=BORDER,
        fill=LIGHT_BG,
    )
    headers = ["Metric", "Average Score", "Pass Rate (>= 0.70)", "Status"]
    for cx, h in zip(col_x, headers):
        page.insert_text((cx + 8, y + 15), h, fontsize=9.5, fontname="hebo", color=NAVY)
    y += row_h

    for label, key in metric_specs:
        vals = [r[key] for r in results if isinstance(r.get(key), (int, float))]
        avg = sum(vals) / len(vals) if vals else 0.0
        passed = sum(1 for v in vals if v >= THRESHOLD)
        total = len(vals)
        pct = (passed / total * 100.0) if total else 0.0
        ok = avg >= THRESHOLD

        page.draw_rect(
            fitz.Rect(margin_x, y, page_w - margin_x, y + row_h),
            color=BORDER,
            fill=WHITE,
        )
        page.insert_text((col_x[0] + 8, y + 15), label, fontsize=9.5, fontname="helv", color=BLACK)
        page.insert_text(
            (col_x[1] + 8, y + 15), f"{avg:.2f}", fontsize=9.5, fontname="hebo", color=BLACK
        )
        page.insert_text(
            (col_x[2] + 8, y + 15),
            f"{pct:.1f}% ({passed}/{total} passed)",
            fontsize=9.5,
            fontname="helv",
            color=SLATE,
        )

        # Status Pill
        pill_rect = fitz.Rect(col_x[3] + 8, y + 4, col_x[3] + 68, y + row_h - 4)
        page.draw_rect(
            pill_rect,
            color=GREEN if ok else RED,
            fill=GREEN_BG if ok else RED_BG,
        )
        page.insert_text(
            (col_x[3] + 22, y + 14.5),
            "PASS" if ok else "FAIL",
            fontsize=8.5,
            fontname="hebo",
            color=GREEN if ok else RED,
        )
        y += row_h

    y += 18.0

    # --- Key Diagnostic Insights ---
    page.insert_text(
        (margin_x, y),
        "2. Key Diagnostic Insights (RAG2 Improved)",
        fontsize=12.5,
        fontname="hebo",
        color=NAVY,
    )
    y += 14.0

    insights = [
        "Faithfulness (1.00 / 100% pass): Zero hallucinations across all 10 test cases; strict grounding prompt + qwen2.5:7b kept every answer faithful to the leaflets.",
        "Correctness [GEval] (0.87 / 90% pass): Major jump from RAG1 (0.57 -> 0.87) with 9/10 passing; upgrading the generator and rubric captured full clinical accuracy.",
        "Answer Relevancy (0.89 / 70% pass): Strong direct answers across 9 scored cases (Test 7 returned N/A due to one invalid-JSON judge response).",
        "Contextual Relevancy (0.44 / 20% pass): Loosening MAX_SCORE_GAP to 0.12 allowed secondary chunks into the context; tightening to k=1 per tool call is the next retrieval optimization.",
    ]
    box_top = y
    wrapped_insights: list[str] = []
    for bullet in insights:
        lines = textwrap.wrap(safe_text(f"- {bullet}"), width=94)
        wrapped_insights.extend(lines)
    box_h = len(wrapped_insights) * 12.5 + 16
    page.draw_rect(
        fitz.Rect(margin_x, box_top, page_w - margin_x, box_top + box_h),
        color=BORDER,
        fill=LIGHT_BG,
    )
    ty = box_top + 15
    for line in wrapped_insights:
        page.insert_text((margin_x + 10, ty), line, fontsize=8.8, fontname="helv", color=BLACK)
        ty += 12.5
    y = box_top + box_h + 18.0

    # --- Per-Test Score Summary Table ---
    new_page_if_needed(90.0)
    page.insert_text(
        (margin_x, y),
        "3. Per-Test Score Overview",
        fontsize=12.5,
        fontname="hebo",
        color=NAVY,
    )
    y += 14.0

    t_cols = [margin_x, margin_x + 28, margin_x + 315, margin_x + 365, margin_x + 415, margin_x + 465]
    page.draw_rect(
        fitz.Rect(margin_x, y, page_w - margin_x, y + 20),
        color=BORDER,
        fill=LIGHT_BG,
    )
    for cx, h in zip(t_cols, ["#", "Question", "AnsRel", "Faith", "CtxRel", "Corr"]):
        page.insert_text((cx + 5, y + 14), h, fontsize=8.8, fontname="hebo", color=NAVY)
    y += 20.0

    for idx, r in enumerate(results, start=1):
        q_short = safe_text(r["question"])
        if len(q_short) > 64:
            q_short = q_short[:61] + "..."
        new_page_if_needed(20.0)
        page.draw_rect(
            fitz.Rect(margin_x, y, page_w - margin_x, y + 19),
            color=BORDER,
            fill=WHITE if idx % 2 == 1 else (0.98, 0.99, 1.0),
        )
        page.insert_text((t_cols[0] + 5, y + 13), str(idx), fontsize=8.5, fontname="hebo", color=SLATE)
        page.insert_text((t_cols[1] + 5, y + 13), q_short, fontsize=8.2, fontname="helv", color=BLACK)

        for cx, key in zip(
            t_cols[2:],
            ["answer_relevancy", "faithfulness", "context_relevancy", "correctness"],
        ):
            val = r.get(key)
            txt = f"{val:.2f}" if isinstance(val, (int, float)) else "N/A"
            col = GREEN if isinstance(val, (int, float)) and val >= THRESHOLD else RED
            page.insert_text((cx + 6, y + 13), txt, fontsize=8.5, fontname="hebo", color=col)
        y += 19.0

    # --- Detailed Per-Test Q&A Breakdown ---
    page = doc.new_page(width=page_w, height=page_h)
    y = 45.0
    page.insert_text(
        (margin_x, y),
        "4. Detailed Per-Test Outputs & Scores",
        fontsize=12.5,
        fontname="hebo",
        color=NAVY,
    )
    y += 18.0

    for idx, r in enumerate(results, start=1):
        q_lines = textwrap.wrap(safe_text(f"Test {idx}: {r['question']}"), width=88)
        actual_lines = textwrap.wrap(
            safe_text(f"Actual Output: {r['actual_answer'].replace(chr(10), ' ')}"), width=94
        )
        expected_lines = textwrap.wrap(
            safe_text(f"Expected Output: {r['expected_answer']}"), width=94
        )

        fmt = lambda v: f"{v:.2f}" if isinstance(v, (int, float)) else "N/A"
        scores_line = (
            f"Answer Relevancy: {fmt(r.get('answer_relevancy'))}   |   "
            f"Faithfulness: {fmt(r.get('faithfulness'))}   |   "
            f"Contextual Relevancy: {fmt(r.get('context_relevancy'))}   |   "
            f"Correctness: {fmt(r.get('correctness'))}"
        )

        block_h = (len(q_lines) * 13) + (len(actual_lines) * 11) + (len(expected_lines) * 11) + 42
        new_page_if_needed(block_h)

        # Card header bar
        hdr_h = len(q_lines) * 13 + 8
        page.draw_rect(
            fitz.Rect(margin_x, y, page_w - margin_x, y + hdr_h),
            color=BORDER,
            fill=LIGHT_BG,
        )
        cy = y + 13
        for line in q_lines:
            page.insert_text((margin_x + 8, cy), line, fontsize=9.2, fontname="hebo", color=NAVY)
            cy += 13
        y += hdr_h + 12

        # Scores strip
        page.insert_text((margin_x + 8, y), scores_line, fontsize=8.5, fontname="hebo", color=SLATE)
        y += 14

        for line in actual_lines:
            new_page_if_needed(14)
            page.insert_text((margin_x + 8, y), line, fontsize=8.2, fontname="helv", color=BLACK)
            y += 11

        y += 4
        for line in expected_lines:
            new_page_if_needed(14)
            page.insert_text((margin_x + 8, y), line, fontsize=8.2, fontname="helv", color=SLATE)
            y += 11

        y += 12

    # Page numbers footer
    for pno, p in enumerate(doc, start=1):
        p.insert_text(
            (page_w - margin_x - 55, page_h - 22),
            f"Page {pno} of {len(doc)}",
            fontsize=8.0,
            fontname="helv",
            color=SLATE,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    print(f"PDF report saved to: {output_path}")


if __name__ == "__main__":
    data = load_results(INPUT_PATH)
    build_pdf(data, OUTPUT_PDF)
