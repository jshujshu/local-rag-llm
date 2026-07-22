#!/bin/bash

source ../src/.venv/bin/activate

export HF_HUB_OFFLINE=1

echo "Starting Qdrant..."
nohup ~/local-rag-llm/qdrant/qdrant > qdrant.log 2>&1 &

sleep 2

echo "Starting FastAPI..."
nohup uvicorn api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

sleep 3

echo "Starting Streamlit Debug Console..."
streamlit run ../src/debug.py