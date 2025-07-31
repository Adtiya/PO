import os
import sys
import json
import openai
from datetime import datetime
from typing import Dict, List, Optional

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.models.user import db

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'ai-nlp-service-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize OpenAI client (using environment variables)
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

with app.app_context():
    db.create_all()

class AITextProcessor:
    """Advanced AI-powered text processing capabilities"""
    
    @staticmethod
    def analyze_sentiment(text: str) -> Dict:
        """Analyze sentiment of text using AI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert. Analyze the sentiment of the given text and return a JSON response with sentiment (positive/negative/neutral), confidence (0-1), and key_emotions (array of emotions detected)."},
                    {"role": "user", "content": f"Analyze the sentiment of this text: {text}"}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "key_emotions": ["unknown"],
                    "raw_response": result
                }
        except Exception as e:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "key_emotions": ["error"],
                "error": str(e)
            }
    
    @staticmethod
    def extract_entities(text: str) -> Dict:
        """Extract named entities from text"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a named entity recognition expert. Extract entities from the given text and return a JSON response with entities categorized by type (PERSON, ORGANIZATION, LOCATION, DATE, etc.)."},
                    {"role": "user", "content": f"Extract named entities from this text: {text}"}
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "entities": {},
                    "raw_response": result
                }
        except Exception as e:
            return {
                "entities": {},
                "error": str(e)
            }
    
    @staticmethod
    def summarize_text(text: str, max_length: int = 150) -> Dict:
        """Generate intelligent text summary"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a text summarization expert. Create a concise summary of the given text in maximum {max_length} words. Return a JSON response with summary, key_points (array), and word_count."},
                    {"role": "user", "content": f"Summarize this text: {text}"}
                ],
                max_tokens=400,
                temperature=0.4
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "summary": result,
                    "key_points": [],
                    "word_count": len(result.split())
                }
        except Exception as e:
            return {
                "summary": "Error generating summary",
                "key_points": [],
                "word_count": 0,
                "error": str(e)
            }
    
    @staticmethod
    def classify_text(text: str, categories: List[str]) -> Dict:
        """Classify text into predefined categories"""
        try:
            categories_str = ", ".join(categories)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a text classification expert. Classify the given text into one of these categories: {categories_str}. Return a JSON response with predicted_category, confidence (0-1), and reasoning."},
                    {"role": "user", "content": f"Classify this text: {text}"}
                ],
                max_tokens=200,
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

# AI NLP API Routes
@app.route('/api/nlp/sentiment', methods=['POST'])
def analyze_sentiment():
    """Analyze sentiment of provided text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        text = data['text']
        if len(text.strip()) == 0:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        result = AITextProcessor.analyze_sentiment(text)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI NLP Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nlp/entities', methods=['POST'])
def extract_entities():
    """Extract named entities from text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        text = data['text']
        if len(text.strip()) == 0:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        result = AITextProcessor.extract_entities(text)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI NLP Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nlp/summarize', methods=['POST'])
def summarize_text():
    """Generate text summary"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        text = data['text']
        max_length = data.get('max_length', 150)
        
        if len(text.strip()) == 0:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        result = AITextProcessor.summarize_text(text, max_length)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI NLP Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nlp/classify', methods=['POST'])
def classify_text():
    """Classify text into categories"""
    try:
        data = request.get_json()
        if not data or 'text' not in data or 'categories' not in data:
            return jsonify({"error": "Text and categories are required"}), 400
        
        text = data['text']
        categories = data['categories']
        
        if len(text.strip()) == 0:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        if not isinstance(categories, list) or len(categories) == 0:
            return jsonify({"error": "Categories must be a non-empty list"}), 400
        
        result = AITextProcessor.classify_text(text, categories)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI NLP Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nlp/analyze', methods=['POST'])
def comprehensive_analysis():
    """Perform comprehensive text analysis"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        text = data['text']
        if len(text.strip()) == 0:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        # Perform all analyses
        sentiment = AITextProcessor.analyze_sentiment(text)
        entities = AITextProcessor.extract_entities(text)
        summary = AITextProcessor.summarize_text(text)
        
        result = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "sentiment_analysis": sentiment,
            "entity_extraction": entities,
            "text_summary": summary,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "AI NLP Service"
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "service": "AI NLP Service",
        "status": "healthy",
        "version": "2.0.0",
        "capabilities": [
            "sentiment_analysis",
            "entity_extraction", 
            "text_summarization",
            "text_classification",
            "comprehensive_analysis"
        ],
        "ai_model": "GPT-3.5-turbo",
        "timestamp": datetime.utcnow().isoformat()
    })

# Service info endpoint
@app.route('/api/info')
def service_info():
    return jsonify({
        "service_name": "AI Natural Language Processing Service",
        "description": "Advanced AI-powered text analysis and processing capabilities",
        "version": "2.0.0",
        "ai_features": [
            "Sentiment Analysis with emotion detection",
            "Named Entity Recognition",
            "Intelligent Text Summarization", 
            "Multi-category Text Classification",
            "Comprehensive Text Analysis"
        ],
        "endpoints": [
            "/api/nlp/sentiment",
            "/api/nlp/entities",
            "/api/nlp/summarize",
            "/api/nlp/classify",
            "/api/nlp/analyze"
        ],
        "models_used": ["GPT-3.5-turbo"],
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
    app.run(host='0.0.0.0', port=5002, debug=True)

