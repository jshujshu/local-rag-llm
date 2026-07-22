# ingest.py

import os
import uuid
from embeddings import embed
from chunking import chunk_text
from vectordb import create_collection, upsert, client
from config import COLLECTION_NAME, VECTOR_SIZE, DATA_DIR

# Security: skip files larger than this to prevent OOM during ingestion.
# Override with MAX_INGEST_FILE_SIZE env var (bytes).
MAX_INGEST_FILE_SIZE = int(os.getenv("MAX_INGEST_FILE_SIZE", str(10 * 1024 * 1024)))  # 10 MB default

def hash_text(text: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, text))


# load markdown from /data
def load_all_markdown_files(root_dir):
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".md"):
                full_path = os.path.join(dirpath, file)
                file_size = os.path.getsize(full_path)
                if file_size > MAX_INGEST_FILE_SIZE:
                    print(
                        f"[ingest] Skipping {full_path}: "
                        f"file size {file_size:,} bytes exceeds limit "
                        f"{MAX_INGEST_FILE_SIZE:,} bytes."
                    )
                    continue
                with open(full_path, "r", encoding="utf-8") as f:
                    files.append((full_path, f.read()))
    return files


# get chunk IDs from qdrant
def get_existing_ids(collection_name):
    try:
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=100000,
            with_payload=False,
            with_vectors=False
        )
        return set(p.id for p in points)
    except Exception:
        return set()


# main ingest
def run():
    create_collection(COLLECTION_NAME, VECTOR_SIZE)
    files = load_all_markdown_files(DATA_DIR)
    existing_ids = get_existing_ids(COLLECTION_NAME)
    new_chunks = []
    new_ids = []
    new_payloads = []
    for path, text in files:
        chunks = chunk_text(text)
        # Generate relative path with forward slashes for cross-platform consistency
        rel_path = os.path.relpath(path, DATA_DIR).replace("\\", "/")
        for chunk in chunks:
            chunk_id = hash_text(rel_path + ":" + chunk)
            if chunk_id in existing_ids:
                continue  # skips chunks already ingested
            new_chunks.append(chunk)
            new_ids.append(chunk_id)
            new_payloads.append({
                "text": chunk,
                "source": rel_path
            })
    if not new_chunks:
        print("No new changes detected. Nothing to ingest.")
        return 0, len(files)
    vectors = embed(new_chunks)
    upsert(
        COLLECTION_NAME,
        ids=new_ids,
        vectors=vectors,
        payloads=new_payloads
    )
    print(f"Ingested {len(new_chunks)} new chunks from {len(files)} files")
    return len(new_chunks), len(files)


if __name__ == "__main__":
    run()

