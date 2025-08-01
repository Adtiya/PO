import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from src.routes.reasoning import reasoning_bp
from src.routes.objects import objects_bp

# Initialize database
db = SQLAlchemy()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
# 🔐 SECURITY: Load secret from environment
SECRET_KEY = os.getenv('OBR_SERVICE_SECRET')
if not SECRET_KEY:
    raise ValueError("OBR_SERVICE_SECRET environment variable is required")
app.config['SECRET_KEY'] = SECRET_KEY

# Enable CORS for all routes
# 🌐 CORS: Secure origins only
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

# Register blueprints
app.register_blueprint(reasoning_bp, url_prefix='/api')
app.register_blueprint(objects_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "service": "OBR (Object-Based Reasoning) Service",
        "status": "healthy",
        "version": "1.0.0"
    })

# Service info endpoint
@app.route('/api/info')
def service_info():
    return jsonify({
        "service_name": "Object-Based Reasoning Service",
        "description": "Provides intelligent reasoning capabilities over objects, entities, and relationships",
        "version": "1.0.0",
        "endpoints": [
            "/api/objects",
            "/api/reasoning/analyze",
            "/api/reasoning/relationships",
            "/api/reasoning/inference"
        ]
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
