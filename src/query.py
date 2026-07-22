# query.py

from embeddings import embed
from vectordb import search
from config import COLLECTION_NAME


def retrieve_context(question: str):
    q_vec = embed([question])[0]
    results = search(COLLECTION_NAME, q_vec)

    context = "\n\n".join(
        f"[SOURCE: {r.payload.get('source')}]\n{r.payload['text']}"
        for r in results[:4]
    )

    return context, results