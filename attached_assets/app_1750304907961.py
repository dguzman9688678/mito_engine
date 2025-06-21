import os
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from config import config
from logging_setup import logger
from project_managers import (
    SoftwareProjectManager,
    AIMLProjectManager,
    MediaProjectManager,
    HealthcareProjectManager,
    FinanceProjectManager,
)
from file_processor import AdvancedFileProcessor
from security import AdvancedSecurityManager
from database import db_manager

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
CORS(app, origins=["*"])
limiter = Limiter(app, key_func=get_remote_address, default_limits=[config.RATELIMIT_DEFAULT], storage_uri=config.REDIS_URL)
cache = Cache(app, config={
    'CACHE_TYPE': config.CACHE_TYPE,
    'CACHE_REDIS_URL': config.REDIS_URL,
    'CACHE_DEFAULT_TIMEOUT': config.CACHE_DEFAULT_TIMEOUT
})

software_manager = SoftwareProjectManager()
aiml_manager = AIMLProjectManager()
media_manager = MediaProjectManager()
healthcare_manager = HealthcareProjectManager()
finance_manager = FinanceProjectManager()
file_processor = AdvancedFileProcessor()
security_manager = AdvancedSecurityManager()

@app.route("/")
def home():
    platform_info = {
        "name": config.PLATFORM_NAME,
        "version": config.PLATFORM_VERSION,
        "creator": config.PLATFORM_CREATOR,
        "contact": config.PLATFORM_CONTACT,
        "copyright": f"2025 {config.PLATFORM_CREATOR} - All Rights Reserved"
    }
    projects = []  # Would load from DB in production
    features = [
        "AI Project Management", "Advanced File Processing", "Multi-Industry Support",
        "Real-time Analytics", "Secure Authentication"
    ]
    industries = [
        "software", "ai/ml", "media", "healthcare", "finance"
    ]
    return render_template("index.html",
        platform_info=platform_info,
        project_count=len(projects),
        features_count=len(features),
        industries=industries
    )

@app.route("/api/project/initialize", methods=["POST"])
def api_initialize_project():
    data = request.json
    industry = data.get("industry", "").lower()
    if industry == "software":
        manager = software_manager
    elif industry == "ai/ml":
        manager = aiml_manager
    elif industry == "media":
        manager = media_manager
    elif industry == "healthcare":
        manager = healthcare_manager
    elif industry == "finance":
        manager = finance_manager
    else:
        return jsonify({"error": "Invalid industry"}), 400
    plan = manager.initialize_project(data.get("project_data", {}))
    return jsonify(plan)

@app.route("/api/file/analyze", methods=["POST"])
def api_file_analyze():
    file = request.files["file"]
    file_type = file.filename.split(".")[-1].lower()
    user_id = request.form.get("user_id", "anonymous")
    save_path = os.path.join(config.UPLOAD_FOLDER, file.filename)
    Path(config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    file.save(save_path)
    result = file_processor.process_file(save_path, file_type, user_id)
    return jsonify(result)

@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    data = request.json
    user_id = data.get("user_id")
    password = data.get("password")
    # Dummy logic, production would check DB
    hash_pw = security_manager.hash_password("testpass")
    if security_manager.verify_password(password, hash_pw):
        token = security_manager.generate_jwt_token(user_id, "user")
        return jsonify({"token": token})
    else:
        security_manager.log_auth_attempt(user_id, False)
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/ping")
def api_ping():
    return jsonify({"pong": True, "timestamp": datetime.utcnow().isoformat()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=config.DEBUG)