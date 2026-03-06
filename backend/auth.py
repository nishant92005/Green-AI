from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_conn

bp = Blueprint("auth", __name__)

@bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    password = (data.get("password") or "")
    if not email or not name or not password:
        return jsonify({"detail": "All fields are required."}), 400
    if "@" not in email or "." not in email:
        return jsonify({"detail": "Invalid email."}), 400
    ph = generate_password_hash(password)
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users(email, name, password_hash) VALUES (?, ?, ?)", (email, name, ph))
        conn.commit()
    except Exception as e:
        return jsonify({"detail": "Email already registered."}), 409
    user_id = cur.lastrowid
    session["user_id"] = user_id
    session["user_email"] = email
    session["user_name"] = name
    return jsonify({"id": user_id, "email": email, "name": name})

@bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")
    if not email or not password:
        return jsonify({"detail": "Email and password required."}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, email, name, password_hash FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"detail": "Invalid credentials."}), 401
    session["user_id"] = row["id"]
    session["user_email"] = row["email"]
    session["user_name"] = row["name"]
    return jsonify({"id": row["id"], "email": row["email"], "name": row["name"]})

@bp.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@bp.route("/auth/me", methods=["GET"])
def me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "id": uid, "email": session.get("user_email"), "name": session.get("user_name")})
