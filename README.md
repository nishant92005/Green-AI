# Green AI – Intelligent Environmental Risk Engine

Production-grade **RAG** (Retrieval-Augmented Generation) system with a ChatGPT-style frontend and **Groq API** for high-speed inference. Built for environmental and construction risk analysis.

## Features

- **Advanced RAG**: Parent–child chunking, HyDE, multi-query expansion, re-ranking, evaluation loop
- **Backend**: Flask, FAISS (vector store), HuggingFace embeddings, Groq LLM
- **Frontend**: Dark theme, neon green accent, hero landing, chat UI with suggestions and typing indicator
- **Security**: Prompt injection detection, input sanitization
- **Monitoring**: Retrieval and generation timing in API response

## Quick start

1. **Environment**

   ```bash
   cd "D:\green ai"
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure**

   Copy `backend\.env.example` to `backend\.env` and set `GROQ_API_KEY`.

3. **Run**

   ```bash
   python main.py
   ```
   Or: `flask --app main run --host 0.0.0.0 --port 8000`

   Open **http://localhost:8000** for the UI. Use **Analyze Project** or **Try Demo** to start the chat.

## API

- **POST /ask** – Send a question; returns `final_answer`, `risk_score`, `sources_used`, `retrieval_time`, `generation_time`.
- **POST /ingest** – Ingest text: `{"text": "...", "source": "optional", "metadata": {}}`.

## Backend layout

| Module | Role |
|--------|------|
| `chunking.py` | Parent/child semantic chunking |
| `document_store.py` | Parent chunks (JSON) |
| `vector_store.py` | Child chunks + FAISS index |
| `embeddings.py` | HuggingFace sentence-transformers |
| `query_processing.py` | Multi-query expansion + HyDE (Groq) |
| `retriever.py` | Retrieve → map to parents → dedupe |
| `ranker.py` | LLM re-ranking of contexts |
| `generator.py` | Groq generation + risk score |
| `evaluator.py` | Grounding check, optional regenerate |
| `security.py` | Sanitization + injection detection |
| `ingest.py` | Ingest text into store + index |
| `main.py` | Flask app + `/ask`, `/ingest`, static frontend |

## Multimodal (extensible)

The design supports adding:


- **PDFs** → Extract text → semantic chunking → ingest
- Text → Clean/normalize text → semantic chunking → ingest
- PPTs → Extract slide text (titles, bullets, notes) → semantic chunking → ingest

Add parsers in `ingest.py` and optional embedding branches in `embeddings.py` / `vector_store.py` as needed.

