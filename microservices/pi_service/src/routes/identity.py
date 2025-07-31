from flask import Blueprint, request, jsonify
import uuid
from datetime import datetime, timedelta
import base64
import hashlib

identity_bp = Blueprint('identity', __name__)

# Mock identity verification data store
identity_verifications = {}
identity_documents = {}

@identity_bp.route('/identity/verify', methods=['POST'])
def verify_identity():
    """Initiate identity verification process"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'verification_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}", "status": "error"}), 400
        
        user_id = data['user_id']
        verification_type = data['verification_type']
        
        # Create verification session
        verification_id = str(uuid.uuid4())
        verification = {
            "verification_id": verification_id,
            "user_id": user_id,
            "verification_type": verification_type,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "metadata": data.get('metadata', {})
        }
        
        # Handle different verification types
        if verification_type == "email":
            verification["verification_code"] = generate_verification_code()
            verification["email"] = data.get('email')
            # In production, send email with verification code
            
        elif verification_type == "phone":
            verification["verification_code"] = generate_verification_code()
            verification["phone"] = data.get('phone')
            # In production, send SMS with verification code
            
        elif verification_type == "document":
            verification["required_documents"] = data.get('required_documents', ['id_card'])
            verification["status"] = "awaiting_documents"
            
        elif verification_type == "biometric":
            verification["biometric_type"] = data.get('biometric_type', 'face')
            verification["status"] = "awaiting_biometric"
            
        identity_verifications[verification_id] = verification
        
        return jsonify({
            "verification": {
                "verification_id": verification_id,
                "status": verification["status"],
                "verification_type": verification_type,
                "expires_at": verification["expires_at"],
                "next_step": get_next_step(verification)
            },
            "message": "Identity verification initiated",
            "status": "success"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@identity_bp.route('/identity/verify/<verification_id>/submit', methods=['POST'])
def submit_verification(verification_id):
    """Submit verification data"""
    try:
        if verification_id not in identity_verifications:
            return jsonify({"error": "Verification session not found", "status": "error"}), 404
        
        verification = identity_verifications[verification_id]
        
        # Check if verification is still valid
        if datetime.fromisoformat(verification["expires_at"]) < datetime.utcnow():
            verification["status"] = "expired"
            return jsonify({"error": "Verification session expired", "status": "error"}), 400
        
        # Check attempt limits
        if verification["attempts"] >= verification["max_attempts"]:
            verification["status"] = "failed"
            return jsonify({"error": "Maximum attempts exceeded", "status": "error"}), 400
        
        data = request.get_json()
        verification["attempts"] += 1
        
        # Handle verification submission based on type
        verification_type = verification["verification_type"]
        
        if verification_type in ["email", "phone"]:
            submitted_code = data.get('verification_code')
            expected_code = verification.get('verification_code')
            
            if submitted_code == expected_code:
                verification["status"] = "verified"
                verification["verified_at"] = datetime.utcnow().isoformat()
            else:
                verification["status"] = "failed" if verification["attempts"] >= verification["max_attempts"] else "pending"
                
        elif verification_type == "document":
            documents = data.get('documents', [])
            verification["submitted_documents"] = documents
            verification["status"] = "under_review"
            
            # Mock document verification
            for doc in documents:
                doc_id = str(uuid.uuid4())
                identity_documents[doc_id] = {
                    "document_id": doc_id,
                    "verification_id": verification_id,
                    "document_type": doc.get('type'),
                    "document_data": doc.get('data'),  # Base64 encoded in production
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "status": "pending_review"
                }
                
        elif verification_type == "biometric":
            biometric_data = data.get('biometric_data')
            verification["biometric_hash"] = hashlib.sha256(
                biometric_data.encode() if isinstance(biometric_data, str) else str(biometric_data).encode()
            ).hexdigest()
            verification["status"] = "under_review"
        
        verification["updated_at"] = datetime.utcnow().isoformat()
        
        return jsonify({
            "verification": {
                "verification_id": verification_id,
                "status": verification["status"],
                "attempts_remaining": verification["max_attempts"] - verification["attempts"],
                "next_step": get_next_step(verification)
            },
            "message": "Verification data submitted",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@identity_bp.route('/identity/verify/<verification_id>/status', methods=['GET'])
def get_verification_status(verification_id):
    """Get verification status"""
    try:
        if verification_id not in identity_verifications:
            return jsonify({"error": "Verification session not found", "status": "error"}), 404
        
        verification = identity_verifications[verification_id]
        
        return jsonify({
            "verification": {
                "verification_id": verification_id,
                "user_id": verification["user_id"],
                "verification_type": verification["verification_type"],
                "status": verification["status"],
                "created_at": verification["created_at"],
                "expires_at": verification["expires_at"],
                "attempts": verification["attempts"],
                "max_attempts": verification["max_attempts"],
                "verified_at": verification.get("verified_at"),
                "next_step": get_next_step(verification)
            },
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@identity_bp.route('/identity/documents', methods=['POST'])
def upload_document():
    """Upload identity document"""
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'document_type', 'document_data']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}", "status": "error"}), 400
        
        document_id = str(uuid.uuid4())
        document = {
            "document_id": document_id,
            "user_id": data['user_id'],
            "document_type": data['document_type'],
            "document_name": data.get('document_name'),
            "document_data": data['document_data'],  # Base64 encoded
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "pending_review",
            "metadata": data.get('metadata', {}),
            "expiry_date": data.get('expiry_date'),
            "issuing_authority": data.get('issuing_authority')
        }
        
        identity_documents[document_id] = document
        
        return jsonify({
            "document": {
                "document_id": document_id,
                "status": document["status"],
                "uploaded_at": document["uploaded_at"]
            },
            "message": "Document uploaded successfully",
            "status": "success"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@identity_bp.route('/identity/documents/<user_id>', methods=['GET'])
def get_user_documents(user_id):
    """Get all documents for a user"""
    try:
        user_documents = [
            doc for doc in identity_documents.values() 
            if doc["user_id"] == user_id
        ]
        
        # Remove sensitive data from response
        safe_documents = []
        for doc in user_documents:
            safe_doc = {
                "document_id": doc["document_id"],
                "document_type": doc["document_type"],
                "document_name": doc.get("document_name"),
                "uploaded_at": doc["uploaded_at"],
                "status": doc["status"],
                "expiry_date": doc.get("expiry_date"),
                "issuing_authority": doc.get("issuing_authority")
            }
            safe_documents.append(safe_doc)
        
        return jsonify({
            "documents": safe_documents,
            "total_count": len(safe_documents),
            "user_id": user_id,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@identity_bp.route('/identity/documents/<document_id>/review', methods=['POST'])
def review_document(document_id):
    """Review and approve/reject document"""
    try:
        if document_id not in identity_documents:
            return jsonify({"error": "Document not found", "status": "error"}), 404
        
        data = request.get_json()
        document = identity_documents[document_id]
        
        review_action = data.get('action')  # 'approve' or 'reject'
        review_notes = data.get('notes', '')
        reviewer_id = data.get('reviewer_id')
        
        if review_action == 'approve':
            document["status"] = "approved"
        elif review_action == 'reject':
            document["status"] = "rejected"
        else:
            return jsonify({"error": "Invalid review action", "status": "error"}), 400
        
        document["reviewed_at"] = datetime.utcnow().isoformat()
        document["reviewer_id"] = reviewer_id
        document["review_notes"] = review_notes
        
        return jsonify({
            "document": {
                "document_id": document_id,
                "status": document["status"],
                "reviewed_at": document["reviewed_at"],
                "review_notes": review_notes
            },
            "message": f"Document {review_action}d successfully",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

def generate_verification_code():
    """Generate 6-digit verification code"""
    import random
    return str(random.randint(100000, 999999))

def get_next_step(verification):
    """Get next step for verification process"""
    status = verification["status"]
    verification_type = verification["verification_type"]
    
    if status == "pending":
        if verification_type in ["email", "phone"]:
            return "Enter verification code"
        elif verification_type == "document":
            return "Upload required documents"
        elif verification_type == "biometric":
            return "Provide biometric data"
    elif status == "awaiting_documents":
        return "Upload required documents"
    elif status == "awaiting_biometric":
        return "Provide biometric data"
    elif status == "under_review":
        return "Wait for review completion"
    elif status == "verified":
        return "Verification complete"
    elif status == "failed":
        return "Verification failed - contact support"
    elif status == "expired":
        return "Start new verification"
    
    return "Contact support"

