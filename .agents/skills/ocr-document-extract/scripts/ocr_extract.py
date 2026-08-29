#!/usr/bin/env python3
"""OCR images and scanned PDFs into traceable Markdown using local tools."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp"}


def run_tesseract(image: Path, language: str) -> str:
    result = subprocess.run(["tesseract", str(image), "stdout", "-l", language], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "tesseract failed")
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--lang", default="eng", help="Tesseract language pack, for example eng or chi_sim")
    args = parser.parse_args()
    source = args.input.resolve()
    if not source.is_file():
        parser.error(f"input does not exist: {source}")
    if shutil.which("tesseract") is None:
        parser.error("tesseract is required")
    languages = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, check=False).stdout.splitlines()[1:]
    if args.lang not in languages:
        parser.error(f"Tesseract language pack '{args.lang}' is unavailable; installed: {', '.join(languages) or 'none'}")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    pages: list[tuple[str, str]] = []
    if source.suffix.lower() == ".pdf":
        if shutil.which("pdftoppm") is None:
            parser.error("pdftoppm is required for PDF OCR")
        with tempfile.TemporaryDirectory(prefix="ocr-pages-") as temporary:
            prefix = Path(temporary) / "page"
            result = subprocess.run(["pdftoppm", "-r", "300", "-png", str(source), str(prefix)], capture_output=True, text=True, check=False)
            if result.returncode:
                sys.stderr.write(result.stderr)
                return result.returncode
            for page in sorted(Path(temporary).glob("page-*.png")):
                pages.append((page.name, run_tesseract(page, args.lang)))
    elif source.suffix.lower() in IMAGE_SUFFIXES:
        pages.append((source.name, run_tesseract(source, args.lang)))
    else:
        parser.error("supported inputs: PDF, PNG, JPG, TIFF, WEBP, BMP")

    stem = source.stem
    markdown = args.output_directory / f"{stem}.ocr.md"
    metadata = args.output_directory / f"{stem}.ocr.json"
    lines = [f"# OCR: {source.name}", "", f"- Original file: `{source.name}`", f"- OCR engine: Tesseract ({args.lang})", f"- Extracted at: {datetime.now(timezone.utc).isoformat()}", "- Verification: OCR is unverified; check material values against the original page.", ""]
    for index, (page_name, text) in enumerate(pages, start=1):
        lines.extend([f"## Page {index}: {page_name}", "", text or "[No readable text extracted]", ""])
    markdown.write_text("\n".join(lines), encoding="utf-8")
    metadata.write_text(json.dumps({"input": str(source), "language": args.lang, "pages": len(pages), "extracted_at": datetime.now(timezone.utc).isoformat(), "markdown": markdown.name}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
