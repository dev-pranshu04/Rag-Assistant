# 🧠 RAG Research Assistant — Cloud Version

> **Free. No local setup. Deploy in 10 minutes.**

Upload PDFs, text files, or CSVs — ask questions — get cited answers with live evaluation metrics. Powered by Groq (free LLM API) + Streamlit Cloud (free hosting).

---

## ⚡ Live Demo
Check It out
`https://rag-assistant-04.streamlit.app`

---

## 🚀 Deploy in 10 Minutes

### 1. Fork / upload this repo to GitHub
Upload all files to a new public GitHub repository.

### 2. Get a free Groq API key
- Go to [console.groq.com](https://console.groq.com)
- Sign up → API Keys → Create Key → Copy

### 3. Deploy on Streamlit Community Cloud
- Go to [share.streamlit.io](https://share.streamlit.io)
- Sign in with GitHub → New app
- Select your repo, branch `main`, file `app.py`
- Click **Deploy**

### 4. Add API key as a secret
In Streamlit Cloud dashboard → your app → **Settings → Secrets**:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```
Save → Done ✅

---

## 🏗 Architecture

```
User uploads PDF/TXT/CSV
        ↓
  [Parser Layer]          PyMuPDF · pandas · Pillow
        ↓
  [Chunking]              500-char chunks, 80-char overlap
        ↓
  [Embedding]             all-MiniLM-L6-v2 (Sentence Transformers)
        ↓
  [In-memory Vector Store] Cosine similarity search
        ↓
  [Generation]            Groq API → Llama3 / Mixtral (free)
        ↓
  [Evaluation]            Faithfulness · Relevance · Coverage
        ↓
  [Streamlit UI]          Chat + Eval Dashboard
```

---

## 📁 File Structure

```
rag-assistant/
├── app.py                        ← entire app in one file
├── requirements.txt              ← dependencies
├── .streamlit/
│   ├── config.toml               ← dark theme config
│   └── secrets.toml.template     ← add your key here (don't commit!)
├── .gitignore
└── README.md
```

---

## 🆓 Free Tier Limits (Groq)

| Model | Free Requests/day | Speed |
|-------|-------------------|-------|
| llama3-8b-8192 | 14,400 | Very fast |
| llama3-70b-8192 | 14,400 | Fast |
| mixtral-8x7b-32768 | 14,400 | Fast, long context |

More than enough for a portfolio project and interviews.

---

## 📈 Metrics to put on your resume

- "Built end-to-end RAG pipeline with semantic retrieval and hallucination scoring"
- "Deployed on Streamlit Cloud with 3 evaluation metrics: faithfulness, relevance, coverage"
- "Supports PDF, CSV, and text ingestion with chunked embedding via Sentence Transformers"
