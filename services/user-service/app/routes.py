from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import User, Role, db
from datetime import timedelta
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        # Get and parse request data
        raw_data = request.get_data(as_text=True)
        logger.debug("Raw request data: %s", raw_data)
        
        # Clean the request data by removing leading/trailing whitespace and newlines
        cleaned_data = raw_data.strip()
        logger.debug("Cleaned request data: %s", cleaned_data)
        
        try:
            data = json.loads(cleaned_data)
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
            return jsonify({'error': 'Invalid JSON data', 'details': str(e)}), 400
            
        if not data:
            logger.error("No JSON data in request")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        logger.debug("Parsed request data: %s", data)
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Get role
        role = Role.query.filter_by(name=data['role']).first()
        if not role:
            return jsonify({
                'error': 'Invalid role',
                'valid_roles': ['customer', 'restaurant_owner', 'delivery_person']
            }), 400
        
        # Create new user
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data.get('phone_number'),
            role_id=role.id
        )
        user.set_password(data['password'])
        
        try:
            db.session.add(user)
            db.session.commit()
            response = make_response(jsonify(user.to_dict()))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response, 201
        except Exception as e:
            db.session.rollback()
            logger.error("Database error: %s", str(e), exc_info=True)
            return jsonify({'error': 'Failed to create user', 'details': str(e)}), 500
            
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return jsonify({'error': 'Failed to process request', 'details': str(e)}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        # Get and parse request data
        raw_data = request.get_data(as_text=True)
        logger.debug("Raw request data: %s", raw_data)
        
        # Clean the request data by removing leading/trailing whitespace and newlines
        cleaned_data = raw_data.strip()
        logger.debug("Cleaned request data: %s", cleaned_data)
        
        try:
            data = json.loads(cleaned_data)
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
            return jsonify({'error': 'Invalid JSON data', 'details': str(e)}), 400
            
        if not data:
            logger.error("No JSON data in request")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        logger.debug("Parsed request data: %s", data)
        
        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create a single access token with all claims
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'role': user.role.name,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            expires_delta=timedelta(days=1)
        )
        
        logger.debug("Generated access token: %s", access_token)
        
        # Create response with proper headers
        response = make_response(jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return jsonify({'error': 'Failed to process request', 'details': str(e)}), 500

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        response = make_response(jsonify(user.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        # Get and parse request data
        raw_data = request.get_data(as_text=True)
        logger.debug("Raw request data: %s", raw_data)
        
        # Clean the request data by removing leading/trailing whitespace and newlines
        cleaned_data = raw_data.strip()
        logger.debug("Cleaned request data: %s", cleaned_data)
        
        try:
            data = json.loads(cleaned_data)
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
            return jsonify({'error': 'Invalid JSON data', 'details': str(e)}), 400
            
        if not data:
            logger.error("No JSON data in request")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        logger.debug("Parsed request data: %s", data)
        
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        
        response = make_response(jsonify(user.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500 