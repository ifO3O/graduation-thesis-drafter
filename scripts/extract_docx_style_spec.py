#!/usr/bin/env python3
"""
Extract a reusable formatting spec from a school thesis DOCX template.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml.ns import qn


CHAPTER_RE = re.compile(r"^\s*第[0-9一二三四五六七八九十百千]+\s*章")
H2_RE = re.compile(r"^\s*\d+\.\d+\s+")
H3_RE = re.compile(r"^\s*\d+\.\d+\.\d+\s+")
TOC_LINE_RE = re.compile(r"\t\d+\s*$")


def to_mm(length_obj: Any) -> float | None:
    try:
        return round(length_obj.mm, 2)
    except Exception:
        return None


def to_pt(length_obj: Any) -> float | None:
    try:
        return round(length_obj.pt, 2)
    except Exception:
        return None


def first_non_empty_run(paragraph) -> Any | None:
    for run in paragraph.runs:
        if run.text and run.text.strip():
            return run
    return None


def style_font_map(style) -> dict[str, str | None]:
    r_pr = getattr(style.element, "rPr", None)
    r_fonts = getattr(r_pr, "rFonts", None) if r_pr is not None else None
    if r_fonts is None:
        return {
            "eastAsia": None,
            "ascii": style.font.name,
            "hAnsi": None,
        }
    return {
        "eastAsia": r_fonts.get(qn("w:eastAsia")),
        "ascii": r_fonts.get(qn("w:ascii")) or style.font.name,
        "hAnsi": r_fonts.get(qn("w:hAnsi")),
    }


def paragraph_signature(paragraph) -> dict[str, Any]:
    style = paragraph.style
    p_fmt = paragraph.paragraph_format

    line_spacing = p_fmt.line_spacing
    if line_spacing is None:
        line_spacing = style.paragraph_format.line_spacing
    if hasattr(line_spacing, "pt"):
        line_spacing_value: float | str | None = round(line_spacing.pt, 2)
    else:
        line_spacing_value = line_spacing

    first_indent = p_fmt.first_line_indent
    if first_indent is None:
        first_indent = style.paragraph_format.first_line_indent

    sample_run = first_non_empty_run(paragraph)
    if sample_run is not None:
        size = sample_run.font.size or style.font.size
        size_pt = round(size.pt, 2) if size is not None else None
        bold = sample_run.bold if sample_run.bold is not None else style.font.bold
    else:
        size_pt = round(style.font.size.pt, 2) if style.font.size is not None else None
        bold = style.font.bold

    return {
        "style_name": style.name,
        "alignment": str(paragraph.alignment or style.paragraph_format.alignment),
        "line_spacing": line_spacing_value,
        "first_line_indent_pt": to_pt(first_indent),
        "font": style_font_map(style),
        "size_pt": size_pt,
        "bold": bold,
    }


def choose_majority_signature(paragraphs: list[Any]) -> dict[str, Any]:
    counts: dict[tuple[str, str, str, str, str, str], int] = defaultdict(int)
    sample_store: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}

    for para in paragraphs:
        sig = paragraph_signature(para)
        key = (
            str(sig["style_name"]),
            str(sig["alignment"]),
            str(sig["line_spacing"]),
            str(sig["first_line_indent_pt"]),
            str(sig["size_pt"]),
            str(sig["bold"]),
        )
        counts[key] += 1
        if key not in sample_store:
            sample_store[key] = sig

    if not counts:
        return {}

    winner = max(counts, key=counts.get)
    result = sample_store[winner]
    result["sample_count"] = counts[winner]
    return result


def detect_style_map(paragraphs: list[Any]) -> dict[str, str | None]:
    chapter_candidates: Counter[str] = Counter()
    h2_candidates: Counter[str] = Counter()
    h3_candidates: Counter[str] = Counter()
    toc_heading_style = None
    abstract_heading_style = None

    for para in paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style_name = para.style.name

        is_toc_entry = bool(TOC_LINE_RE.search(text))

        if CHAPTER_RE.search(text) and not is_toc_entry:
            chapter_candidates[style_name] += 1
        if H3_RE.search(text) and not is_toc_entry:
            h3_candidates[style_name] += 1
        if H2_RE.search(text) and not H3_RE.search(text) and not is_toc_entry:
            h2_candidates[style_name] += 1
        if toc_heading_style is None and ("目录" in text or "目 录" in text):
            toc_heading_style = style_name
        if abstract_heading_style is None and ("摘要" in text.upper() or "ABSTRACT" in text.upper()):
            abstract_heading_style = style_name

    def pick_best_style(candidates: Counter[str]) -> str | None:
        if not candidates:
            return None
        ranked = candidates.most_common()
        for style_name, _ in ranked:
            if not style_name.lower().startswith("toc"):
                return style_name
        return ranked[0][0]

    return {
        "chapter": pick_best_style(chapter_candidates),
        "heading2": pick_best_style(h2_candidates),
        "heading3": pick_best_style(h3_candidates),
        "toc_heading": toc_heading_style,
        "abstract_heading": abstract_heading_style,
    }


def collect_toc_styles(paragraphs: list[Any]) -> list[str]:
    names: Counter[str] = Counter()
    for para in paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if TOC_LINE_RE.search(text):
            names[para.style.name] += 1
    return [name for name, _ in names.most_common()]


def build_page_setup(doc: Document) -> dict[str, Any]:
    if not doc.sections:
        return {}
    first = doc.sections[0]
    return {
        "page_width_mm": to_mm(first.page_width),
        "page_height_mm": to_mm(first.page_height),
        "top_margin_mm": to_mm(first.top_margin),
        "bottom_margin_mm": to_mm(first.bottom_margin),
        "left_margin_mm": to_mm(first.left_margin),
        "right_margin_mm": to_mm(first.right_margin),
        "gutter_mm": to_mm(first.gutter),
        "header_distance_mm": to_mm(first.header_distance),
        "footer_distance_mm": to_mm(first.footer_distance),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract formatting spec from DOCX template.")
    parser.add_argument("--template-docx", required=True, help="Path to school template DOCX")
    parser.add_argument("--output", required=True, help="Output JSON spec path")
    args = parser.parse_args()

    template = Path(args.template_docx).resolve()
    if not template.exists():
        raise SystemExit(f"Template not found: {template}")

    doc = Document(str(template))
    paragraphs = list(doc.paragraphs)
    non_empty = [p for p in paragraphs if p.text.strip()]

    style_map = detect_style_map(non_empty)
    toc_styles = collect_toc_styles(non_empty)

    chapter_paras = [p for p in non_empty if style_map["chapter"] and p.style.name == style_map["chapter"]]
    h2_paras = [p for p in non_empty if style_map["heading2"] and p.style.name == style_map["heading2"]]
    h3_paras = [p for p in non_empty if style_map["heading3"] and p.style.name == style_map["heading3"]]

    body_candidates = []
    for p in non_empty:
        if p.style.name in {style_map["chapter"], style_map["heading2"], style_map["heading3"]}:
            continue
        if TOC_LINE_RE.search(p.text.strip()):
            continue
        # Prefer body-like paragraphs with enough words.
        if len(p.text.strip()) >= 15:
            body_candidates.append(p)

    if not body_candidates:
        body_candidates = non_empty

    spec: dict[str, Any] = {
        "template_file": str(template),
        "page_setup": build_page_setup(doc),
        "style_map": style_map,
        "toc_styles": toc_styles,
        "format_rules": {
            "body": choose_majority_signature(body_candidates),
            "chapter": choose_majority_signature(chapter_paras),
            "heading2": choose_majority_signature(h2_paras),
            "heading3": choose_majority_signature(h3_paras),
        },
        "stats": {
            "paragraph_count": len(paragraphs),
            "non_empty_paragraph_count": len(non_empty),
            "section_count": len(doc.sections),
            "toc_style_count": len(toc_styles),
        },
        "examples": {
            "chapter_samples": [p.text.strip() for p in chapter_paras[:5]],
            "heading2_samples": [p.text.strip() for p in h2_paras[:5]],
            "heading3_samples": [p.text.strip() for p in h3_paras[:5]],
        },
    }

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote template spec to: {output}")
    print(
        "Detected styles: "
        f"chapter={style_map['chapter']}, "
        f"h2={style_map['heading2']}, "
        f"h3={style_map['heading3']}, "
        f"toc_styles={len(toc_styles)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
