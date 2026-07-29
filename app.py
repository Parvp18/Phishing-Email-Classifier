"""
PhishGuard Main Flask Application
=================================
Provides REST API endpoints and serves the frontend UI.
Handles request validation, rate limiting, and DB integration.
"""

import os
import json
import logging
from functools import wraps
from datetime import datetime, timedelta, timezone

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import pandas as pd
import email
from email.policy import default

from config import (
    API_KEYS, FLASK_SECRET_KEY, DATABASE_URL, UPLOAD_FOLDER, REPORTS_FOLDER,
    RATE_LIMIT, MODEL_VERSION, MAX_EMAIL_SIZE_BYTES, MAX_BULK_ROWS
)
from models import db, ScanResult, Feedback
from predict import PhishingPredictor
from report_generator import ReportGenerator
from scheduler import init_scheduler

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS
CORS(app)

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize Database
db.init_app(app)

with app.app_context():
    db.create_all()

# Start background scheduler
init_scheduler(app)

# Lazy-load predictor to avoid loading models twice during init
predictor = None
report_gen = ReportGenerator()

def get_predictor():
    global predictor
    if predictor is None:
        predictor = PhishingPredictor()
    return predictor

# --- Middleware / Auth ---

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # We allow browser access without API key to the web UI routes
        # For API, X-API-Key is required.
        key = request.headers.get("X-API-Key")
        if not key or key not in API_KEYS:
            return jsonify({"error": "Unauthorized. Invalid or missing X-API-Key.", "code": 401}), 401
        return f(*args, **kwargs)
    return decorated

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": f"Rate limit exceeded: {e.description}", "code": 429}), 429

@app.errorhandler(Exception)
def generic_error(e):
    logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return jsonify({"error": "Internal Server Error", "code": 500}), 500


# --- Frontend Routes ---

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", version=MODEL_VERSION)

@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html", version=MODEL_VERSION)

@app.route("/history", methods=["GET"])
def history_page():
    return render_template("history.html", version=MODEL_VERSION)


# --- API Routes ---

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "model_version": MODEL_VERSION,
        "uptime": "active"
    })

@app.route("/api/analyze", methods=["POST"])
@limiter.limit(RATE_LIMIT)
@require_api_key
def analyze_email():
    data = request.json
    if not data or "email_text" not in data:
        return jsonify({"error": "Missing 'email_text' in request body.", "code": 400}), 400
        
    text = data.get("email_text", "")
    subject = data.get("subject", "")
    sender = data.get("sender", "")
    
    if len(text.encode('utf-8')) > MAX_EMAIL_SIZE_BYTES:
        return jsonify({"error": "Email exceeds maximum size limit.", "code": 400}), 400

    pred = get_predictor()
    res = pred.analyze(text, subject, sender)
    
    if "error" in res:
        return jsonify({"error": res["error"], "code": 500}), 500

    # Save to DB
    scan_result = ScanResult(
        email_hash=res["email_hash"],
        label=res["label"],
        confidence=res["confidence"],
        risk_score=res["risk_score"],
        risk_level=res["risk_level"],
        attack_type=res["attack_type"],
        features_json=json.dumps(res["features"]),
        urls_json=json.dumps(res["urls_found"]),
        shap_json=json.dumps(res["shap_top_features"]),
        model_votes_json=json.dumps(res["model_votes"]),
        word_heatmap_json=json.dumps(res["word_heatmap"]),
        recommendation=res["recommendation"],
        sender=sender,
        subject=subject,
        email_body=text,
        scan_source=data.get("scan_source", "api"),
        analysis_time_ms=res["analysis_time_ms"]
    )
    db.session.add(scan_result)
    db.session.commit()
    
    res["id"] = scan_result.id
    return jsonify(res)


