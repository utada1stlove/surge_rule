---
name: markdown-pdf
description: Render Markdown or LaTeX documents to checked PDFs while preserving requested source files and removing TeX intermediates. Use when a task needs a PDF report, handout, or reproducible document export.
---

# Markdown PDF

Prefer `scripts/render_markdown_pdf.py input.md output-directory` for ordinary
Markdown. It emits `.tex` and `.pdf`, compiles in a temporary directory, and
does not leave compiler artifacts in the output directory.

For custom LaTeX, compile twice, inspect page count and extracted text, then run
`safe-file-cleanup` in the output directory. Preserve only requested source,
PDF, and data files. Do not claim a PDF is delivered until it opens and its
expected title or key text is extractable.
