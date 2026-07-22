# embeddings.py

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, DEVICE

model = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

def embed(texts):
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()

