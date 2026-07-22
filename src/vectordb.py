# vectordb.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from typing import List, Dict, Any, Optional
from config import QDRANT_HOST, QDRANT_PORT

# connect qdrant
client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT,
    prefer_grpc=False
)

# collection manager
def create_collection(name: str, vector_size: int) -> None:
    """
    Create collection ONLY if it doesn't already exist.
    """
    existing = client.get_collections().collections
    existing_names = [c.name for c in existing]

    if name in existing_names:
        print(f"Collection '{name}' already exists. Skipping creation.")
        return

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )


# insert + update vectors
def upsert(
    collection: str,
    ids: List[int],
    vectors: List[List[float]],
    payloads: List[Dict[str, Any]]
) -> None:
    """
    Insert or update vectors in the collection.
    Each payload typically contains {"text": "...", "metadata": {...}}
    """
    points = [
        {
            "id": _id,
            "vector": vector,
            "payload": payload
        }
        for _id, vector, payload in zip(ids, vectors, payloads)
    ]

    client.upsert(
        collection_name=collection,
        points=points
    )


# search
def search(
    collection: str,
    query_vector: List[float],
    top_k: int = 5,
    filter: Optional[Any] = None
):
    result = client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=top_k,
        query_filter=filter,
        with_payload=True
    )

    return result.points

