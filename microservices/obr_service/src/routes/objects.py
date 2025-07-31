from flask import Blueprint, request, jsonify
import uuid
from datetime import datetime

objects_bp = Blueprint('objects', __name__)

# Mock object store
objects_store = {}
object_schemas = {}

@objects_bp.route('/objects', methods=['POST'])
def create_object():
    """Create a new object in the system"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'properties']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}", "status": "error"}), 400
        
        object_id = str(uuid.uuid4())
        obj = {
            "id": object_id,
            "type": data['type'],
            "name": data.get('name', f"Object_{object_id[:8]}"),
            "description": data.get('description', ''),
            "properties": data['properties'],
            "metadata": data.get('metadata', {}),
            "tags": data.get('tags', []),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": 1,
            "status": "active"
        }
        
        # Validate against schema if exists
        schema_validation = validate_object_schema(obj)
        if not schema_validation['valid']:
            return jsonify({
                "error": "Schema validation failed",
                "validation_errors": schema_validation['errors'],
                "status": "error"
            }), 400
        
        objects_store[object_id] = obj
        
        return jsonify({
            "object": obj,
            "message": "Object created successfully",
            "status": "success"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects', methods=['GET'])
def get_objects():
    """Get all objects with optional filtering"""
    try:
        # Get query parameters
        object_type = request.args.get('type')
        tags = request.args.getlist('tags')
        status = request.args.get('status', 'active')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Filter objects
        filtered_objects = []
        for obj in objects_store.values():
            # Apply filters
            if object_type and obj['type'] != object_type:
                continue
            if status and obj['status'] != status:
                continue
            if tags and not any(tag in obj['tags'] for tag in tags):
                continue
            
            filtered_objects.append(obj)
        
        # Apply pagination
        total_count = len(filtered_objects)
        paginated_objects = filtered_objects[offset:offset + limit]
        
        return jsonify({
            "objects": paginated_objects,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/<object_id>', methods=['GET'])
def get_object(object_id):
    """Get specific object by ID"""
    try:
        if object_id not in objects_store:
            return jsonify({"error": "Object not found", "status": "error"}), 404
        
        obj = objects_store[object_id]
        
        return jsonify({
            "object": obj,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/<object_id>', methods=['PUT'])
def update_object(object_id):
    """Update existing object"""
    try:
        if object_id not in objects_store:
            return jsonify({"error": "Object not found", "status": "error"}), 404
        
        data = request.get_json()
        obj = objects_store[object_id]
        
        # Update allowed fields
        updatable_fields = ['name', 'description', 'properties', 'metadata', 'tags']
        for field in updatable_fields:
            if field in data:
                obj[field] = data[field]
        
        obj['updated_at'] = datetime.utcnow().isoformat()
        obj['version'] += 1
        
        # Validate against schema
        schema_validation = validate_object_schema(obj)
        if not schema_validation['valid']:
            return jsonify({
                "error": "Schema validation failed",
                "validation_errors": schema_validation['errors'],
                "status": "error"
            }), 400
        
        return jsonify({
            "object": obj,
            "message": "Object updated successfully",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/<object_id>', methods=['DELETE'])
def delete_object(object_id):
    """Delete object (soft delete)"""
    try:
        if object_id not in objects_store:
            return jsonify({"error": "Object not found", "status": "error"}), 404
        
        force_delete = request.args.get('force', 'false').lower() == 'true'
        
        if force_delete:
            del objects_store[object_id]
            message = "Object permanently deleted"
        else:
            objects_store[object_id]['status'] = 'deleted'
            objects_store[object_id]['deleted_at'] = datetime.utcnow().isoformat()
            message = "Object soft deleted"
        
        return jsonify({
            "message": message,
            "object_id": object_id,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/search', methods=['POST'])
def search_objects():
    """Search objects by various criteria"""
    try:
        data = request.get_json()
        
        search_criteria = data.get('criteria', {})
        search_text = data.get('text', '')
        filters = data.get('filters', {})
        
        results = []
        
        for obj in objects_store.values():
            if obj['status'] == 'deleted':
                continue
            
            match_score = 0
            
            # Text search
            if search_text:
                text_fields = [obj['name'], obj['description']]
                text_fields.extend(str(v) for v in obj['properties'].values())
                
                for field in text_fields:
                    if search_text.lower() in field.lower():
                        match_score += 1
            
            # Criteria matching
            for key, value in search_criteria.items():
                if key in obj and obj[key] == value:
                    match_score += 2
                elif key in obj['properties'] and obj['properties'][key] == value:
                    match_score += 2
            
            # Apply filters
            filter_match = True
            for filter_key, filter_value in filters.items():
                if filter_key == 'type' and obj['type'] != filter_value:
                    filter_match = False
                    break
                elif filter_key == 'tags' and not any(tag in obj['tags'] for tag in filter_value):
                    filter_match = False
                    break
            
            if match_score > 0 and filter_match:
                results.append({
                    "object": obj,
                    "match_score": match_score
                })
        
        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            "results": results,
            "total_count": len(results),
            "search_criteria": search_criteria,
            "search_text": search_text,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/schemas', methods=['POST'])
def create_object_schema():
    """Create object schema for validation"""
    try:
        data = request.get_json()
        
        required_fields = ['object_type', 'schema']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}", "status": "error"}), 400
        
        schema_id = str(uuid.uuid4())
        schema = {
            "schema_id": schema_id,
            "object_type": data['object_type'],
            "schema": data['schema'],
            "version": data.get('version', '1.0'),
            "description": data.get('description', ''),
            "is_active": data.get('is_active', True),
            "created_at": datetime.utcnow().isoformat()
        }
        
        object_schemas[data['object_type']] = schema
        
        return jsonify({
            "schema": schema,
            "message": "Object schema created successfully",
            "status": "success"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/schemas', methods=['GET'])
def get_object_schemas():
    """Get all object schemas"""
    try:
        schemas = list(object_schemas.values())
        
        return jsonify({
            "schemas": schemas,
            "total_count": len(schemas),
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/<object_id>/relationships', methods=['GET'])
def get_object_relationships(object_id):
    """Get relationships for a specific object"""
    try:
        if object_id not in objects_store:
            return jsonify({"error": "Object not found", "status": "error"}), 404
        
        # Find relationships where this object is involved
        relationships = find_object_relationships(object_id)
        
        return jsonify({
            "object_id": object_id,
            "relationships": relationships,
            "relationship_count": len(relationships),
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/<object_id>/properties/<property_name>', methods=['GET'])
def get_object_property(object_id, property_name):
    """Get specific property of an object"""
    try:
        if object_id not in objects_store:
            return jsonify({"error": "Object not found", "status": "error"}), 404
        
        obj = objects_store[object_id]
        
        if property_name not in obj['properties']:
            return jsonify({"error": "Property not found", "status": "error"}), 404
        
        return jsonify({
            "object_id": object_id,
            "property_name": property_name,
            "property_value": obj['properties'][property_name],
            "property_type": type(obj['properties'][property_name]).__name__,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/<object_id>/properties/<property_name>', methods=['PUT'])
def update_object_property(object_id, property_name):
    """Update specific property of an object"""
    try:
        if object_id not in objects_store:
            return jsonify({"error": "Object not found", "status": "error"}), 404
        
        data = request.get_json()
        obj = objects_store[object_id]
        
        old_value = obj['properties'].get(property_name)
        new_value = data.get('value')
        
        obj['properties'][property_name] = new_value
        obj['updated_at'] = datetime.utcnow().isoformat()
        obj['version'] += 1
        
        return jsonify({
            "object_id": object_id,
            "property_name": property_name,
            "old_value": old_value,
            "new_value": new_value,
            "message": "Property updated successfully",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@objects_bp.route('/objects/types', methods=['GET'])
def get_object_types():
    """Get all object types in the system"""
    try:
        types = {}
        
        for obj in objects_store.values():
            obj_type = obj['type']
            if obj_type not in types:
                types[obj_type] = {
                    "type": obj_type,
                    "count": 0,
                    "sample_properties": set()
                }
            
            types[obj_type]["count"] += 1
            types[obj_type]["sample_properties"].update(obj['properties'].keys())
        
        # Convert sets to lists for JSON serialization
        for type_info in types.values():
            type_info["sample_properties"] = list(type_info["sample_properties"])
        
        return jsonify({
            "object_types": list(types.values()),
            "total_types": len(types),
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

# Helper functions

def validate_object_schema(obj):
    """Validate object against its schema"""
    object_type = obj['type']
    
    if object_type not in object_schemas:
        return {"valid": True, "errors": []}  # No schema defined, allow all
    
    schema = object_schemas[object_type]['schema']
    errors = []
    
    # Basic schema validation (in production, use jsonschema library)
    required_properties = schema.get('required_properties', [])
    for prop in required_properties:
        if prop not in obj['properties']:
            errors.append(f"Missing required property: {prop}")
    
    property_types = schema.get('property_types', {})
    for prop, expected_type in property_types.items():
        if prop in obj['properties']:
            actual_type = type(obj['properties'][prop]).__name__
            if actual_type != expected_type:
                errors.append(f"Property {prop} should be {expected_type}, got {actual_type}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def find_object_relationships(object_id):
    """Find relationships involving the specified object"""
    # Mock relationship finding
    relationships = []
    
    # In a real implementation, this would query a relationship database
    for other_id, other_obj in objects_store.items():
        if other_id != object_id:
            # Mock relationship detection based on shared properties
            obj = objects_store[object_id]
            shared_props = set(obj['properties'].keys()) & set(other_obj['properties'].keys())
            
            if shared_props:
                relationships.append({
                    "related_object_id": other_id,
                    "relationship_type": "shared_properties",
                    "strength": len(shared_props) / max(len(obj['properties']), len(other_obj['properties'])),
                    "shared_properties": list(shared_props)
                })
    
    return relationships