@app.route("/api/upload", methods=["POST"])
@limiter.limit(RATE_LIMIT)
@require_api_key
def upload_eml():
    if "email_file" not in request.files:
        return jsonify({"error": "No file part 'email_file'", "code": 400}), 400
        
    file = request.files["email_file"]
    if file.filename == "":
        return jsonify({"error": "No selected file", "code": 400}), 400
        
    if not file.filename.endswith(".eml"):
        return jsonify({"error": "Only .eml files are supported", "code": 400}), 400

    import uuid
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
    file.save(filepath)
    
    try:
        with open(filepath, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=default)
            
        subject = msg.get('Subject', '')
        sender = msg.get('From', '')
        
        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_content()
                    break
            # Fallback to HTML if no plain text
            if not body:
                for part in msg.walk():
                    if part.get_content_type() == 'text/html':
                        body = part.get_content()
                        break
        else:
            body = msg.get_content()
            
        # Parse logic
        pred = get_predictor()
        res = pred.analyze(body, subject, sender)
        
        if "error" in res:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": res["error"], "code": 500}), 500

        # Save to DB
        scan_result = ScanResult(
            email_hash=res["email_hash"],
            label=res["label"],
            confidence=res["confidence"],
            risk_score=res["risk_score"],
            risk_level=res["risk_level"],
            attack_type=res["attack_type"],
            features_json=json.dumps(res["features"]),
            urls_json=json.dumps(res["urls_found"]),
            shap_json=json.dumps(res["shap_top_features"]),
            model_votes_json=json.dumps(res["model_votes"]),
            word_heatmap_json=json.dumps(res["word_heatmap"]),
            recommendation=res["recommendation"],
            sender=sender,
            subject=subject,
            email_body=body,
            scan_source="upload",
            analysis_time_ms=res["analysis_time_ms"]
        )
        db.session.add(scan_result)
        db.session.commit()
        res["id"] = scan_result.id

    except Exception as e:
        logger.error(f"Error parsing .eml: {e}")
        return jsonify({"error": "Failed to parse .eml file", "code": 500}), 500
    finally:
        # Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)

    return jsonify(res)


@app.route("/api/bulk", methods=["POST"])
@limiter.limit(RATE_LIMIT)
@require_api_key
def bulk_scan():
    if "csv_file" not in request.files:
        return jsonify({"error": "No file part 'csv_file'", "code": 400}), 400
        
    file = request.files["csv_file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Only .csv files supported", "code": 400}), 400
        
    try:
        df = pd.read_csv(file)
        if "text" not in df.columns:
            return jsonify({"error": "CSV must contain a 'text' column", "code": 400}), 400
            
        df = df.head(MAX_BULK_ROWS)
        pred = get_predictor()
        
        results = []
        for idx, row in df.iterrows():
            text = str(row.get("text", ""))
            subj = str(row.get("subject", ""))
            sender = str(row.get("sender", ""))
            
            res = pred.analyze(text, subj, sender)
            res["original_id"] = str(row.get("id", idx))
            
            # Save bulk scan result to DB so history persists
            scan_result = ScanResult(
                email_hash=res["email_hash"],
                label=res["label"],
                confidence=res["confidence"],
                risk_score=res["risk_score"],
                risk_level=res["risk_level"],
                attack_type=res["attack_type"],
                features_json=json.dumps(res["features"]),
                urls_json=json.dumps(res["urls_found"]),
                shap_json=json.dumps(res["shap_top_features"]),
                model_votes_json=json.dumps(res["model_votes"]),
                word_heatmap_json=json.dumps(res["word_heatmap"]),
                recommendation=res["recommendation"],
                sender=sender,
                subject=subj,
                email_body=text,
                scan_source="bulk",
                analysis_time_ms=res["analysis_time_ms"]
            )
            db.session.add(scan_result)
            db.session.commit()
            res["id"] = scan_result.id
            
            results.append(res)
            
        # Summary stats
        total = len(results)
        phishing = sum(1 for r in results if r.get("label") == "PHISHING")
        
        return jsonify({
            "summary": {
                "total_processed": total,
                "phishing_found": phishing,
                "safe_found": total - phishing
            },
            "results": results
        })

    except Exception as e:
        logger.error(f"Error processing bulk CSV: {e}")
        return jsonify({"error": "Failed to process CSV file", "code": 500}), 500


