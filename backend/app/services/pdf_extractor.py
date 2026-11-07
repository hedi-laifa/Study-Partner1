from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

LOW_TEXT_THRESHOLD = 50  # characters per page below which a page is flagged


@dataclass
class PageText:
    page_number: int  # 0-indexed
    text: str
    low_text: bool


def extract_pages(pdf_path: Path) -> list[PageText]:
    """Return per-page text from a PDF, flagging low-text pages."""
    results: list[PageText] = []
    with fitz.open(str(pdf_path)) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text")
            results.append(PageText(
                page_number=i,
                text=text,
                low_text=len(text.strip()) < LOW_TEXT_THRESHOLD,
            ))
    return results
