"""
app.py  –  Smart Placement Intelligence System  (v2 – Industry Level)
─────────────────────────────────────────────────────────────────────
SUBJECTS COVERED:
  WT     → Flask REST API, HTTP methods, JSON, Sessions, File Upload
  AI     → ML prediction, NLP resume analysis, Intent-based chatbot
  DSBDA  → MySQL CRUD, aggregate analytics, data persistence

ROUTES:
  GET/POST  /register        → account creation
  GET/POST  /login           → authentication
  GET       /logout          → session clear
  GET       /dashboard       → main dashboard (requires login)
  POST      /predict         → ML prediction API  → returns JSON
  POST      /resume          → Resume NLP API     → returns JSON
  POST      /chat            → Chatbot API        → returns JSON
  GET       /api/stats       → aggregate DB stats → returns JSON
  GET       /api/history     → prediction history → returns JSON

RUN: python app.py
"""

from flask import (Flask, render_template, request,
                   redirect, session, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import numpy as np
import json
from db              import get_db
from resume_analyzer import analyze_resume
from chatbot         import get_chatbot_response

# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key         = "placement_ai_secret_v2_2024"
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024   # 2 MB max upload

# Load ML model once at startup (loaded into RAM — fast for all requests)
try:
    model = pickle.load(open("placement_model.pkl", "rb"))
    print("✅ ML model loaded")
except FileNotFoundError:
    model = None
    print("⚠️  placement_model.pkl not found — run: python model.py")


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return redirect("/dashboard" if "user_id" in session else "/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    GET  → show register form
    POST → validate → hash password → INSERT into users table → redirect to login

    Security note: generate_password_hash() uses Werkzeug's PBKDF2 algorithm.
    Even if DB is hacked, passwords can't be reversed.
    """
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            try:
                db     = get_db()
                cursor = db.cursor()
                hashed = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed)
                )
                db.commit()
                return redirect("/login?registered=1")
            except Exception:
                error = "Username already taken. Please choose another."

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  → show login form
    POST → fetch user → check_password_hash → set session → redirect to dashboard
    """
    error      = None
    registered = request.args.get("registered")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db     = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = %s",
                       (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session.permanent    = True
            session["user_id"]   = user[0]
            session["username"]  = user[1]
            return redirect("/dashboard")
        else:
            error = "Invalid username or password. Please try again."

    return render_template("login.html", error=error, registered=registered)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/dashboard")
def dashboard():
    """
    Protected route — redirects to /login if not logged in.
    Passes username to template for personalised greeting.
    History is loaded via AJAX (/api/history) so the page loads fast.
    """
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html", username=session["username"])


# ═══════════════════════════════════════════════════════════════════════════════
# API: PREDICT  (ML Prediction Engine)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/predict", methods=["POST"])
def predict():
    """
    POST JSON/Form → ML prediction → skill gap → role recommendation → save to DB → return JSON

    WT     : REST POST endpoint, JSON response
    AI     : Random Forest predict + predict_proba
    DSBDA  : Data validation, DB insert with all fields
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if not model:
        return jsonify({"error": "Model not loaded. Run: python model.py"}), 500

    # ── Parse inputs ─────────────────────────────────────────────────────────
    try:
        cgpa          = float(request.form.get("cgpa", 0))
        internships   = int(request.form.get("internships", 0))
        projects      = int(request.form.get("projects", 0))
        aptitude      = float(request.form.get("aptitude", 0))
        communication = float(request.form.get("communication", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input values"}), 400

    # ── Validate ranges ───────────────────────────────────────────────────────
    if not (0 <= cgpa <= 10 and 0 <= aptitude <= 100 and 0 <= communication <= 100):
        return jsonify({"error": "Values out of range"}), 400

    # ── ML Prediction ─────────────────────────────────────────────────────────
    features   = np.array([[cgpa, internships, projects, aptitude, communication]])
    prediction = model.predict(features)[0]
    proba      = model.predict_proba(features)[0]

    result         = "Placed" if prediction == 1 else "Not Placed"
    placed_prob    = round(proba[1] * 100, 1)
    not_placed_prob = round(proba[0] * 100, 1)
    confidence     = round(max(proba) * 100, 1)

    # ── AI Recommendation Engine ──────────────────────────────────────────────
    suggestions = []
    if cgpa < 6.5:
        suggestions.append("Improve CGPA above 6.5 – target 7.5+ for better companies")
    elif cgpa < 7.5:
        suggestions.append("Good CGPA! Push towards 8+ for product companies")
    if aptitude < 55:
        suggestions.append("Practise aptitude daily – IndiaBix, PrepInsta (30 min/day)")
    elif aptitude < 70:
        suggestions.append("Aptitude is average – aim for 75+ through regular practice")
    if communication < 55:
        suggestions.append("Work on communication: join Toastmasters or speak English daily")
    elif communication < 70:
        suggestions.append("Good communication – practise group discussion topics weekly")
    if internships == 0:
        suggestions.append("Get at least 1 internship – even virtual/remote counts")
    if projects < 2:
        suggestions.append("Build 2+ deployed projects with GitHub links")
    elif projects < 4:
        suggestions.append("Projects look good! Add 1 AI/ML project to stand out")
    if not suggestions:
        suggestions.append("Outstanding profile! Focus on FAANG-level DSA practice")

    # ── Skill Gap Analysis ────────────────────────────────────────────────────
    skill_gap = []
    if cgpa < 7.0:
        skill_gap.append("Academic performance")
    if aptitude < 60:
        skill_gap.append("Quantitative aptitude")
    if communication < 60:
        skill_gap.append("Communication skills")
    if internships == 0:
        skill_gap.append("Practical work experience")
    if projects < 2:
        skill_gap.append("Project portfolio")

    # ── Role Recommendation ───────────────────────────────────────────────────
    role = _recommend_role(cgpa, aptitude, communication, projects, internships)

    # ── Feature Importances from model ───────────────────────────────────────
    feature_names = ["CGPA", "Internships", "Projects", "Aptitude", "Communication"]
    importances   = [round(float(v)*100, 1) for v in model.feature_importances_]

    suggestion_text = " | ".join(suggestions)
    skill_gap_text  = ", ".join(skill_gap) if skill_gap else "No major gaps identified"

    # ── Save to DB ────────────────────────────────────────────────────────────
    try:
        db     = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO predictions
               (user_id,cgpa,internships,projects,aptitude,communication,
                result,confidence,suggestion,skill_gap,role_rec)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (session["user_id"], cgpa, internships, projects, aptitude,
             communication, result, confidence, suggestion_text,
             skill_gap_text, role)
        )
        db.commit()
    except Exception as e:
        print(f"DB save error: {e}")

    return jsonify({
        "result":           result,
        "confidence":       confidence,
        "placed_prob":      placed_prob,
        "not_placed_prob":  not_placed_prob,
        "suggestion":       suggestion_text,
        "suggestions_list": suggestions,
        "skill_gap":        skill_gap_text,
        "skill_gap_list":   skill_gap,
        "role":             role,
        "feature_names":    feature_names,
        "importances":      importances,
        "input": {
            "cgpa": cgpa, "internships": internships,
            "projects": projects, "aptitude": aptitude,
            "communication": communication
        }
    })


def _recommend_role(cgpa, aptitude, communication, projects, internships):
    """
    Rule-based role recommendation engine.
    Returns the most suitable job role based on profile.
    """
    score = (cgpa / 10) * 40 + (aptitude / 100) * 30 + (communication / 100) * 30

    if cgpa >= 8.5 and aptitude >= 80 and projects >= 3:
        return "Software Development Engineer (Product Company)"
    elif cgpa >= 7.5 and aptitude >= 70:
        return "Software Developer / Full Stack Developer"
    elif projects >= 4 or internships >= 2:
        return "Full Stack / Backend Developer"
    elif aptitude >= 75:
        return "Data Analyst / Business Analyst"
    elif communication >= 75:
        return "Technical Consultant / Business Analyst"
    elif score >= 60:
        return "Junior Developer / Associate Engineer"
    else:
        return "Support Engineer / Trainee"


# ═══════════════════════════════════════════════════════════════════════════════
# API: RESUME ANALYZER  (NLP)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/resume", methods=["POST"])
def resume():
    """
    POST multipart/form-data → read .txt resume file → NLP analysis → save → return JSON

    WT    : File upload (multipart/form-data), REST API
    AI    : NLP keyword extraction, scoring algorithm
    DSBDA : Save analysis results to DB
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Only accept .txt for simplicity (extendable to PDF with pdfminer)
    if not file.filename.lower().endswith(".txt"):
        return jsonify({"error": "Please upload a .txt file. Copy your resume text into a .txt file."}), 400

    text   = file.read().decode("utf-8", errors="ignore")
    result = analyze_resume(text)

    # Save to DB
    try:
        skills_str = ", ".join(result["skills"])
        sugg_str   = " | ".join(result["suggestions"])
        db     = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO resume_analyses (user_id, filename, score, skills, suggestions)
               VALUES (%s, %s, %s, %s, %s)""",
            (session["user_id"], file.filename,
             result["score"], skills_str, sugg_str)
        )
        db.commit()
    except Exception as e:
        print(f"Resume DB error: {e}")

    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════════════════
# API: CHATBOT
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/chat", methods=["POST"])
def chat():
    """
    POST JSON {message: "..."} → intent detection → response → save to DB → return JSON

    WT  : REST POST, JSON request & response
    AI  : Intent-based conversational AI
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data    = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    response = get_chatbot_response(message)

    # Save chat to DB
    try:
        db     = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO chat_logs (user_id, message, response) VALUES (%s, %s, %s)",
            (session["user_id"], message, response)
        )
        db.commit()
    except Exception as e:
        print(f"Chat DB error: {e}")

    return jsonify({"response": response})


# ═══════════════════════════════════════════════════════════════════════════════
# API: STATS & HISTORY  (DSBDA Analytics)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/stats")
def stats():
    """
    Returns aggregate statistics from predictions table.
    Used to populate dashboard stat cards and charts.
    DSBDA concept: aggregation queries (COUNT, AVG, GROUP BY)
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        db     = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT result, COUNT(*) as cnt FROM predictions GROUP BY result")
        rows   = cursor.fetchall()
        counts = {r[0]: r[1] for r in rows}

        cursor.execute(
            "SELECT AVG(cgpa), AVG(aptitude), AVG(communication), AVG(confidence) FROM predictions"
        )
        avgs = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        return jsonify({
            "placed":       counts.get("Placed", 0),
            "not_placed":   counts.get("Not Placed", 0),
            "total_users":  total_users,
            "avg_cgpa":     round(avgs[0] or 0, 2),
            "avg_aptitude": round(avgs[1] or 0, 2),
            "avg_comm":     round(avgs[2] or 0, 2),
            "avg_confidence": round(avgs[3] or 0, 1),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history")
def history():
    """
    Returns this user's last 15 predictions as JSON array.
    Called via AJAX on page load so history always shows fresh data.
    FIX for the "history not showing" bug — now fully AJAX-driven.
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        db     = get_db()
        cursor = db.cursor()
        cursor.execute(
            """SELECT id, cgpa, internships, projects, aptitude, communication,
                      result, confidence, suggestion, skill_gap, role_rec,
                      DATE_FORMAT(created_at, '%d %b %Y %H:%i') as dt
               FROM predictions
               WHERE user_id = %s
               ORDER BY created_at DESC
               LIMIT 15""",
            (session["user_id"],)
        )
        rows = cursor.fetchall()
        cols = ["id","cgpa","internships","projects","aptitude","communication",
                "result","confidence","suggestion","skill_gap","role_rec","created_at"]
        return jsonify([dict(zip(cols, r)) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)