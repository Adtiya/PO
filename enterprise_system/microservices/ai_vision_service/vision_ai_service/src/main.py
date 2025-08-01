import os
import sys
import json
import base64
import openai
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image
import io

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Initialize database
db = SQLAlchemy()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
# 🔐 SECURITY: Load secret from environment
SECRET_KEY = os.getenv('AI_VISION_SERVICE_SECRET')
if not SECRET_KEY:
    raise ValueError("AI_VISION_SERVICE_SECRET environment variable is required")
app.config['SECRET_KEY'] = SECRET_KEY

# Enable CORS for all routes
# 🌐 CORS: Secure origins only
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize OpenAI client (using environment variables)
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

with app.app_context():
    db.create_all()

class AIVisionProcessor:
    """Advanced AI-powered computer vision capabilities"""
    
    @staticmethod
    def analyze_image(image_data: str, analysis_type: str = "comprehensive") -> Dict:
        """Analyze image using AI vision capabilities"""
        try:
            # Prepare the message for GPT-4 Vision
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze this image and provide a {analysis_type} analysis. Return a JSON response with description, objects_detected, colors, mood, and technical_details."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "description": result,
                    "objects_detected": [],
                    "colors": [],
                    "mood": "neutral",
                    "technical_details": {},
                    "raw_response": result
                }
        except Exception as e:
            return {
                "description": "Error analyzing image",
                "objects_detected": [],
                "colors": [],
                "mood": "unknown",
                "technical_details": {},
                "error": str(e)
            }
    
    @staticmethod
    def detect_objects(image_data: str) -> Dict:
        """Detect and identify objects in image"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Detect and list all objects in this image. Return a JSON response with objects array containing name, confidence, and location description for each object."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=400,
                temperature=0.2
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "objects": [],
                    "raw_response": result
                }
        except Exception as e:
            return {
                "objects": [],
                "error": str(e)
            }
    
    @staticmethod
    def extract_text(image_data: str) -> Dict:
        """Extract text from image (OCR)"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text visible in this image. Return a JSON response with extracted_text, text_regions (array of text blocks), and confidence."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=400,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "extracted_text": result,
                    "text_regions": [],
                    "confidence": 0.5
                }
        except Exception as e:
            return {
                "extracted_text": "",
                "text_regions": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    @staticmethod
    def classify_image(image_data: str, categories: List[str]) -> Dict:
        """Classify image into predefined categories"""
        try:
            categories_str = ", ".join(categories)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Classify this image into one of these categories: {categories_str}. Return a JSON response with predicted_category, confidence (0-1), and reasoning."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=300,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "predicted_category": categories[0] if categories else "unknown",
                    "confidence": 0.5,
                    "reasoning": result
                }
        except Exception as e:
            return {
                "predicted_category": "error",
                "confidence": 0.0,
                "reasoning": str(e),
                "error": str(e)
            }

def validate_image_data(image_data: str) -> bool:
    """Validate base64 image data"""
    try:
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Try to open with PIL
        image = Image.open(io.BytesIO(image_bytes))
        return True
    except:
        return False

# AI Vision API Routes
@app.route('/api/vision/analyze', methods=['POST'])
def analyze_image():
    """Comprehensive image analysis"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "Image data is required"}), 400
        
        image_data = data['image']
        analysis_type = data.get('analysis_type', 'comprehensive')
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        if not validate_image_data(image_data):
            return jsonify({"error": "Invalid image data"}), 400
        
        result = AIVisionProcessor.analyze_image(image_data, analysis_type)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Vision Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vision/objects', methods=['POST'])
def detect_objects():
    """Detect objects in image"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "Image data is required"}), 400
        
        image_data = data['image']
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        if not validate_image_data(image_data):
            return jsonify({"error": "Invalid image data"}), 400
        
        result = AIVisionProcessor.detect_objects(image_data)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Vision Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vision/ocr', methods=['POST'])
def extract_text():
    """Extract text from image (OCR)"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "Image data is required"}), 400
        
        image_data = data['image']
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        if not validate_image_data(image_data):
            return jsonify({"error": "Invalid image data"}), 400
        
        result = AIVisionProcessor.extract_text(image_data)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Vision Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vision/classify', methods=['POST'])
def classify_image():
    """Classify image into categories"""
    try:
        data = request.get_json()
        if not data or 'image' not in data or 'categories' not in data:
            return jsonify({"error": "Image data and categories are required"}), 400
        
        image_data = data['image']
        categories = data['categories']
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        if not validate_image_data(image_data):
            return jsonify({"error": "Invalid image data"}), 400
        
        if not isinstance(categories, list) or len(categories) == 0:
            return jsonify({"error": "Categories must be a non-empty list"}), 400
        
        result = AIVisionProcessor.classify_image(image_data, categories)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Vision Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "service": "AI Vision Service",
        "status": "healthy",
        "version": "2.0.0",
        "capabilities": [
            "image_analysis",
            "object_detection",
            "text_extraction_ocr",
            "image_classification"
        ],
        "ai_model": "GPT-4-Vision",
        "timestamp": datetime.utcnow().isoformat()
    })

# Service info endpoint
@app.route('/api/info')
def service_info():
    return jsonify({
        "service_name": "AI Computer Vision Service",
        "description": "Advanced AI-powered image analysis and computer vision capabilities",
        "version": "2.0.0",
        "ai_features": [
            "Comprehensive Image Analysis",
            "Object Detection and Recognition",
            "Optical Character Recognition (OCR)",
            "Image Classification",
            "Scene Understanding"
        ],
        "endpoints": [
            "/api/vision/analyze",
            "/api/vision/objects",
            "/api/vision/ocr",
            "/api/vision/classify"
        ],
        "models_used": ["GPT-4-Vision"],
        "supported_formats": ["JPEG", "PNG", "GIF", "WebP"],
        "timestamp": datetime.utcnow().isoformat()
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
    app.run(host='0.0.0.0', port=5003, debug=True)

