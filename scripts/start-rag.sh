#!/bin/bash

cd ~/local-llm/src || exit 1

source ../src/.venv/bin/activate

# Security: prevent HuggingFace from pulling updated model weights at runtime
export HF_HUB_OFFLINE=1

# Security: bind to loopback by default — set BIND_HOST=0.0.0.0 explicitly
# only when you intend to expose the API on the LAN.
export BIND_HOST=${BIND_HOST:-127.0.0.1}

echo "Starting Qdrant..."
nohup ~/local-llm/qdrant/qdrant > qdrant.log 2>&1 &

sleep 2

echo "Starting FastAPI (host=$BIND_HOST)..."
if [ "${DEV_MODE:-0}" = "1" ]; then
    uvicorn api:app --host "$BIND_HOST" --port 8000 --reload
else
    uvicorn api:app --host "$BIND_HOST" --port 8000
fi
