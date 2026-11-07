from dataclasses import dataclass

CHUNK_SIZE = 400    # tokens (approximated as whitespace-split words)
OVERLAP = 60


@dataclass
class TextChunk:
    text: str
    page_start: int
    page_end: int


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_pages(pages: list[tuple[int, str]]) -> list[TextChunk]:
    """
    pages: list of (page_number, text) tuples in order.
    Returns overlapping chunks of ~CHUNK_SIZE words, each carrying the
    page range it spans.
    """
    # Build a flat list of (word, page_number) pairs
    word_pages: list[tuple[str, int]] = []
    for page_num, text in pages:
        for word in text.split():
            word_pages.append((word, page_num))

    if not word_pages:
        return []

    chunks: list[TextChunk] = []
    start = 0
    total = len(word_pages)

    while start < total:
        end = min(start + CHUNK_SIZE, total)
        slice_ = word_pages[start:end]
        chunk_text = " ".join(w for w, _ in slice_)
        page_start = slice_[0][1]
        page_end = slice_[-1][1]
        chunks.append(TextChunk(text=chunk_text, page_start=page_start, page_end=page_end))
        step = CHUNK_SIZE - OVERLAP
        start += step

    return chunks
