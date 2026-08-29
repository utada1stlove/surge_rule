---
name: ocr-document-extract
description: Extract text from images and scanned PDFs with page-level provenance, OCR metadata, and uncertainty markers. Use when a document lacks a reliable text layer or when image text must be archived as Markdown.
---

# OCR Document Extract

Run `scripts/ocr_extract.py INPUT OUTPUT_DIRECTORY [--lang eng]`. It keeps the
original input untouched and writes OCR Markdown plus metadata. For PDFs it
renders each page before OCR; for images it OCRs the source directly.

OCR output is a transcription aid, not a verified fact. Recheck material names,
numbers, dates, currency, legal terms, and identifiers against the original
page. Preserve unreadable sections as uncertainty instead of inventing text.
