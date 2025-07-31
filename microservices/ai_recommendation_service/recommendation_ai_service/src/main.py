import os
import sys
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import openai
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.models.user import db

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'ai-recommendation-service-secret-key-change-in-production'

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

class AIRecommendationEngine:
    """Advanced AI-powered recommendation system"""
    
    @staticmethod
    def content_based_recommendations(user_profile: Dict, items: List[Dict], top_k: int = 5) -> Dict:
        """Generate content-based recommendations"""
        try:
            if not items or len(items) == 0:
                return {"recommendations": [], "method": "content_based"}
            
            # Extract user preferences
            user_interests = user_profile.get('interests', [])
            user_categories = user_profile.get('categories', [])
            
            # Score items based on content similarity
            scored_items = []
            for item in items:
                score = 0
                item_tags = item.get('tags', [])
                item_category = item.get('category', '')
                item_description = item.get('description', '')
                
                # Interest matching
                for interest in user_interests:
                    if interest.lower() in item_description.lower():
                        score += 2
                    if interest.lower() in [tag.lower() for tag in item_tags]:
                        score += 3
                
                # Category matching
                if item_category in user_categories:
                    score += 5
                
                # Add item with score
                scored_items.append({
                    **item,
                    "recommendation_score": score,
                    "match_reasons": []
                })
            
            # Sort by score and return top k
            scored_items.sort(key=lambda x: x['recommendation_score'], reverse=True)
            recommendations = scored_items[:top_k]
            
            return {
                "recommendations": recommendations,
                "method": "content_based",
                "total_items_analyzed": len(items),
                "user_profile_used": user_profile
            }
            
        except Exception as e:
            return {"recommendations": [], "error": str(e)}
    
    @staticmethod
    def collaborative_filtering(user_id: str, user_interactions: List[Dict], all_interactions: List[Dict], top_k: int = 5) -> Dict:
        """Generate collaborative filtering recommendations"""
        try:
            # Create user-item interaction matrix
            users = list(set([interaction['user_id'] for interaction in all_interactions]))
            items = list(set([interaction['item_id'] for interaction in all_interactions]))
            
            if user_id not in users or len(items) == 0:
                return {"recommendations": [], "method": "collaborative_filtering"}
            
            # Create interaction matrix
            user_item_matrix = {}
            for user in users:
                user_item_matrix[user] = {}
                for item in items:
                    user_item_matrix[user][item] = 0
            
            # Fill matrix with interactions
            for interaction in all_interactions:
                uid = interaction['user_id']
                iid = interaction['item_id']
                rating = interaction.get('rating', 1)
                user_item_matrix[uid][iid] = rating
            
            # Find similar users
            target_user_vector = [user_item_matrix[user_id][item] for item in items]
            similar_users = []
            
            for other_user in users:
                if other_user != user_id:
                    other_user_vector = [user_item_matrix[other_user][item] for item in items]
                    
                    # Calculate cosine similarity
                    if np.sum(target_user_vector) > 0 and np.sum(other_user_vector) > 0:
                        similarity = cosine_similarity([target_user_vector], [other_user_vector])[0][0]
                        similar_users.append((other_user, similarity))
            
            # Sort by similarity
            similar_users.sort(key=lambda x: x[1], reverse=True)
            
            # Generate recommendations based on similar users
            recommendations = []
            target_user_items = set([item for item in items if user_item_matrix[user_id][item] > 0])
            
            for similar_user, similarity in similar_users[:5]:  # Top 5 similar users
                for item in items:
                    if item not in target_user_items and user_item_matrix[similar_user][item] > 0:
                        recommendations.append({
                            "item_id": item,
                            "recommendation_score": similarity * user_item_matrix[similar_user][item],
                            "similar_user": similar_user,
                            "similarity": similarity
                        })
            
            # Remove duplicates and sort
            unique_recommendations = {}
            for rec in recommendations:
                item_id = rec['item_id']
                if item_id not in unique_recommendations or rec['recommendation_score'] > unique_recommendations[item_id]['recommendation_score']:
                    unique_recommendations[item_id] = rec
            
            final_recommendations = list(unique_recommendations.values())
            final_recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            return {
                "recommendations": final_recommendations[:top_k],
                "method": "collaborative_filtering",
                "similar_users_found": len(similar_users),
                "total_users_analyzed": len(users)
            }
            
        except Exception as e:
            return {"recommendations": [], "error": str(e)}
    
    @staticmethod
    def ai_powered_recommendations(user_profile: Dict, context: str, domain: str = "general") -> Dict:
        """Generate AI-powered personalized recommendations"""
        try:
            prompt = f"""
            Generate personalized recommendations for a user based on their profile and context.
            
            User Profile: {json.dumps(user_profile, indent=2)}
            Context: {context}
            Domain: {domain}
            
            Please provide recommendations in JSON format with:
            - recommendations: array of recommendation objects with:
              - title: recommendation title
              - description: detailed description
              - category: category/type
              - confidence: confidence score (0-1)
              - reasoning: why this is recommended
              - priority: high/medium/low
            - personalization_factors: factors used for personalization
            - recommendation_strategy: strategy used
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert recommendation system. Provide personalized recommendations in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.6
            )
            
            result = response.choices[0].message.content
            try:
                parsed_result = json.loads(result)
                parsed_result["method"] = "ai_powered"
                return parsed_result
            except:
                return {
                    "recommendations": [
                        {
                            "title": "AI Analysis Complete",
                            "description": result,
                            "category": "general",
                            "confidence": 0.7,
                            "reasoning": "AI-generated recommendation",
                            "priority": "medium"
                        }
                    ],
                    "method": "ai_powered",
                    "raw_response": result
                }
                
        except Exception as e:
            return {
                "recommendations": [],
                "error": str(e),
                "method": "ai_powered"
            }
    
    @staticmethod
    def hybrid_recommendations(user_profile: Dict, items: List[Dict], user_interactions: List[Dict], all_interactions: List[Dict], context: str = "", top_k: int = 5) -> Dict:
        """Generate hybrid recommendations combining multiple methods"""
        try:
            user_id = user_profile.get('user_id', 'unknown')
            
            # Get recommendations from different methods
            content_recs = AIRecommendationEngine.content_based_recommendations(user_profile, items, top_k * 2)
            collab_recs = AIRecommendationEngine.collaborative_filtering(user_id, user_interactions, all_interactions, top_k * 2)
            ai_recs = AIRecommendationEngine.ai_powered_recommendations(user_profile, context)
            
            # Combine and weight recommendations
            all_recommendations = []
            
            # Add content-based recommendations (weight: 0.4)
            for rec in content_recs.get('recommendations', []):
                rec['method'] = 'content_based'
                rec['weighted_score'] = rec.get('recommendation_score', 0) * 0.4
                all_recommendations.append(rec)
            
            # Add collaborative filtering recommendations (weight: 0.3)
            for rec in collab_recs.get('recommendations', []):
                rec['method'] = 'collaborative_filtering'
                rec['weighted_score'] = rec.get('recommendation_score', 0) * 0.3
                all_recommendations.append(rec)
            
            # Add AI recommendations (weight: 0.3)
            for rec in ai_recs.get('recommendations', []):
                rec['method'] = 'ai_powered'
                rec['weighted_score'] = rec.get('confidence', 0.5) * 0.3
                all_recommendations.append(rec)
            
            # Sort by weighted score
            all_recommendations.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
            
            # Remove duplicates and select top k
            seen_items = set()
            final_recommendations = []
            
            for rec in all_recommendations:
                item_id = rec.get('item_id') or rec.get('title', '')
                if item_id not in seen_items and len(final_recommendations) < top_k:
                    seen_items.add(item_id)
                    final_recommendations.append(rec)
            
            return {
                "recommendations": final_recommendations,
                "method": "hybrid",
                "methods_used": ["content_based", "collaborative_filtering", "ai_powered"],
                "total_candidates": len(all_recommendations),
                "content_based_count": len(content_recs.get('recommendations', [])),
                "collaborative_count": len(collab_recs.get('recommendations', [])),
                "ai_powered_count": len(ai_recs.get('recommendations', []))
            }
            
        except Exception as e:
            return {"recommendations": [], "error": str(e)}

# AI Recommendation API Routes
@app.route('/api/recommendations/content-based', methods=['POST'])
def content_based_recommendations():
    """Generate content-based recommendations"""
    try:
        data = request.get_json()
        if not data or 'user_profile' not in data or 'items' not in data:
            return jsonify({"error": "User profile and items are required"}), 400
        
        user_profile = data['user_profile']
        items = data['items']
        top_k = data.get('top_k', 5)
        
        result = AIRecommendationEngine.content_based_recommendations(user_profile, items, top_k)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Recommendation Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations/collaborative', methods=['POST'])
def collaborative_filtering():
    """Generate collaborative filtering recommendations"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data or 'user_interactions' not in data or 'all_interactions' not in data:
            return jsonify({"error": "User ID, user interactions, and all interactions are required"}), 400
        
        user_id = data['user_id']
        user_interactions = data['user_interactions']
        all_interactions = data['all_interactions']
        top_k = data.get('top_k', 5)
        
        result = AIRecommendationEngine.collaborative_filtering(user_id, user_interactions, all_interactions, top_k)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Recommendation Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations/ai-powered', methods=['POST'])
