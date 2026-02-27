import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta

st.set_page_config(page_title="Doc → Summary + Tasks", layout="centered")
st.title("Doc → Summary + Action Items (MVP)")

uploaded = st.file_uploader("Upload a .txt file", type=["txt"])

def extract_text_txt(file) -> str:
    return file.read().decode("utf-8", errors="ignore")

def simple_summary(text: str) -> str:
    # Very simple starter summary: first ~5 sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:5]) if sentences else text[:600]

def extract_tasks(text: str):
    """
    MVP tasks extractor (no AI):
    - Finds lines that start with action verbs or contain 'TODO' / 'Action:'.
    - You will replace this with LLM later.
    """
    tasks = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    patterns = [
        r'^(action|todo)\s*[:\-]\s*(.+)$',
        r'^(please|need to|we should|we will|follow up|send|call|email|schedule|prepare)\b(.+)$'
    ]

    for l in lines:
        low = l.lower()
        found = None
        for p in patterns:
            m = re.match(p, low)
            if m:
                found = l
                break
        # Also capture bullet lines containing "by" (deadline hint)
        if not found and (l.startswith("-") or l.startswith("•")) and (" by " in low or " due " in low):
            found = l

        if found:
            tasks.append({
                "task_title": found.lstrip("-• ").strip(),
                "owner": "",
                "due_date": "",
                "priority": "Medium"
            })

    # If nothing found, create a placeholder task
    if not tasks and text.strip():
        tasks.append({
            "task_title": "Review the document and define next actions",
            "owner": "",
            "due_date": str(date.today() + timedelta(days=2)),
            "priority": "High"
        })
    return tasks

if uploaded:
    text = extract_text_txt(uploaded)

    st.subheader("Preview (first 600 chars)")
    st.code(text[:600])

    st.subheader("Executive Summary")
    st.write(simple_summary(text))

    st.subheader("Action Items")
    tasks = extract_tasks(text)
    df = pd.DataFrame(tasks)
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download tasks as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="tasks.csv",
        mime="text/csv"
    )
else:
    st.info("Upload a .txt file to test the MVP.")