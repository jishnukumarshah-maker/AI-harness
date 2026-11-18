import streamlit as st
import sqlite3
import pandas as pd
from cache import init_db, DB_NAME
from harness import run_harness

init_db()
st.set_page_config(page_title="Agentic Harness v1.2", layout="wide")

st.title("Agentic Harness v1.2")
st.caption("Explainable Self-Correcting LLM Reliability & Semantic Caching Framework")

tab1, tab2 = st.tabs(["Live Playground", "Reliability Analytics"])

with tab1:
    prompt = st.text_area(
        "Enter a prompt (try strict constraints like 'Return valid JSON with keys name and age for 2 users'):",
        height=100
    )
    use_cache = st.checkbox("Enable SQLite Semantic Cache", value=True)

    if st.button("Run Orchestrator", type="primary") and prompt.strip():
        with st.spinner("Generating, validating, and evaluating..."):
            try:
                result = run_harness(prompt, use_cache=use_cache)
            except Exception as e:
                st.error(f"Error running harness: {e}")
                result = None

        if result:
            # Top Metrics Row
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Initial Score", f"{result['initial_score']:.2f}")
            c2.metric("Final Reliability", f"{result['final_score']:.2f}", delta=round(result['final_score'] - result['initial_score'], 2))
            c3.metric("Retries Used", result["retries"])
            c4.metric("Latency", f"{result['latency_ms']} ms", delta="Cache Hit" if result["cached"] else "Live API")

            # Explainable Execution Trace
            with st.expander("Explainable Evaluation Trace (How the Harness judged this)", expanded=True):
                for step in result["trace"]:
                    st.write(f"- {step}")

            st.subheader("Final Verified Output")
            st.write(result["answer"])

with tab2:
    st.subheader("Historical System Performance")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM logs", conn)
    conn.close()

    if df.empty:
        st.info("No queries logged yet. Run some prompts in the Live Playground first!")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Queries", len(df))
        col2.metric("Avg Initial vs Final Score", f"{df['initial_score'].mean():.2f} -> {df['final_score'].mean():.2f}")
        col3.metric("Cache Hit Rate", f"{(df['cached'].mean() * 100):.1f}%")

        st.bar_chart(df[["initial_score", "final_score"]])
        st.dataframe(df.tail(15), use_container_width=True)