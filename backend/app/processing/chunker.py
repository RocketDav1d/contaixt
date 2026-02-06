"""
Deterministic text chunker with overlap.
Splits on sentence boundaries where possible, falls back to hard split.
"""

import re
import uuid
from dataclasses import dataclass

# Approximate 200–400 tokens per chunk (~4 chars/token)
CHUNK_SIZE = 1200  # characters
# 10–15% overlap for evidence chunks
CHUNK_OVERLAP = 150

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    idx: int
    text: str
    start_offset: int
    end_offset: int


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[Chunk]:
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [Chunk(idx=0, text=text, start_offset=0, end_offset=len(text))]

    sentences = SENTENCE_SPLIT.split(text)

    chunks: list[Chunk] = []
    current = ""
    current_start = 0
    pos = 0

    for sentence in sentences:
        # Find actual position of this sentence in original text
        sent_start = text.find(sentence, pos)
        if sent_start == -1:
            sent_start = pos
        sent_end = sent_start + len(sentence)

        if current and len(current) + len(sentence) + 1 > chunk_size:
            chunks.append(Chunk(
                idx=len(chunks),
                text=current.strip(),
                start_offset=current_start,
                end_offset=current_start + len(current.strip()),
            ))
            # Overlap: walk back to find overlap start
            overlap_text = current[-overlap:] if len(current) > overlap else current
            current_start = current_start + len(current) - len(overlap_text)
            current = overlap_text.lstrip() + " " + sentence
        else:
            if not current:
                current_start = sent_start
                current = sentence
            else:
                current = current + " " + sentence

        pos = sent_end

    if current.strip():
        chunks.append(Chunk(
            idx=len(chunks),
            text=current.strip(),
            start_offset=current_start,
            end_offset=current_start + len(current.strip()),
        ))

    return chunks
