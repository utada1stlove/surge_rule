#!/usr/bin/env python3
"""Render a conservative Markdown subset to LaTeX/PDF without build leftovers."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def escape(value: str) -> str:
    table = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(table.get(char, char) for char in value)


def inline(value: str) -> str:
    value = escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", value)
    value = re.sub(r"`(.+?)`", r"\\texttt{\1}", value)
    return value


def markdown_body(markdown: str) -> str:
    result: list[str] = []
    in_code = False
    in_list = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_list:
                result.append(r"\end{itemize}")
                in_list = False
            result.append(r"\end{verbatim}" if in_code else r"\begin{verbatim}")
            in_code = not in_code
            continue
        if in_code:
            result.append(line)
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if heading:
            if in_list:
                result.append(r"\end{itemize}")
                in_list = False
            command = {1: "section*", 2: "subsection*", 3: "subsubsection*"}[len(heading.group(1))]
            result.append(rf"\{command}{{{inline(heading.group(2))}}}")
        elif bullet:
            if not in_list:
                result.append(r"\begin{itemize}")
                in_list = True
            result.append(rf"\item {inline(bullet.group(1))}")
        else:
            if in_list:
                result.append(r"\end{itemize}")
                in_list = False
            if line:
                result.append(inline(line) + r"\par")
            else:
                result.append(r"\medskip")
    if in_code:
        result.append(r"\end{verbatim}")
    if in_list:
        result.append(r"\end{itemize}")
    return "\n".join(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    if shutil.which("xelatex") is None:
        parser.error("xelatex is required")
    source = args.input.resolve()
    if source.suffix.lower() != ".md":
        parser.error("input must be a Markdown file")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    tex = args.output_directory / f"{stem}.tex"
    pdf = args.output_directory / f"{stem}.pdf"
    body = markdown_body(source.read_text(encoding="utf-8"))
    tex.write_text("\n".join([
        r"\documentclass[11pt,a4paper]{ctexart}",
        r"\usepackage[margin=18mm]{geometry}",
        r"\usepackage{hyperref}",
        r"\setlength{\parindent}{0pt}",
        r"\begin{document}", body, r"\end{document}", "",
    ]), encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="markdown-pdf-") as temporary:
        temp = Path(temporary)
        temp_tex = temp / tex.name
        shutil.copy2(tex, temp_tex)
        command = ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", str(temp), str(temp_tex)]
        for _ in range(2):
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode:
                sys.stderr.write(result.stdout[-6000:])
                return result.returncode
        shutil.copy2(temp / pdf.name, pdf)
    print(pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
