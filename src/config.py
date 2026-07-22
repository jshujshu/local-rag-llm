# config.py

import os
import torch

EMBEDDING_MODEL = "ibm-granite/granite-embedding-small-english-r2"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# CHUNK_SIZE is in TOKENS (not characters), matched to the embedding model's tokenizer.
# Granite small supports up to 512 tokens; 384 leaves a safe buffer.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "384"))
CHUNK_OVERLAP_SENTENCE = int(os.getenv("CHUNK_OVERLAP_SENTENCE", "2"))

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "markdown_docs")
VECTOR_SIZE = 384   # Granite small embedding size

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

LLM_MODELS = {
    # "qwen2.5i-coder-3b": "Qwen/Qwen2.5-Coder-3B-Instruct",
    "qwen2.5i-coder-1.5b": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    "qwen2.5i-coder-0.5b": "Qwen/Qwen2.5-Coder-0.5B-Instruct",
    
    # "qwen2.5i-3b": "Qwen/Qwen2.5-3B-Instruct",
    
    # "qwen3i-4b": "Qwen/Qwen3-4B-Instruct-2507",
    
    "qwen3.5-4b-uncensored-4bit": "HauhauCS/Qwen3.5-4B-Uncensored-HauhauCS-Aggressive"
}

# Mapping of model keys to their quantization settings (if they should be loaded in 4-bit)
QUANTIZED_MODELS = {
    "qwen3.5-4b-uncensored-4bit": True
}

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5-4b-uncensored-4bit")

DATA_DIR = os.getenv("DATA_DIR", "data")

MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "10000"))

# Automatically unload model after 300 seconds (5 minutes) of inactivity
LLM_IDLE_TIMEOUT = int(os.getenv("LLM_IDLE_TIMEOUT", "300"))