def ai_powered_recommendations():
    """Generate AI-powered recommendations"""
    try:
        data = request.get_json()
        if not data or 'user_profile' not in data:
            return jsonify({"error": "User profile is required"}), 400
        
        user_profile = data['user_profile']
        context = data.get('context', '')
        domain = data.get('domain', 'general')
        
        result = AIRecommendationEngine.ai_powered_recommendations(user_profile, context, domain)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Recommendation Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations/hybrid', methods=['POST'])
def hybrid_recommendations():
    """Generate hybrid recommendations"""
    try:
        data = request.get_json()
        if not data or 'user_profile' not in data:
            return jsonify({"error": "User profile is required"}), 400
        
        user_profile = data['user_profile']
        items = data.get('items', [])
        user_interactions = data.get('user_interactions', [])
        all_interactions = data.get('all_interactions', [])
        context = data.get('context', '')
        top_k = data.get('top_k', 5)
        
        result = AIRecommendationEngine.hybrid_recommendations(
            user_profile, items, user_interactions, all_interactions, context, top_k
        )
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Recommendation Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations/sample-data', methods=['GET'])
def get_sample_data():
    """Generate sample data for testing recommendations"""
    try:
        data_type = request.args.get('type', 'user_profile')
        
        if data_type == 'user_profile':
            sample_data = {
                "user_id": "user_123",
                "interests": ["technology", "artificial intelligence", "data science", "machine learning"],
                "categories": ["tech", "education", "business"],
                "demographics": {
                    "age_group": "25-34",
                    "location": "San Francisco",
                    "profession": "Software Engineer"
                },
                "behavior": {
                    "active_hours": ["9-12", "14-17"],
                    "preferred_content_length": "medium",
                    "engagement_level": "high"
                }
            }
        
        elif data_type == 'items':
            sample_data = [
                {
                    "item_id": "item_1",
                    "title": "Introduction to Machine Learning",
                    "description": "Comprehensive course on machine learning fundamentals and applications",
                    "category": "education",
                    "tags": ["machine learning", "AI", "data science", "python"],
                    "rating": 4.8
                },
                {
                    "item_id": "item_2", 
                    "title": "Advanced Python Programming",
                    "description": "Deep dive into advanced Python concepts and best practices",
                    "category": "tech",
                    "tags": ["python", "programming", "software development"],
                    "rating": 4.6
                },
                {
                    "item_id": "item_3",
                    "title": "Business Analytics with AI",
                    "description": "Using artificial intelligence for business decision making",
                    "category": "business",
                    "tags": ["business", "analytics", "AI", "decision making"],
                    "rating": 4.7
                }
            ]
        
        elif data_type == 'interactions':
            sample_data = [
                {"user_id": "user_123", "item_id": "item_1", "rating": 5, "timestamp": "2024-01-15"},
                {"user_id": "user_123", "item_id": "item_2", "rating": 4, "timestamp": "2024-01-20"},
                {"user_id": "user_456", "item_id": "item_1", "rating": 4, "timestamp": "2024-01-18"},
                {"user_id": "user_456", "item_id": "item_3", "rating": 5, "timestamp": "2024-01-22"},
                {"user_id": "user_789", "item_id": "item_2", "rating": 3, "timestamp": "2024-01-25"}
            ]
        
        else:
            sample_data = {"error": "Invalid data type"}
        
        return jsonify({
            "data": sample_data,
            "type": data_type,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "AI Recommendation Service"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "service": "AI Recommendation Service",
        "status": "healthy",
        "version": "2.0.0",
        "capabilities": [
            "content_based_filtering",
            "collaborative_filtering",
            "ai_powered_recommendations",
            "hybrid_recommendations",
            "sample_data_generation"
        ],
        "ai_model": "GPT-3.5-turbo",
        "timestamp": datetime.utcnow().isoformat()
    })

# Service info endpoint
@app.route('/api/info')
def service_info():
    return jsonify({
        "service_name": "AI Recommendation Engine Service",
        "description": "Advanced AI-powered recommendation system with multiple algorithms",
        "version": "2.0.0",
        "ai_features": [
            "Content-Based Filtering with semantic matching",
            "Collaborative Filtering with cosine similarity",
            "AI-Powered Personalized Recommendations",
            "Hybrid Recommendation System",
            "Real-time Recommendation Scoring"
        ],
        "endpoints": [
            "/api/recommendations/content-based",
            "/api/recommendations/collaborative",
            "/api/recommendations/ai-powered",
            "/api/recommendations/hybrid",
            "/api/recommendations/sample-data"
        ],
        "algorithms_used": ["Content-Based Filtering", "Collaborative Filtering", "GPT-3.5-turbo", "Cosine Similarity"],
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
    app.run(host='0.0.0.0', port=5005, debug=True)

