from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Restaurant, MenuItem, db
from marshmallow import Schema, fields, validate, ValidationError
import logging
from sqlalchemy.exc import NoResultFound

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Schema definitions for request validation
class RestaurantSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    address = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    email = fields.Email(required=True)
    cuisine_type = fields.Str(allow_none=True)
    opening_hours = fields.Str(allow_none=True)
    is_active = fields.Bool(allow_none=True)

class RestaurantUpdateSchema(Schema):
    name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    phone_number = fields.Str(allow_none=True)
    email = fields.Email(allow_none=True)
    cuisine_type = fields.Str(allow_none=True)
    opening_hours = fields.Str(allow_none=True)
    is_active = fields.Bool(allow_none=True)

class MenuItemSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    price = fields.Float(required=True, validate=validate.Range(min=0))
    category = fields.Str(allow_none=True)
    is_available = fields.Bool(allow_none=True)

restaurant_schema = RestaurantSchema()
restaurant_update_schema = RestaurantUpdateSchema()
menu_item_schema = MenuItemSchema()

restaurant_bp = Blueprint('restaurant', __name__)

@restaurant_bp.route('', methods=['POST'])
@jwt_required()
def create_restaurant():
    try:
        request_data = request.get_json()
        logger.debug(f"Create restaurant request data: {request_data}")
        
        data = restaurant_schema.load(request_data)
        logger.debug(f"Validated restaurant data: {data}")
        
        user_id = int(get_jwt_identity())  # Convert string to int
        
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
        return jsonify(restaurant.to_dict()), 201
    except ValidationError as e:
        logger.error(f"Validation error: {e.messages}")
        return jsonify({'error': 'Validation error', 'details': e.messages}), 422
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create restaurant', 'details': str(e)}), 500

@restaurant_bp.route('', methods=['GET'])
def get_restaurants():
    # Get query parameters
    cuisine_type = request.args.get('cuisine_type')
    is_active = request.args.get('is_active')
    
    # Build query
    query = Restaurant.query
    
    if cuisine_type:
        query = query.filter_by(cuisine_type=cuisine_type)
    if is_active is not None:
        query = query.filter_by(is_active=is_active.lower() == 'true')
    
    restaurants = query.all()
    return jsonify([restaurant.to_dict() for restaurant in restaurants])

@restaurant_bp.route('/<int:restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    try:
        restaurant = db.session.get(Restaurant, restaurant_id)
        if restaurant is None:
            return jsonify({'error': 'Restaurant not found'}), 404
        return jsonify(restaurant.to_dict())
    except Exception as e:
        logger.error(f"Error getting restaurant: {str(e)}")
        return jsonify({'error': 'Failed to get restaurant'}), 500

@restaurant_bp.route('/<int:restaurant_id>', methods=['PUT'])
@jwt_required()
def update_restaurant(restaurant_id):
    try:
        request_data = request.get_json()
        logger.debug(f"Update restaurant request data: {request_data}")
        
        restaurant = db.session.get(Restaurant, restaurant_id)
        if restaurant is None:
            return jsonify({'error': 'Restaurant not found'}), 404
            
        user_id = int(get_jwt_identity())  # Convert string to int
        
        # Check if user is the owner
        if restaurant.owner_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = restaurant_update_schema.load(request_data)
        logger.debug(f"Validated update data: {data}")
        
        # Update fields
        for field, value in data.items():
            if value is not None:  # Only update if value is provided
                setattr(restaurant, field, value)
        
        db.session.commit()
        return jsonify(restaurant.to_dict())
    except ValidationError as e:
        logger.error(f"Validation error: {e.messages}")
        return jsonify({'error': 'Validation error', 'details': e.messages}), 422
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update restaurant', 'details': str(e)}), 500

@restaurant_bp.route('/<int:restaurant_id>/menu', methods=['POST'])
@jwt_required()
def create_menu_item(restaurant_id):
    try:
        request_data = request.get_json()
        logger.debug(f"Create menu item request data: {request_data}")
        
        restaurant = db.session.get(Restaurant, restaurant_id)
        if restaurant is None:
            return jsonify({'error': 'Restaurant not found'}), 404
            
        user_id = int(get_jwt_identity())  # Convert string to int
        
        # Check if user is the owner
        if restaurant.owner_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = menu_item_schema.load(request_data)
        logger.debug(f"Validated menu item data: {data}")
        
        menu_item = MenuItem(
            restaurant_id=restaurant_id,
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            category=data.get('category'),
            is_available=data.get('is_available', True)
        )
        
        db.session.add(menu_item)
        db.session.commit()
        return jsonify(menu_item.to_dict()), 201
    except ValidationError as e:
        logger.error(f"Validation error: {e.messages}")
        return jsonify({'error': 'Validation error', 'details': e.messages}), 422
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create menu item', 'details': str(e)}), 500

@restaurant_bp.route('/<int:restaurant_id>/menu', methods=['GET'])
def get_menu_items(restaurant_id):
    try:
        restaurant = db.session.get(Restaurant, restaurant_id)
        if restaurant is None:
            return jsonify({'error': 'Restaurant not found'}), 404
            
        category = request.args.get('category')
        
        query = MenuItem.query.filter_by(restaurant_id=restaurant_id)
        if category:
            query = query.filter_by(category=category)
        
        menu_items = query.all()
        return jsonify([item.to_dict() for item in menu_items])
    except Exception as e:
        logger.error(f"Error getting menu items: {str(e)}")
        return jsonify({'error': 'Failed to get menu items'}), 500 