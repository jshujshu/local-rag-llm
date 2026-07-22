# debug.py

import time
import requests
import streamlit as st
from config import LLM_MODELS, DEFAULT_MODEL
from query import retrieve_context
from ingest import run as run_ingest

API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="RAG Debug Console", layout="wide")
st.title("RAG Debug Console")
tab_compare, tab_retrieval, tab_ingest = st.tabs(
    ["Compare Models", "Retrieval Inspector", "Ingest"]
)

# model comparison tool
with tab_compare:
    st.subheader("Compare answers across models / RAG settings")
    question = st.text_input("Question", key="compare_question")
    selected_models = st.multiselect(
        "Models to compare",
        options=list(LLM_MODELS.keys()),
        default=[DEFAULT_MODEL],
    )
    use_rag = st.checkbox("Use RAG", value=True, key="compare_use_rag")
    if st.button("Run comparison", key="compare_run"):
        if not question:
            st.warning("Enter a question first.")
        elif not selected_models:
            st.warning("Select at least one model.")
        else:
            cols = st.columns(len(selected_models))
            for col, model_key in zip(cols, selected_models):
                with col:
                    st.markdown(f"**{model_key}**")
                    with st.spinner("Generating..."):
                        start = time.time()
                        try:
                            resp = requests.post(
                                API_URL,
                                json={
                                    "question": question,
                                    "model": model_key,
                                    "use_rag": use_rag,
                                },
                                timeout=300,
                            )
                            elapsed = time.time() - start
                            st.write(resp.text)
                            st.caption(f"{elapsed:.1f}s")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Request failed: {e}")

# inspector
with tab_retrieval:
    st.subheader("See what gets retrieved for a query")
    query_text = st.text_input("Query", key="retrieval_query")
    top_n = st.slider("Chunks to show", min_value=1, max_value=10, value=4)
    if st.button("Retrieve", key="retrieval_run"):
        if not query_text:
            st.warning("Enter a query first.")
        else:
            with st.spinner("Searching Qdrant..."):
                try:
                    _, results = retrieve_context(query_text)
                except Exception as e:
                    st.error(f"Retrieval failed: {e}")
                    results = []
            if not results:
                st.warning("No results returned.")
            else:
                for i, r in enumerate(results[:top_n], start=1):
                    payload = r.payload or {}
                    source = payload.get("source", "unknown")
                    text = payload.get("text", "")
                    label = f"#{i} — {source}"
                    if r.score is not None:
                        label += f"  (score: {r.score:.4f})"
                    with st.expander(label):
                        st.caption(f"id: {r.id} · {len(text)} chars")
                        st.text(text)

# ingest
with tab_ingest:
    st.subheader("Run ingestion")
    st.write(
        "Scans the data directory for markdown files and embeds any "
        "new or changed chunks into Qdrant."
    )
    if st.button("Run ingest now"):
        with st.spinner("Ingesting..."):
            try:
                new_chunks, files_scanned = run_ingest()
                if new_chunks == 0:
                    st.info(f"No new changes. Scanned {files_scanned} files.")
                else:
                    st.success(
                        f"Ingested {new_chunks} new chunks from {files_scanned} files."
                    )
            except Exception as e:
                st.error(f"Ingest failed: {e}")