@app.route("/api/feedback", methods=["POST"])
@require_api_key
def submit_feedback():
    data = request.json
    scan_id = data.get("scan_id")
    correct_label = data.get("correct_label")
    
    if not scan_id or correct_label not in [0, 1]:
        return jsonify({"error": "Invalid payload", "code": 400}), 400
        
    scan = ScanResult.query.get(scan_id)
    if not scan:
        return jsonify({"error": "Scan ID not found", "code": 404}), 404
        
    feedback = Feedback(scan_id=scan_id, correct_label=correct_label)
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Feedback recorded."})


@app.route("/api/report/<scan_id>", methods=["GET"])
@require_api_key
def get_pdf_report(scan_id):
    scan = ScanResult.query.get(scan_id)
    if not scan:
        return jsonify({"error": "Scan ID not found", "code": 404}), 404
        
    filepath = os.path.join(REPORTS_FOLDER, f"{scan_id}.pdf")
    
    # Generate if not exists
    if not os.path.exists(filepath):
        pdf_bytes = report_gen.generate_pdf(scan.to_dict(), scan_id)
        if b"Error" in pdf_bytes:
             return jsonify({"error": "PDF Generation failed", "code": 500}), 500
             
    return send_file(filepath, as_attachment=True, download_name=f"PhishGuard_Report_{scan_id}.pdf")


@app.route("/api/stats", methods=["GET"])
@require_api_key
def get_stats():
    total_scans = ScanResult.query.count()
    phishing = ScanResult.query.filter_by(label="PHISHING").count()
    
    avg_conf = db.session.query(db.func.avg(ScanResult.confidence)).scalar() or 0
    
    # Attack types
    attack_types_query = db.session.query(ScanResult.attack_type, db.func.count(ScanResult.id))\
        .group_by(ScanResult.attack_type).all()
    attack_types = {k: v for k, v in attack_types_query if k}
    
    # Daily counts (last 30 days)
    # Ensure thirty_days_ago is timezone-naive for SQLite matching
    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    
    # SQLite friendly date grouping
    if "sqlite" in app.config['SQLALCHEMY_DATABASE_URI']:
        daily_query = db.session.query(
            db.func.date(ScanResult.created_at).label('date'),
            ScanResult.label,
            db.func.count(ScanResult.id)
        ).filter(ScanResult.created_at >= thirty_days_ago)\
         .group_by('date', ScanResult.label).all()
    else:
        # Fallback for other DBs might require different date casting
        daily_query = []
         
    daily_counts = {}
    for date_str, label, count in daily_query:
        if date_str not in daily_counts:
            daily_counts[date_str] = {"PHISHING": 0, "SAFE": 0}
        daily_counts[date_str][label] = count

    return jsonify({
        "total_scans": total_scans,
        "phishing_detected": phishing,
        "safe_detected": total_scans - phishing,
        "avg_confidence": round(avg_conf, 1),
        "top_attack_types": attack_types,
        "daily_counts": daily_counts,
        "top_flagged_domains": [] # Omitted complex JSON parsing in SQLite for brevity
    })


@app.route("/api/history", methods=["GET"])
@require_api_key
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = ScanResult.query.order_by(ScanResult.created_at.desc())
    
    # Filters
    label_filter = request.args.get("label_filter")
    if label_filter:
        query = query.filter_by(label=label_filter.upper())
        
    search = request.args.get("search")
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                ScanResult.subject.ilike(search_term),
                ScanResult.sender.ilike(search_term),
                ScanResult.email_hash.ilike(search_term)
            )
        )
        
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    items = [item.to_dict() for item in paginated.items]
    
    return jsonify({
        "items": items,
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": page
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
