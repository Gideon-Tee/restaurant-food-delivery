from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Restaurant, MenuItem, db
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

restaurant_bp = Blueprint('restaurant', __name__)

@restaurant_bp.route('/', methods=['GET'])
def get_restaurants():
    try:
        restaurants = Restaurant.query.all()
        response = make_response(jsonify([r.to_dict() for r in restaurants]))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error("Error getting restaurants: %s", str(e))
        return jsonify({'error': 'Failed to get restaurants'}), 500

@restaurant_bp.route('/<int:id>', methods=['GET'])
def get_restaurant(id):
    try:
        restaurant = Restaurant.query.get_or_404(id)
        response = make_response(jsonify(restaurant.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error("Error getting restaurant: %s", str(e))
        return jsonify({'error': 'Failed to get restaurant'}), 500

@restaurant_bp.route('/<int:id>/menu', methods=['GET'])
def get_menu(id):
    try:
        restaurant = Restaurant.query.get_or_404(id)
        menu_items = MenuItem.query.filter_by(restaurant_id=id).all()
        response = make_response(jsonify([item.to_dict() for item in menu_items]))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error("Error getting menu: %s", str(e))
        return jsonify({'error': 'Failed to get menu'}), 500

@restaurant_bp.route('/<int:id>/menu', methods=['POST'])
@jwt_required()
def add_menu_item(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'price', 'category']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Verify restaurant exists
        restaurant = Restaurant.query.get_or_404(id)
        
        # Create new menu item
        menu_item = MenuItem(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            category=data['category'],
            is_available=data.get('is_available', True),
            restaurant_id=id
        )
        
        db.session.add(menu_item)
        db.session.commit()
        
        response = make_response(jsonify(menu_item.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 201
        
    except Exception as e:
        logger.error("Error adding menu item: %s", str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to add menu item'}), 500

@restaurant_bp.route('', methods=['POST'])
@jwt_required()
def create_restaurant():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'address', 'phone_number', 'email']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        user_id = int(get_jwt_identity())
        
        # Check if restaurant with email already exists
        if Restaurant.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        restaurant = Restaurant(
            name=data['name'],
            description=data.get('description'),
            address=data['address'],
            phone_number=data['phone_number'],
            email=data['email'],
            owner_id=user_id,
            cuisine_type=data.get('cuisine_type'),
            opening_hours=data.get('opening_hours'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(restaurant)
        db.session.commit()
        
        response = make_response(jsonify(restaurant.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 201
        
    except Exception as e:
        logger.error("Error creating restaurant: %s", str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to create restaurant'}), 500

@restaurant_bp.route('/<int:restaurant_id>', methods=['PUT'])
@jwt_required()
def update_restaurant(restaurant_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        user_id = int(get_jwt_identity())
        
        # Check if user is the owner
        if restaurant.owner_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update fields
        for field, value in data.items():
            if value is not None:  # Only update if value is provided
                setattr(restaurant, field, value)
        
        db.session.commit()
        
        response = make_response(jsonify(restaurant.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error("Error updating restaurant: %s", str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to update restaurant'}), 500 