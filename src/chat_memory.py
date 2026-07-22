import os
import json
from collections import deque, OrderedDict

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Security: cap total in-memory sessions to prevent RAM exhaustion from
# session-ID flooding. FIFO eviction drops the oldest session.
# Override with MAX_SESSIONS env var.
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "1000"))

# session_id -> deque (in-memory cache, ordered for FIFO eviction)
memory: OrderedDict = OrderedDict()


def get_session_file(session_id: str) -> str:
    # Sanitize session_id to prevent path traversal
    safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
    return os.path.join(STORAGE_DIR, f"{safe_id}.json")


def _evict_if_needed() -> None:
    """Drop oldest session(s) from the in-memory cache if we hit MAX_SESSIONS."""
    while len(memory) >= MAX_SESSIONS:
        oldest_key, _ = memory.popitem(last=False)
        print(f"[chat_memory] Session cap reached ({MAX_SESSIONS}). Evicted oldest session: {oldest_key}")


def load_session(session_id: str) -> deque:
    if session_id in memory:
        # Move to end to mark as recently used
        memory.move_to_end(session_id)
        return memory[session_id]

    session_file = get_session_file(session_id)
    history = []
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            print(f"Error loading session {session_id} from file: {e}")

    _evict_if_needed()
    d = deque(history, maxlen=10)
    memory[session_id] = d
    return d


def add_message(session_id: str, role: str, content: str):
    d = load_session(session_id)
    d.append({
        "role": role,
        "content": content
    })

    # Persist to disk
    session_file = get_session_file(session_id)
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(list(d), f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving session {session_id} to file: {e}")


def get_history(session_id: str):
    return list(load_session(session_id))


def clear_session(session_id: str):
    if session_id in memory:
        memory[session_id].clear()
        del memory[session_id]
    session_file = get_session_file(session_id)
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            print(f"Deleted history file for session {session_id}")
        except Exception as e:
            print(f"Error deleting session file {session_file}: {e}")


