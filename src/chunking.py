import re
from transformers import AutoTokenizer
from config import CHUNK_SIZE, CHUNK_OVERLAP_SENTENCE, EMBEDDING_MODEL

# Load only the tokenizer (not model weights) — uses the locally-cached files.
# No network calls are made when HF_HUB_OFFLINE=1 is set.
_tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)


def _count_tokens(text: str) -> int:
    """Count the number of tokens the embedding model would produce for `text`."""
    return len(_tokenizer.encode(text, add_special_tokens=False))


def split_sentences(text: str) -> list:
    """Split text into sentences, ignoring common abbreviations."""
    raw_splits = re.split(r'(?<=[.!?])\s+', text.strip())

    abbreviations = {
        "e.g.", "i.e.", "vs.", "mr.", "mrs.", "dr.", "st.", "co.", "corp.", "inc.",
        "ltd.", "jan.", "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.",
        "oct.", "nov.", "dec.", "a.m.", "p.m.", "al.", "etc.", "u.s.",
    }

    sentences = []
    temp = []

    for part in raw_splits:
        temp.append(part)
        words = part.split()
        if not words:
            continue
        last_word = words[-1].lower().rstrip(".,!?") + "."
        # Skip if it looks like an abbreviation or single-letter initial (e.g. "A.")
        is_abbrev = (last_word in abbreviations) or (
            len(last_word) == 2 and last_word[0].isalpha() and last_word[1] == "."
        )
        if not is_abbrev:
            sentences.append(" ".join(temp))
            temp = []

    if temp:
        sentences.append(" ".join(temp))

    return [s for s in sentences if s.strip()]


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap_sentences=CHUNK_OVERLAP_SENTENCE):
    """
    Split `text` into token-bounded chunks that respect sentence boundaries.

    Strategy:
    - Sentences are accumulated until the next one would push the chunk over
      `chunk_size` tokens (as counted by the embedding model's own tokenizer).
    - The last `overlap_sentences` sentences from the completed chunk are carried
      forward to seed the next one, giving continuity across chunk boundaries.
    - Single sentences that individually exceed `chunk_size` tokens are hard-split
      on token boundaries with a small token overlap (12.5% of chunk_size).
    """
    sentences = split_sentences(text)

    chunks = []
    current_sentences = []
    current_token_count = 0

    for sentence in sentences:
        sentence_tokens = _count_tokens(sentence)

        # --- Hard-split oversized single sentences ---
        if sentence_tokens > chunk_size:
            # Flush current buffer first
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_token_count = 0

            token_ids = _tokenizer.encode(sentence, add_special_tokens=False)
            overlap_tokens = max(1, chunk_size // 8)  # 12.5% token overlap
            start = 0
            while start < len(token_ids):
                end = min(start + chunk_size, len(token_ids))
                piece = _tokenizer.decode(token_ids[start:end], skip_special_tokens=True)
                chunks.append(piece.strip())
                if end == len(token_ids):
                    break
                start += chunk_size - overlap_tokens
            continue

        # --- Normal accumulation ---
        if current_sentences and current_token_count + sentence_tokens > chunk_size:
            chunks.append(" ".join(current_sentences))

            # Carry last N sentences as overlap into the next chunk
            overlap = current_sentences[-overlap_sentences:] if overlap_sentences else []
            current_sentences = overlap
            current_token_count = sum(_count_tokens(s) for s in current_sentences)

        current_sentences.append(sentence)
        current_token_count += sentence_tokens

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks