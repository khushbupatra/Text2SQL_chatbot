import os
import json
import time
import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Text-to-SQL Chatbot", layout="wide")

# ---------------- Config ----------------
DEFAULT_API = os.getenv("TEXT2SQL_API_BASE", "http://localhost:8000")

st.sidebar.title("Settings")
api_base = st.sidebar.text_input("API base URL", DEFAULT_API, help="FastAPI server base")
st.sidebar.caption("Start the API with: `uvicorn backend.main:app --reload --port 8000`")

# Fetch DB keys
def get_schemas():
    try:
        r = requests.get(f"{api_base}/schemas", timeout=10)
        r.raise_for_status()
        return r.json().get("databases", [])
    except Exception as e:
        st.sidebar.error(f"Failed to load DB keys: {e}")
        return []

def get_metrics():
    try:
        r = requests.get(f"{api_base}/metrics", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

db_keys = get_schemas()

st.title("🧠 AI Text-to-SQL Chatbot")

colA, colB = st.columns([1,1])

with colA:
    st.subheader("Ask a question")
    db_key = st.selectbox("Database key", options=db_keys or ["demo_sqlite"])
    user_text = st.text_area("Natural-language query", placeholder="Top 10 customers by spend last month in APAC", height=120)
    schema_hint = st.text_area("Schema hint (optional)", placeholder="tables: customers(id, name, spend, region); orders(...)", height=120)
    run = st.button("Run", type="primary")

with colB:
    st.subheader("Service metrics")
    m = get_metrics()
    st.json(m)

st.markdown("---")

if run and user_text.strip():
    payload = {"user_text": user_text, "db_key": db_key, "schema_hint": schema_hint}
    t0 = time.time()
    with st.spinner("Generating SQL, verifying, and executing..."):
        try:
            r = requests.post(f"{api_base}/ask", json=payload, timeout=60)
            if r.status_code != 200:
                detail = r.json().get("detail") if r.headers.get("content-type","").startswith("application/json") else r.text
                st.error(f"Error: {detail}")
            else:
                j = r.json()
                st.success(f"Done in {j.get('latency_ms', int((time.time()-t0)*1000))} ms")
                with st.expander("Generated SQL", expanded=True):
                    st.code(j.get("sql",""), language="sql")
                    st.write("Verified with EXPLAIN:", "✅" if j.get("verified") else "❌")
                rows = j.get("rows", [])
                if rows:
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)
                    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), file_name="query_result.csv")
                else:
                    st.info("No rows returned.")
        except Exception as e:
            st.error(f"Request failed: {e}")
