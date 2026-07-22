# api.py

import os
import requests
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid
from query import retrieve_context
from prompt import build_prompt
from llm import generate_stream
from chat_memory import add_message, get_history, clear_session
from models import resolve_model
from config import LLM_MODELS, DEFAULT_MODEL, QDRANT_HOST, QDRANT_PORT

# ---------------------------------------------------------------------------
# Rate limiter — keyed by client IP (Fix: DoS prevention on /chat)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — restricted to explicit origins only (Fix: wildcard CORS)
# Override via env: ALLOWED_ORIGINS=http://host1,http://host2
# ---------------------------------------------------------------------------
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000"
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# Request schema — with field length limits (Fix: payload size validation)
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4096)
    session_id: str | None = Field(None, max_length=64)
    model: str | None = Field(None, max_length=64)
    use_rag: bool = True


@app.post("/chat")
@limiter.limit("10/minute")
async def chat(req: ChatRequest, request: Request):
    session_id = req.session_id or str(uuid.uuid4())

    # Fix: return clean 422 instead of leaking 500 traceback on unknown model
    try:
        model_name = resolve_model(req.model)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    add_message(session_id, "user", req.question)
    if req.use_rag:
        context, _ = retrieve_context(req.question)
    else:
        context = ""
    history = get_history(session_id)
    messages = build_prompt(context, history, req.use_rag)

    def stream():
        response_text = ""
        for token in generate_stream(messages, model_name):
            if not token:
                continue
            response_text += token
            yield token
        add_message(session_id, "assistant", response_text)
    return StreamingResponse(stream(), media_type="text/plain")


@app.get("/history/{session_id}")
def history(session_id: str):
    return get_history(session_id)


@app.delete("/history/{session_id}")
def clear_history(session_id: str):
    clear_session(session_id)
    return {"status": "cleared"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/models")
def get_models():
    return {
        "models": list(LLM_MODELS.keys()),
        "default": DEFAULT_MODEL
    }


@app.get("/")
def ui():
    return FileResponse("chat-ui.html")


@app.get("/marked.min.js")
def get_marked():
    return FileResponse("marked.min.js")


@app.get("/dashboard")
def qdrant_redirect():
    """Convenience redirect so /dashboard goes to the dashboard/."""
    return RedirectResponse(url="/dashboard/")


# ---------------------------------------------------------------------------
# Qdrant proxy — read-only by default (Fix: unauthenticated admin mutation)
#
# Write methods (POST/PUT/DELETE) are blocked unless QDRANT_PROXY_WRITE=1
# is set in the environment. The dashboard only needs GET for display.
# ---------------------------------------------------------------------------
QDRANT_ENDPOINTS = ["collections", "aliases", "telemetry", "cluster", "locks", "snapshots", "version"]
_PROXY_WRITE_ENABLED = os.getenv("QDRANT_PROXY_WRITE", "0") == "1"
_PROXY_READ_METHODS = {"GET", "HEAD", "OPTIONS"}


def _filter_headers(headers):
    ignored = {"host", "content-encoding", "content-length"}
    return {
        k: v for k, v in headers.items()
        if k.lower() not in ignored and not k.lower().startswith("access-control-")
    }


def _proxy_request(qdrant_url: str, request: Request, body: bytes) -> Response:
    """Forward a request to Qdrant, enforcing write restrictions."""
    if request.method.upper() not in _PROXY_READ_METHODS and not _PROXY_WRITE_ENABLED:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Qdrant proxy: write method {request.method!r} is disabled. "
                "Set QDRANT_PROXY_WRITE=1 to allow mutations."
            )
        )
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "accept-encoding")
    }
    res = requests.request(
        method=request.method,
        url=qdrant_url,
        params=dict(request.query_params),
        data=body,
        headers=headers,
        timeout=30
    )
    return Response(content=res.content, status_code=res.status_code, headers=_filter_headers(res.headers))


def register_proxy_routes(app: FastAPI):
    for endpoint in QDRANT_ENDPOINTS:
        # Root-level endpoint proxy
        @app.api_route(f"/{endpoint}", methods=["GET", "POST", "PUT", "DELETE"], name=f"proxy_{endpoint}_base")
        async def proxy_base(request: Request, ep=endpoint):
            body = await request.body()
            return _proxy_request(f"http://{QDRANT_HOST}:{QDRANT_PORT}/{ep}", request, body)

        # Root-level path proxy
        @app.api_route(f"/{endpoint}/{{path:path}}", methods=["GET", "POST", "PUT", "DELETE"], name=f"proxy_{endpoint}_path")
        async def proxy_path(path: str, request: Request, ep=endpoint):
            body = await request.body()
            return _proxy_request(f"http://{QDRANT_HOST}:{QDRANT_PORT}/{ep}/{path}", request, body)

        # Dashboard-prefixed relative endpoint proxy
        @app.api_route(f"/dashboard/{endpoint}", methods=["GET", "POST", "PUT", "DELETE"], name=f"proxy_db_{endpoint}_base")
        async def proxy_db_base(request: Request, ep=endpoint):
            body = await request.body()
            return _proxy_request(f"http://{QDRANT_HOST}:{QDRANT_PORT}/{ep}", request, body)

        # Dashboard-prefixed relative path proxy
        @app.api_route(f"/dashboard/{endpoint}/{{path:path}}", methods=["GET", "POST", "PUT", "DELETE"], name=f"proxy_db_{endpoint}_path")
        async def proxy_db_path(path: str, request: Request, ep=endpoint):
            body = await request.body()
            return _proxy_request(f"http://{QDRANT_HOST}:{QDRANT_PORT}/{ep}/{path}", request, body)


register_proxy_routes(app)


# Serve Qdrant web UI at /dashboard/
# The dashboard directory is ../qdrant/dashboard relative to src/
_dashboard_path = os.path.join(os.path.dirname(__file__), "..", "qdrant", "dashboard")
if os.path.isdir(_dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=_dashboard_path, html=True), name="qdrant-dashboard")
