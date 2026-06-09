import streamlit as st
import os, re, time, json, math, hashlib
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Research Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0f1117; color: #e8eaf0; }
.hero-title {
    font-size: 2.2rem; font-weight: 700; letter-spacing: -0.03em;
    background: linear-gradient(135deg, #7c6ef2 0%, #a78bfa 50%, #60a5fa 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero-sub { color: #8b92a9; font-size: 0.9rem; margin-bottom: 1.5rem; }
.metric-card {
    background: #1a1d27; border: 1px solid #2a2d3e;
    border-radius: 12px; padding: 1rem; text-align: center;
}
.metric-value { font-size: 1.6rem; font-weight: 700; color: #a78bfa; }
.metric-label { font-size: 0.72rem; color: #8b92a9; text-transform: uppercase; letter-spacing: 0.08em; }
.chat-user {
    background: #1e2235; border-radius: 12px 12px 4px 12px;
    padding: 0.8rem 1rem; margin: 0.6rem 0; border-left: 3px solid #7c6ef2;
}
.chat-bot {
    background: #161926; border-radius: 12px 12px 12px 4px;
    padding: 0.8rem 1rem; margin: 0.6rem 0; border-left: 3px solid #60a5fa;
}
.source-pill {
    display:inline-block; background:#1e2235; border:1px solid #2a2d3e;
    border-radius:6px; padding:2px 8px; font-size:0.73rem; color:#a78bfa;
    margin:2px; font-family:'JetBrains Mono',monospace;
}
.eval-chip {
    display:inline-block; padding:2px 10px; border-radius:20px;
    font-size:0.76rem; font-weight:600; margin:2px;
}
.step-box {
    background:#1a1d27; border:1px solid #2a2d3e; border-radius:10px;
    padding:1rem; margin:0.5rem 0;
}
.step-num { color:#7c6ef2; font-weight:700; font-family:'JetBrains Mono',monospace; font-size:0.8rem; }
div[data-testid="stSidebar"] { background:#0d0f1a; border-right:1px solid #1e2235; }
.stButton>button {
    background:linear-gradient(135deg,#7c6ef2,#5b5bd6); color:white;
    border:none; border-radius:8px; font-weight:600;
    transition:all 0.2s;
}
.stButton>button:hover { transform:translateY(-1px); box-shadow:0 4px 15px rgba(124,110,242,0.4); }
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background:#1a1d27 !important; border:1px solid #2a2d3e !important;
    color:#e8eaf0 !important; border-radius:8px !important;
}
code { background:#1e2235; padding:2px 6px; border-radius:4px; color:#a78bfa; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INLINE BACKEND  (no separate files needed — works on Streamlit Cloud)
# ══════════════════════════════════════════════════════════════════════════════

# ── Chunking ──────────────────────────────────────────────────────────────────
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

# ── Parsers ───────────────────────────────────────────────────────────────────
def parse_file(uploaded_file):
    name = uploaded_file.name
    ext  = Path(name).suffix.lower()
    raw  = uploaded_file.read()

    if ext == ".txt" or ext == ".md":
        return raw.decode("utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            import fitz
            doc  = fitz.open(stream=raw, filetype="pdf")
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
            import io
            text = pytesseract.image_to_string(Image.open(io.BytesIO(raw)))
            return text if text.strip() else f"[Image: {name} — no text detected]"
        except:
            return f"[Image: {name} — OCR not available on this server]"

    return f"[Unsupported file type: {ext}]"

# ── Embedding (cached so model loads once per session) ────────────────────────
@st.cache_resource(show_spinner="Loading embedding model…")
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")

def embed(texts):
    return get_embedder().encode(texts, show_progress_bar=False).tolist()

# ── In-memory vector store (persists across reruns via session_state) ─────────
def cosine(a, b):
    dot  = sum(x*y for x,y in zip(a,b))
    magA = math.sqrt(sum(x*x for x in a))
    magB = math.sqrt(sum(x*x for x in b))
    return dot / (magA * magB + 1e-9)

def add_chunks_to_store(chunks):
    """Embed and add chunks to session-state vector store."""
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = []
    texts  = [c["text"] for c in chunks]
    vecs   = embed(texts)
    for chunk, vec in zip(chunks, vecs):
        uid = hashlib.md5(f"{chunk['source']}_{chunk['chunk_id']}".encode()).hexdigest()
        # avoid duplicates
        existing_ids = {e["id"] for e in st.session_state.vector_store}
        if uid not in existing_ids:
            st.session_state.vector_store.append({
                "id":       uid,
                "text":     chunk["text"],
                "source":   chunk["source"],
                "chunk_id": chunk["chunk_id"],
                "vec":      vec,
            })

def retrieve(query, top_k=4):
    store = st.session_state.get("vector_store", [])
    if not store:
        return []
    qvec   = embed([query])[0]
    scored = [(cosine(qvec, e["vec"]), e) for e in store]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"text": e["text"], "source": e["source"], "chunk_id": e["chunk_id"], "score": round(s, 4)}
        for s, e in scored[:top_k]
    ]

# ── Groq generation ───────────────────────────────────────────────────────────
def build_context(chunks):
    return "\n\n".join(
        f"--- Excerpt {i} (from {c['source']}, relevance {c['score']:.2f}) ---\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    )

def generate_answer(question, chunks, api_key, model):
    import requests
    context = build_context(chunks)
    system  = (
        "You are a research assistant. Answer ONLY using the provided document excerpts. "
        "Be concise and accurate. At the end cite sources like [Source: filename]. "
        "If the context lacks the answer, say so."
    )
    user_msg = f"CONTEXT:\n{context}\n\nQUESTION: {question}"

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model":       model,
                "messages":    [{"role":"system","content":system}, {"role":"user","content":user_msg}],
                "temperature": 0.2,
                "max_tokens":  600,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip(), None
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            return None, "❌ Invalid API key. Double-check your Groq key."
        return None, f"❌ Groq API error {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return None, f"❌ Error: {e}"

# ── Evaluation ────────────────────────────────────────────────────────────────
def _tf(text):
    tokens = re.findall(r"\b[a-z]{2,}\b", text.lower())
    freq   = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return freq

def _cos_token(a, b):
    ta, tb   = _tf(a), _tf(b)
    vocab    = set(ta) | set(tb)
    dot      = sum(ta.get(v,0)*tb.get(v,0) for v in vocab)
    magA     = math.sqrt(sum(x*x for x in ta.values()))
    magB     = math.sqrt(sum(x*x for x in tb.values()))
    return dot / (magA * magB + 1e-9)

def evaluate(question, answer, chunks):
    ctx   = " ".join(c["text"] for c in chunks)
    sents = [s.strip() for s in re.split(r"[.!?]+", answer) if len(s.strip()) > 10]
    faith = min(
        sum(_cos_token(s, ctx) for s in sents) / max(len(sents), 1) * 1.6, 1.0
    ) if sents else 0.0
    rel   = min(_cos_token(question, answer) * 2.5, 1.0)
    atoks = set(re.findall(r"\b[a-z]{2,}\b", answer.lower()))
    cov   = sum(
        1 for c in chunks
        if len(atoks & set(re.findall(r"\b[a-z]{2,}\b", c["text"].lower()))) >= 3
    ) / max(len(chunks), 1)
    return {"faithfulness": round(faith,3), "relevance": round(rel,3), "coverage": round(cov,3)}

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for key, val in [("messages",[]), ("eval_log",[]), ("vector_store",[])]:
    if key not in st.session_state:
        st.session_state[key] = val

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🧠 RAG Assistant")
    st.markdown("<p style='color:#8b92a9;font-size:0.82rem;'>Powered by Groq · Free · Cloud</p>", unsafe_allow_html=True)
    st.divider()

    # ── API Key ──
    st.markdown("#### 🔑 Groq API Key")
    # Try secrets first (for deployed app), then manual input
    groq_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    if not groq_key:
        groq_key = st.text_input("Paste your free Groq key", type="password",
                                  placeholder="gsk_...",
                                  help="Get free key at console.groq.com")
    else:
        st.success("✅ API key loaded from secrets")

    model = st.selectbox("Model", [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
    ], index=0, help="llama-3.1-8b-instant is fastest · all are free tier")

    st.divider()

    # ── Upload ──
    st.markdown("#### 📂 Upload Documents")
    uploaded = st.file_uploader(
        "PDF · TXT · CSV · Image",
        type=["pdf","txt","md","csv","png","jpg","jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded:
        if st.button("🚀 Index Documents", use_container_width=True):
            total = 0
            with st.spinner("Parsing & embedding…"):
                for f in uploaded:
                    text   = parse_file(f)
                    chunks = chunk_text(text, f.name)
                    add_chunks_to_store(chunks)
                    total += len(chunks)
            st.success(f"✅ {total} chunks indexed!")

    st.divider()

    # ── Settings ──
    st.markdown("#### ⚙️ Settings")
    top_k        = st.slider("Chunks to retrieve", 2, 8, 4)
    show_sources = st.toggle("Show source citations", True)
    show_eval    = st.toggle("Show eval scores",      True)

    st.divider()

    # ── Stats ──
    store = st.session_state.vector_store
    docs  = len({e["source"] for e in store})
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='metric-card'><div class='metric-value'>{len(store)}</div><div class='metric-label'>Chunks</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-value'>{docs}</div><div class='metric-label'>Docs</div></div>",   unsafe_allow_html=True)

    st.markdown("")
    if st.button("🗑 Clear Everything", use_container_width=True):
        st.session_state.messages    = []
        st.session_state.eval_log    = []
        st.session_state.vector_store= []
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='hero-title'>RAG Research Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>Upload documents → Ask questions → Get cited, explainable answers — Free via Groq</div>", unsafe_allow_html=True)

tab_chat, tab_eval, tab_guide = st.tabs(["💬 Chat", "📊 Evaluation", "📖 Deploy Guide"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 – CHAT
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    # Render history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'>👤 <b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bot'>🤖 <b>Assistant:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
            if show_sources and msg.get("sources"):
                src_html = "".join(
                    f"<span class='source-pill'>📄 {s['source']} · chunk {s['chunk_id']} · {s['score']:.0%}</span>"
                    for s in msg["sources"]
                )
                st.markdown(f"<div style='margin-top:4px'>{src_html}</div>", unsafe_allow_html=True)
            if show_eval and msg.get("eval"):
                e = msg["eval"]
                colors = {"Faithfulness":"#7c6ef2","Relevance":"#60a5fa","Coverage":"#34d399"}
                vals   = {"Faithfulness": e["faithfulness"], "Relevance": e["relevance"], "Coverage": e["coverage"]}
                html   = "".join(
                    f"<span class='eval-chip' style='background:{c}22;color:{c};border:1px solid {c}55'>{k}: {vals[k]:.0%}</span>"
                    for k, c in colors.items()
                )
                st.markdown(f"<div style='margin-top:6px'>{html}</div>", unsafe_allow_html=True)

    # Input row
    col_q, col_btn = st.columns([5,1])
    with col_q:
        question = st.text_input("Ask about your documents…", key="q", label_visibility="collapsed")
    with col_btn:
        send = st.button("Send →", use_container_width=True)

    if send and question.strip():
        if not groq_key:
            st.error("Please enter your Groq API key in the sidebar.")
            st.stop()
        if not st.session_state.vector_store:
            st.warning("Upload and index some documents first using the sidebar.")
            st.stop()

        st.session_state.messages.append({"role":"user","content":question})

        with st.spinner("Retrieving & generating…"):
            chunks = retrieve(question, top_k=top_k)
            answer, err = generate_answer(question, chunks, groq_key, model)

        if err:
            st.error(err)
        else:
            scores = evaluate(question, answer, chunks)
            sources = [{"source":c["source"],"chunk_id":c["chunk_id"],"score":c["score"]} for c in chunks]
            st.session_state.messages.append({
                "role":"assistant","content":answer,
                "sources":sources,"eval":scores,
            })
            st.session_state.eval_log.append({
                "question":question, "timestamp":time.strftime("%H:%M:%S"), **scores
            })
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 – EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
with tab_eval:
    st.markdown("### 📊 Live Evaluation Metrics")
    log = st.session_state.eval_log

    if not log:
        st.info("Ask questions in the Chat tab to see metrics here.")
    else:
        import pandas as pd
        df = pd.DataFrame(log)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Queries",    len(log))
        c2.metric("Avg Faithfulness", f"{df['faithfulness'].mean():.0%}")
        c3.metric("Avg Relevance",    f"{df['relevance'].mean():.0%}")
        c4.metric("Avg Coverage",     f"{df['coverage'].mean():.0%}")

        st.markdown("#### Per-Query Breakdown")
        st.dataframe(
            df[["timestamp","question","faithfulness","relevance","coverage"]]
              .style.format({"faithfulness":"{:.0%}","relevance":"{:.0%}","coverage":"{:.0%}"}),
            use_container_width=True
        )
        st.download_button("⬇ Export as JSON",
            json.dumps(log, indent=2), "eval_results.json", "application/json")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 – DEPLOY GUIDE
# ─────────────────────────────────────────────────────────────────────────────
with tab_guide:
    st.markdown("### 📖 Deploy This App in 10 Minutes — No Coding")

    steps = [
        ("Create a free GitHub account",
         "Go to <b>github.com</b> → Sign up (free). You need this to host the code."),
        ("Create a new repository",
         "Click the <b>+</b> icon → New repository → Name it <code>rag-assistant</code> → Set to Public → Create."),
        ("Upload the project files",
         "Click <b>uploading an existing file</b> → Drag all files from the downloaded ZIP → Commit changes."),
        ("Get a free Groq API key",
         "Go to <b>console.groq.com</b> → Sign up (free) → API Keys → Create Key → Copy it. Takes 2 minutes."),
        ("Deploy on Streamlit Cloud",
         "Go to <b>share.streamlit.io</b> → Sign in with GitHub → New app → Choose your repo → Main file: <code>app.py</code> → Deploy."),
        ("Add your API key as a secret",
         "In Streamlit Cloud dashboard → your app → Settings → Secrets → paste:<br><code>GROQ_API_KEY = \"gsk_your_key_here\"</code> → Save. Done!"),
    ]

    for i, (title, body) in enumerate(steps, 1):
        st.markdown(f"""
        <div class='step-box'>
            <div class='step-num'>STEP {i} OF {len(steps)}</div>
            <b style='color:#e8eaf0;font-size:0.95rem'>{title}</b>
            <p style='color:#8b92a9;margin:0.3rem 0 0;font-size:0.85rem'>{body}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔧 Troubleshooting")
    with st.expander("App says 'Invalid API key'"):
        st.markdown("Make sure you pasted the full Groq key including the `gsk_` prefix, and saved the secret correctly.")
    with st.expander("'No module named X' error on Streamlit Cloud"):
        st.markdown("Make sure `requirements.txt` is in the root of your GitHub repo and contains all packages.")
    with st.expander("Embedding model slow to load"):
        st.markdown("First load takes ~30 seconds on Streamlit Cloud. After that it's cached for the session.")
    with st.expander("How to use a different model"):
        st.markdown("Change the model in the sidebar dropdown. `llama-3.3-70b-versatile` is smarter but slower. `openai/gpt-oss-120b` is the most powerful. `llama-3.1-8b-instant` is fastest for quick answers.")

