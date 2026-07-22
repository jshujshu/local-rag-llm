import os
from config import LLM_MODELS, DEFAULT_MODEL

def resolve_model(name: str | None) -> str:
    """
    Request model key -> local path (if exists under snapshots/) or HF repo ID.
    Fallback to default if not specified in request.
    """
    name = name or DEFAULT_MODEL

    if name not in LLM_MODELS:
        raise ValueError(f"Unknown model: {name}")

    # Check if a local snapshot directory exists for this model key
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(base_dir, "snapshots", name)
    if os.path.isdir(local_path):
        print(f"Resolved model key '{name}' to local path: {local_path}")
        return local_path

    return LLM_MODELS[name]