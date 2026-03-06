"""Green AI – Intelligent Environmental Risk Engine. Flask app and RAG pipeline."""

import os
import time

from flask import Flask, request, jsonify, send_from_directory

from .security import sanitize_input
from .retriever import retrieve
from .ranker import rerank
from .generator import generate_answer
from .evaluator import is_answer_grounded
from .ingest import ingest_text, load_existing_index
from .config import MAX_REGENERATE_ATTEMPTS
from .ppt_parser import extract_text_from_pptx
from .pdf_parser import extract_text_from_pdf
from .image_parser import extract_text_from_image
from .db import init_db
from .auth import bp as auth_bp


SEED_DOCUMENT = """
Environmental risk in construction and land development. Construction projects can pose significant environmental risks including soil erosion, water pollution, habitat destruction, and carbon emissions. Best practices include conducting environmental impact assessments (EIA), implementing erosion and sediment controls, protecting waterways, and minimizing tree removal. Tree removal often requires surveys and compliance with local ordinances; unauthorized removal can result in fines and project delays. Carbon footprint of construction includes embodied carbon in materials and operational emissions; sustainable practices include using low-carbon materials, renewable energy, and efficient design. Compliance with regulations such as EPA stormwater rules and local environmental permits is essential for project approval.
"""


def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="",
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_change_me")
    app.register_blueprint(auth_bp)

    # CORS: allow frontend from any origin
    @app.after_request
    def add_cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    def handle_upload(file_storage, extract_fn, source_label):
        """Common flow: read file, extract text, ingest, and confirm indexing (no immediate analysis)."""
        if not file_storage or not file_storage.filename:
            return jsonify({"detail": "No file selected."}), 400
        try:
            raw = file_storage.read()
            text = extract_fn(raw)
        except Exception as e:
            return jsonify({"detail": "Failed to read file: " + str(e)}), 400
        if not (text or "").strip():
            return jsonify({"detail": "No text found in the file."}), 400
        try:
            ingest_result = ingest_text(text, source=source_label, metadata={"filename": file_storage.filename})
        except Exception as e:
            return jsonify({"detail": "Failed to index document: " + str(e)}), 500
        return jsonify({
            "file_name": file_storage.filename,
            "message": "Document uploaded and indexed. You can now ask questions about this project (environment safety, AQI, deforestation, pollution, etc.).",
            "parents_added": ingest_result.get("parents_added", 0),
            "children_added": ingest_result.get("children_added", 0),
        })

    # Startup: load index and seed if empty
    with app.app_context():
        init_db()
        load_existing_index()
        from .vector_store import child_count
        if child_count() == 0:
            try:
                ingest_text(SEED_DOCUMENT, source="seed", metadata={"type": "default"})
            except Exception:
                pass

    def require_auth():
        from flask import session, jsonify
        if not session.get("user_id"):
            return jsonify({"detail": "Authentication required."}), 401
        return None

    @app.route("/ask", methods=["POST"])
    def ask_question():
        """Full RAG pipeline: security → retrieve → rank → generate (using Ollama)."""
        auth_resp = require_auth()
        if auth_resp:
            return auth_resp
        data = request.get_json(silent=True) or {}
        query = (data.get("query") or "").strip()
        if not query:
            return jsonify({"detail": "Query cannot be empty."}), 400
        if len(query) > 2000:
            query = query[:2000]

        sanitized, safe = sanitize_input(query)
        if not safe:
            return jsonify({
                "final_answer": sanitized,
                "risk_score": "Medium",
                "sources_used": [],
                "retrieval_time": "0ms",
                "generation_time": "0ms",
            })

        t_ret_start = time.perf_counter()
        context_strings, sources, _ = retrieve(sanitized)
        ranked = rerank(sanitized, context_strings)
        context = "\n\n---\n\n".join(ranked) if ranked else ""
        retrieval_time_ms = (time.perf_counter() - t_ret_start) * 1000

        t_gen_start = time.perf_counter()
        # Single Ollama generation for speed; no extra self-check loop
        answer, risk_score = generate_answer(context, sanitized)
        generation_time_ms = (time.perf_counter() - t_gen_start) * 1000

        return jsonify({
            "final_answer": answer,
            "risk_score": risk_score,
            "sources_used": sources[:10],
            "retrieval_time": f"{retrieval_time_ms:.0f}ms",
            "generation_time": f"{generation_time_ms:.0f}ms",
        })

    @app.route("/ingest", methods=["POST"])
    def ingest_document():
        """Ingest raw text into document store and vector index."""
        auth_resp = require_auth()
        if auth_resp:
            return auth_resp
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"detail": "text is required."}), 400
        source = data.get("source") or "upload"
        metadata = data.get("metadata") or {}
        result = ingest_text(text=text, source=source, metadata=metadata)
        return jsonify(result)

    @app.route("/upload_ppt", methods=["POST"])
    def upload_ppt():
        """Upload a .pptx file, ingest its text, and run safety analysis."""
        auth_resp = require_auth()
        if auth_resp:
            return auth_resp
        if "file" not in request.files:
            return jsonify({"detail": "No file provided. Use form field 'file'."}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"detail": "No file selected."}), 400
        if not f.filename.lower().endswith(".pptx"):
            return jsonify({"detail": "Only .pptx (PowerPoint) files are supported."}), 400
        return handle_upload(f, extract_text_from_pptx, "uploaded_ppt")

    @app.route("/upload_pdf", methods=["POST"])
    def upload_pdf():
        """Upload a .pdf file, ingest its text, and run safety analysis."""
        auth_resp = require_auth()
        if auth_resp:
            return auth_resp
        if "file" not in request.files:
            return jsonify({"detail": "No file provided. Use form field 'file'."}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"detail": "No file selected."}), 400
        if not f.filename.lower().endswith(".pdf"):
            return jsonify({"detail": "Only .pdf files are supported."}), 400
        return handle_upload(f, extract_text_from_pdf, "uploaded_pdf")

    @app.route("/upload_image", methods=["POST"])
    def upload_image():
        """Upload an image – OCR text, chunk, and ingest (same as PDF/PPT)."""
        auth_resp = require_auth()
        if auth_resp:
            return auth_resp
        if "file" not in request.files:
            return jsonify({"detail": "No file provided. Use form field 'file'."}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"detail": "No file selected."}), 400
        ext = "." + (f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "")
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"):
            return jsonify({"detail": "Only image files (PNG, JPG, GIF, WebP, etc.) are supported."}), 400
        return handle_upload(f, extract_text_from_image, "uploaded_image")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        """Serve frontend static files; index.html for root."""
        if not path or path == "/":
            return send_from_directory(app.static_folder, "index.html")
        if os.path.isfile(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    return app


app = create_app()
