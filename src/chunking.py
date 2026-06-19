# chunking.py

def chunk_text(text, chunk_size=800, overlap=150):
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) > chunk_size and current:
            chunks.append(current.strip())
            current = current[-overlap:] + "\n\n" + p
        else:
            current += "\n\n" + p
    if current:
        chunks.append(current.strip())

    return chunks

