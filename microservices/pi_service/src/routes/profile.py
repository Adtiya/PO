from flask import Blueprint, request, jsonify
from src.models.user import db
import uuid
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

# Mock profile data store (in production, use proper database)
profiles = {}

@profile_bp.route('/profiles', methods=['GET'])
def get_profiles():
    """Get all user profiles"""
    try:
        # In production, implement proper pagination and filtering
        return jsonify({
            "profiles": list(profiles.values()),
            "total_count": len(profiles),
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@profile_bp.route('/profiles/<user_id>', methods=['GET'])
def get_profile(user_id):
    """Get specific user profile"""
    try:
        if user_id not in profiles:
            return jsonify({"error": "Profile not found", "status": "error"}), 404
        
        return jsonify({
            "profile": profiles[user_id],
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@profile_bp.route('/profiles', methods=['POST'])
def create_profile():
    """Create new user profile"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'first_name', 'last_name', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}", "status": "error"}), 400
        
        user_id = data['user_id']
        
        # Check if profile already exists
        if user_id in profiles:
            return jsonify({"error": "Profile already exists", "status": "error"}), 409
        
        # Create profile
        profile = {
            "user_id": user_id,
            "profile_id": str(uuid.uuid4()),
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "email": data['email'],
            "phone": data.get('phone'),
            "date_of_birth": data.get('date_of_birth'),
            "address": data.get('address', {}),
            "preferences": data.get('preferences', {}),
            "metadata": data.get('metadata', {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_verified": False,
            "verification_level": "basic"
        }
        
        profiles[user_id] = profile
        
        return jsonify({
            "profile": profile,
            "message": "Profile created successfully",
            "status": "success"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@profile_bp.route('/profiles/<user_id>', methods=['PUT'])
def update_profile(user_id):
    """Update user profile"""
    try:
        if user_id not in profiles:
            return jsonify({"error": "Profile not found", "status": "error"}), 404
        
        data = request.get_json()
        profile = profiles[user_id]
        
        # Update allowed fields
        updatable_fields = [
            'first_name', 'last_name', 'phone', 'date_of_birth', 
            'address', 'preferences', 'metadata'
        ]
        
        for field in updatable_fields:
            if field in data:
                profile[field] = data[field]
        
        profile['updated_at'] = datetime.utcnow().isoformat()
        
        return jsonify({
            "profile": profile,
            "message": "Profile updated successfully",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@profile_bp.route('/profiles/<user_id>/verify', methods=['POST'])
def verify_profile(user_id):
    """Verify user profile"""
    try:
        if user_id not in profiles:
            return jsonify({"error": "Profile not found", "status": "error"}), 404
        
        data = request.get_json()
        verification_type = data.get('verification_type', 'basic')
        verification_data = data.get('verification_data', {})
        
        profile = profiles[user_id]
        
        # Mock verification logic
        if verification_type == 'email':
            profile['email_verified'] = True
            profile['verification_level'] = 'email_verified'
        elif verification_type == 'phone':
            profile['phone_verified'] = True
            profile['verification_level'] = 'phone_verified'
        elif verification_type == 'identity':
            profile['identity_verified'] = True
            profile['verification_level'] = 'identity_verified'
            profile['verification_documents'] = verification_data.get('documents', [])
        
        profile['is_verified'] = True
        profile['updated_at'] = datetime.utcnow().isoformat()
        
        return jsonify({
            "profile": profile,
            "message": f"Profile {verification_type} verification completed",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@profile_bp.route('/profiles/<user_id>/preferences', methods=['GET'])
def get_preferences(user_id):
    """Get user preferences"""
    try:
        if user_id not in profiles:
            return jsonify({"error": "Profile not found", "status": "error"}), 404
        
        profile = profiles[user_id]
        preferences = profile.get('preferences', {})
        
        return jsonify({
            "preferences": preferences,
            "user_id": user_id,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@profile_bp.route('/profiles/<user_id>/preferences', methods=['PUT'])
def update_preferences(user_id):
    """Update user preferences"""
    try:
        if user_id not in profiles:
            return jsonify({"error": "Profile not found", "status": "error"}), 404
        
        data = request.get_json()
        profile = profiles[user_id]
        
        # Update preferences
        if 'preferences' not in profile:
            profile['preferences'] = {}
        
        profile['preferences'].update(data.get('preferences', {}))
        profile['updated_at'] = datetime.utcnow().isoformat()
        
        return jsonify({
            "preferences": profile['preferences'],
            "message": "Preferences updated successfully",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@profile_bp.route('/profiles/search', methods=['POST'])
def search_profiles():
    """Search profiles by criteria"""
    try:
        data = request.get_json()
        search_criteria = data.get('criteria', {})
        
        # Simple search implementation
        results = []
        for profile in profiles.values():
            match = True
            
            for key, value in search_criteria.items():
                if key in profile:
                    if isinstance(profile[key], str) and isinstance(value, str):
                        if value.lower() not in profile[key].lower():
                            match = False
                            break
                    elif profile[key] != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                results.append(profile)
        
        return jsonify({
            "results": results,
            "total_count": len(results),
            "search_criteria": search_criteria,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

