#!/usr/bin/env python3
"""Capture simple static web pages into Markdown with provenance metadata."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "div", "section", "article", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._in_title:
            self.title += data
        self.parts.append(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    request = Request(args.url, headers={"User-Agent": "Mozilla/5.0 (compatible; universal-agent-kit/1.0)"})
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(charset, errors="replace")
        content_type = response.headers.get_content_type()
    extractor = TextExtractor()
    extractor.feed(html)
    text = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", "".join(extractor.parts))).strip()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^a-zA-Z0-9]+", "-", extractor.title.strip() or "webpage").strip("-").lower()[:80] or "webpage"
    markdown = args.output_directory / f"{stem}.md"
    metadata = args.output_directory / f"{stem}.capture.json"
    retrieved = datetime.now(timezone.utc).isoformat()
    markdown.write_text(f"# {extractor.title.strip() or 'Web capture'}\n\n- Source: {args.url}\n- Retrieved at: {retrieved}\n- Content type: {content_type}\n\n{text}\n", encoding="utf-8")
    metadata.write_text(json.dumps({"url": args.url, "retrieved_at": retrieved, "title": extractor.title.strip(), "content_type": content_type, "markdown": markdown.name}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
