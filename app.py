import streamlit as st
import os, re, time, json, math, hashlib
from pathlib import Path

st.set_page_config(
    page_title="Docwise — AI Research Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
}

/* ── Base ── */
.stApp { background: #09090b; color: #fafafa; }
.block-container { padding-top: 2rem !important; padding-bottom: 4rem !important; }

/* ── Sidebar ── */
div[data-testid="stSidebar"] {
    background: #0c0c0e !important;
    border-right: 1px solid #1c1c1f !important;
}
div[data-testid="stSidebar"] .block-container { padding-top: 1.5rem !important; }

/* ── Sidebar wordmark ── */
.wordmark {
    font-size: 0.95rem; font-weight: 600; color: #fafafa;
    letter-spacing: -0.01em; margin-bottom: 0.1rem;
}
.wordmark-sub { font-size: 0.72rem; color: #52525b; letter-spacing: 0.01em; }

/* ── Section label ── */
.section-label {
    font-size: 0.68rem; font-weight: 600; color: #52525b;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 1.2rem 0 0.5rem 0;
}

/* ── Status badge ── */
.badge-ok {
    display: inline-flex; align-items: center; gap: 6px;
    background: #052e16; border: 1px solid #166534;
    color: #4ade80; border-radius: 6px;
    padding: 5px 10px; font-size: 0.75rem; font-weight: 500;
}
.badge-dot { width: 6px; height: 6px; background: #4ade80; border-radius: 50%; }

/* ── Stat cards ── */
.stat-row { display: flex; gap: 8px; margin-top: 0.5rem; }
.stat-card {
    flex: 1; background: #111113; border: 1px solid #1c1c1f;
    border-radius: 8px; padding: 10px 12px;
}
.stat-val { font-size: 1.4rem; font-weight: 700; color: #fafafa; line-height: 1; }
.stat-lbl { font-size: 0.68rem; color: #52525b; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Buttons ── */
.stButton > button {
    background: #fafafa !important; color: #09090b !important;
    border: none !important; border-radius: 7px !important;
    font-size: 0.8rem !important; font-weight: 600 !important;
    padding: 0.45rem 1rem !important; transition: opacity 0.15s !important;
    width: 100%;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Ghost button ── */
.btn-ghost > button {
    background: transparent !important; color: #71717a !important;
    border: 1px solid #27272a !important;
}
.btn-ghost > button:hover { color: #fafafa !important; border-color: #52525b !important; opacity: 1 !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #111113 !important; border: 1px solid #27272a !important;
    color: #fafafa !important; border-radius: 8px !important;
    font-size: 0.875rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #52525b !important;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.04) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #111113 !important; border: 1px solid #27272a !important;
    border-radius: 8px !important; color: #fafafa !important;
}

/* ── Slider ── */
.stSlider > div > div > div { background: #27272a !important; }
.stSlider > div > div > div > div { background: #fafafa !important; }

/* ── Toggle ── */
.stToggle { margin: 0 !important; }

/* ── Divider ── */
hr { border-color: #1c1c1f !important; margin: 1rem 0 !important; }

/* ── Page header ── */
.page-header { margin-bottom: 1.5rem; }
.page-title {
    font-size: 1.35rem; font-weight: 700; color: #fafafa;
    letter-spacing: -0.03em; margin: 0;
}
.page-desc { font-size: 0.8rem; color: #52525b; margin-top: 0.25rem; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1c1c1f !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #71717a !important;
    font-size: 0.8rem !important; font-weight: 500 !important;
    padding: 0.6rem 1rem !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #fafafa !important;
    border-bottom: 2px solid #fafafa !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem !important; }

/* ── Chat messages ── */
.msg-user {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 1rem 0; border-bottom: 1px solid #111113;
}
.msg-bot {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 1rem 0; border-bottom: 1px solid #111113;
    background: #0c0c0e; margin: 0 -1rem; padding: 1rem;
    border-radius: 8px; margin-bottom: 4px;
}
.msg-avatar {
    width: 28px; height: 28px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; flex-shrink: 0; margin-top: 1px;
}
.avatar-user { background: #27272a; color: #a1a1aa; }
.avatar-bot  { background: #fafafa; color: #09090b; }
.msg-content { flex: 1; font-size: 0.875rem; line-height: 1.6; color: #d4d4d8; }
.msg-role { font-size: 0.72rem; font-weight: 600; color: #52525b; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Source tags ── */
.source-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 10px; }
.source-tag {
    display: inline-flex; align-items: center; gap: 5px;
    background: #111113; border: 1px solid #27272a;
    border-radius: 5px; padding: 3px 8px;
    font-size: 0.7rem; color: #71717a;
    font-family: 'JetBrains Mono', monospace;
}
.source-tag-score { color: #a1a1aa; font-weight: 600; }

/* ── Eval chips ── */
.eval-row { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.eval-chip {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 9px; border-radius: 100px;
    font-size: 0.7rem; font-weight: 500; letter-spacing: 0.01em;
}

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 4rem 2rem;
    color: #3f3f46;
}
.empty-title { font-size: 0.9rem; font-weight: 500; color: #52525b; margin-bottom: 0.4rem; }
.empty-sub { font-size: 0.78rem; color: #3f3f46; }

/* ── Metric cards (eval page) ── */
.eval-stat {
    background: #0c0c0e; border: 1px solid #1c1c1f;
    border-radius: 10px; padding: 1.2rem 1.4rem;
}
.eval-stat-val { font-size: 2rem; font-weight: 700; color: #fafafa; line-height: 1; }
.eval-stat-lbl { font-size: 0.72rem; color: #52525b; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Spinner override ── */
.stSpinner > div { border-top-color: #fafafa !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #111113 !important; border: 1px dashed #27272a !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"]:hover { border-color: #52525b !important; }

/* ── Success / error ── */
.stSuccess { background: #052e16 !important; border: 1px solid #166534 !important; color: #4ade80 !important; border-radius: 8px !important; }
.stError   { background: #1c0a0a !important; border: 1px solid #7f1d1d !important; color: #f87171 !important; border-radius: 8px !important; }
.stWarning { background: #1c1100 !important; border: 1px solid #7c4f00 !important; color: #fbbf24 !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BACKEND
# ══════════════════════════════════════════════════════════════════════════════
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 80

def chunk_text(text, source):
    text = re.sub(r"\s+", " ", text).strip()
    chunks, start, idx = [], 0, 0
    while start < len(text):
        piece = text[start:start + CHUNK_SIZE]
        if piece.strip():
            chunks.append({"text": piece, "source": Path(source).name, "chunk_id": idx})
        start += CHUNK_SIZE - CHUNK_OVERLAP
        idx   += 1
    return chunks

def parse_file(uploaded_file):
    name = uploaded_file.name
    ext  = Path(name).suffix.lower()
    raw  = uploaded_file.read()
    if ext in (".txt", ".md"):
        return raw.decode("utf-8", errors="ignore")
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(stream=raw, filetype="pdf")
            return "\n".join(p.get_text() for p in doc)
        except Exception as e:
            return f"[PDF error: {e}]"
    if ext == ".csv":
        try:
            import pandas as pd, io
            return pd.read_csv(io.BytesIO(raw)).to_string(index=False)
        except Exception as e:
            return f"[CSV error: {e}]"
    if ext in (".png", ".jpg", ".jpeg"):
        try:
            import pytesseract
            from PIL import Image
            import io as _io
            text = pytesseract.image_to_string(Image.open(_io.BytesIO(raw)))
            return text if text.strip() else f"[Image: {name} — no text detected]"
        except:
            return f"[Image: {name} — OCR not available]"
    return f"[Unsupported: {ext}]"

@st.cache_resource(show_spinner="Loading embedding model...")
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")

def embed(texts):
    return get_embedder().encode(texts, show_progress_bar=False).tolist()

def cosine(a, b):
    dot  = sum(x*y for x,y in zip(a,b))
    magA = math.sqrt(sum(x*x for x in a))
    magB = math.sqrt(sum(x*x for x in b))
    return dot / (magA * magB + 1e-9)

def add_to_store(chunks):
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = []
    texts = [c["text"] for c in chunks]
    vecs  = embed(texts)
    existing = {e["id"] for e in st.session_state.vector_store}
    for chunk, vec in zip(chunks, vecs):
        uid = hashlib.md5(f"{chunk['source']}_{chunk['chunk_id']}".encode()).hexdigest()
        if uid not in existing:
            st.session_state.vector_store.append({
                "id": uid, "text": chunk["text"],
                "source": chunk["source"], "chunk_id": chunk["chunk_id"], "vec": vec,
            })

def retrieve(query, top_k=4):
    store = st.session_state.get("vector_store", [])
    if not store:
        return []
    qvec   = embed([query])[0]
    scored = sorted([(cosine(qvec, e["vec"]), e) for e in store], reverse=True)
    return [{"text":e["text"],"source":e["source"],"chunk_id":e["chunk_id"],"score":round(s,4)}
            for s, e in scored[:top_k]]

def build_context(chunks):
    return "\n\n".join(
        f"[Excerpt {i} — {c['source']}, relevance {c['score']:.2f}]\n{c['text']}"
        for i, c in enumerate(chunks, 1))

def generate_answer(question, chunks, api_key, model):
    import requests
    context = build_context(chunks)
    system  = ("You are a precise research assistant. Answer using ONLY the provided excerpts. "
               "Be concise. Cite sources as [Source: filename]. "
               "If the context lacks the answer, state that clearly.")
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model,
                  "messages": [{"role":"system","content":system},
                                {"role":"user","content":f"Context:\n{context}\n\nQuestion: {question}"}],
                  "temperature": 0.2, "max_tokens": 600},
            timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip(), None
    except requests.exceptions.HTTPError:
        if resp.status_code == 401:
            return None, "Invalid API key. Verify your Groq key in the sidebar."
        return None, f"API error {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return None, f"Error: {e}"

def _tf(text):
    tokens = re.findall(r"\b[a-z]{2,}\b", text.lower())
    freq = {}
    for t in tokens: freq[t] = freq.get(t,0)+1
    return freq

def _cos_token(a, b):
    ta, tb = _tf(a), _tf(b)
    vocab  = set(ta)|set(tb)
    dot    = sum(ta.get(v,0)*tb.get(v,0) for v in vocab)
    magA   = math.sqrt(sum(x*x for x in ta.values()))
    magB   = math.sqrt(sum(x*x for x in tb.values()))
    return dot/(magA*magB+1e-9)

def evaluate(question, answer, chunks):
    ctx   = " ".join(c["text"] for c in chunks)
    sents = [s.strip() for s in re.split(r"[.!?]+", answer) if len(s.strip())>10]
    faith = min(sum(_cos_token(s,ctx) for s in sents)/max(len(sents),1)*1.6,1.0) if sents else 0.0
    rel   = min(_cos_token(question,answer)*2.5,1.0)
    atoks = set(re.findall(r"\b[a-z]{2,}\b", answer.lower()))
    cov   = sum(1 for c in chunks if len(atoks&set(re.findall(r"\b[a-z]{2,}\b",c["text"].lower())))>=3)/max(len(chunks),1)
    return {"faithfulness":round(faith,3),"relevance":round(rel,3),"coverage":round(cov,3)}

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("messages",[]),("eval_log",[]),("vector_store",[])]:
    if k not in st.session_state: st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<div class='wordmark'>Docwise</div><div class='wordmark-sub'>AI Research Assistant</div>", unsafe_allow_html=True)
    st.divider()

    # API Key
    st.markdown("<div class='section-label'>API Key</div>", unsafe_allow_html=True)
    groq_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    if not groq_key:
        groq_key = st.text_input("Groq API key", type="password",
                                  placeholder="gsk_...",
                                  label_visibility="collapsed")
    else:
        st.markdown("<div class='badge-ok'><div class='badge-dot'></div>Connected</div>", unsafe_allow_html=True)

    # Model
    st.markdown("<div class='section-label'>Model</div>", unsafe_allow_html=True)
    model = st.selectbox("Model", [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
    ], index=0, label_visibility="collapsed")

    st.divider()

    # Upload
    st.markdown("<div class='section-label'>Documents</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload",
        type=["pdf","txt","md","csv","png","jpg","jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded:
        if st.button("Index documents", use_container_width=True):
            total = 0
            with st.spinner("Embedding documents..."):
                for f in uploaded:
                    text   = parse_file(f)
                    chunks = chunk_text(text, f.name)
                    add_to_store(chunks)
                    total += len(chunks)
            st.success(f"{total} chunks indexed")

    st.divider()

    # Settings
    st.markdown("<div class='section-label'>Retrieval</div>", unsafe_allow_html=True)
    top_k        = st.slider("Top-K chunks", 2, 8, 4, label_visibility="collapsed")
    show_sources = st.toggle("Show citations",    value=True)
    show_eval    = st.toggle("Show eval metrics", value=True)

    st.divider()

    # Stats
    store = st.session_state.vector_store
    docs  = len({e["source"] for e in store})
    st.markdown(f"""
    <div class='stat-row'>
        <div class='stat-card'><div class='stat-val'>{len(store)}</div><div class='stat-lbl'>Chunks</div></div>
        <div class='stat-card'><div class='stat-val'>{docs}</div><div class='stat-lbl'>Docs</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='btn-ghost'>", unsafe_allow_html=True)
        if st.button("Clear session", use_container_width=True):
            st.session_state.messages     = []
            st.session_state.eval_log     = []
            st.session_state.vector_store = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='page-header'>
    <div class='page-title'>Research Assistant</div>
    <div class='page-desc'>Upload documents, ask questions, receive cited answers with quality metrics.</div>
</div>""", unsafe_allow_html=True)

tab_chat, tab_eval = st.tabs(["Chat", "Evaluation"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — CHAT
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    # Empty state
    if not st.session_state.messages:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-title'>No messages yet</div>
            <div class='empty-sub'>Upload a document using the sidebar, index it, then ask a question below.</div>
        </div>""", unsafe_allow_html=True)

    # Message history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class='msg-user'>
                <div class='msg-avatar avatar-user'>U</div>
                <div class='msg-content'>
                    <div class='msg-role'>You</div>
                    {msg['content']}
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            sources_html = ""
            if show_sources and msg.get("sources"):
                tags = "".join(
                    f"<span class='source-tag'>{s['source']} &middot; chunk {s['chunk_id']} "
                    f"<span class='source-tag-score'>{s['score']:.0%}</span></span>"
                    for s in msg["sources"])
                sources_html = f"<div class='source-row'>{tags}</div>"

            eval_html = ""
            if show_eval and msg.get("eval"):
                e = msg["eval"]
                chips_data = [
                    ("Faithfulness", e["faithfulness"], "#6366f1", "#1e1b4b"),
                    ("Relevance",    e["relevance"],    "#0ea5e9", "#082f49"),
                    ("Coverage",     e["coverage"],     "#10b981", "#022c22"),
                ]
                chips = "".join(
                    f"<span class='eval-chip' style='background:{bg};color:{fg};'>"
                    f"{label} {val:.0%}</span>"
                    for label, val, fg, bg in chips_data)
                eval_html = f"<div class='eval-row'>{chips}</div>"

            st.markdown(f"""
            <div class='msg-bot'>
                <div class='msg-avatar avatar-bot'>AI</div>
                <div class='msg-content'>
                    <div class='msg-role'>Assistant</div>
                    {msg['content']}
                    {sources_html}
                    {eval_html}
                </div>
            </div>""", unsafe_allow_html=True)

    # Input
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col_q, col_btn = st.columns([6, 1])
    with col_q:
        question = st.text_input("question", placeholder="Ask anything about your documents...",
                                  key="q", label_visibility="collapsed")
    with col_btn:
        send = st.button("Send", use_container_width=True)

    if send and question.strip():
        if not groq_key:
            st.error("Add your Groq API key in the sidebar to continue.")
            st.stop()
        if not st.session_state.vector_store:
            st.warning("Index at least one document before asking questions.")
            st.stop()

        st.session_state.messages.append({"role":"user","content":question})

        with st.spinner("Generating answer..."):
            chunks       = retrieve(question, top_k=top_k)
            answer, err  = generate_answer(question, chunks, groq_key, model)

        if err:
            st.error(err)
        else:
            scores  = evaluate(question, answer, chunks)
            sources = [{"source":c["source"],"chunk_id":c["chunk_id"],"score":c["score"]} for c in chunks]
            st.session_state.messages.append({
                "role":"assistant","content":answer,
                "sources":sources,"eval":scores,
            })
            st.session_state.eval_log.append({
                "question":question,"timestamp":time.strftime("%H:%M:%S"),**scores
            })
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
with tab_eval:
    log = st.session_state.eval_log

    if not log:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-title'>No evaluation data</div>
            <div class='empty-sub'>Metrics appear here after you send messages in the Chat tab.</div>
        </div>""", unsafe_allow_html=True)
    else:
        import pandas as pd
        df = pd.DataFrame(log)

        c1,c2,c3,c4 = st.columns(4)
        for col, label, val in [
            (c1, "Queries",         str(len(log))),
            (c2, "Avg Faithfulness",f"{df['faithfulness'].mean():.0%}"),
            (c3, "Avg Relevance",   f"{df['relevance'].mean():.0%}"),
            (c4, "Avg Coverage",    f"{df['coverage'].mean():.0%}"),
        ]:
            col.markdown(f"""
            <div class='eval-stat'>
                <div class='eval-stat-val'>{val}</div>
                <div class='eval-stat-lbl'>{label}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.dataframe(
            df[["timestamp","question","faithfulness","relevance","coverage"]]
              .rename(columns={"timestamp":"Time","question":"Question",
                               "faithfulness":"Faithfulness","relevance":"Relevance","coverage":"Coverage"})
              .style.format({"Faithfulness":"{:.0%}","Relevance":"{:.0%}","Coverage":"{:.0%}"}),
            use_container_width=True, hide_index=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.download_button(
            "Export results",
            json.dumps(log, indent=2),
            "eval_results.json",
            "application/json",
        )
