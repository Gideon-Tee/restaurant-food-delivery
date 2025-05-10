from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Restaurant, MenuItem, db

restaurant_bp = Blueprint('restaurant', __name__)

@restaurant_bp.route('', methods=['POST'])
@jwt_required()
def create_restaurant():
    data = request.get_json()
    user_id = int(get_jwt_identity())
    
    # Validate required fields
    required_fields = ['name', 'address', 'phone_number', 'email']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'missing_fields': missing_fields
        }), 400
    
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
        opening_hours=data.get('opening_hours')
    )
    
    try:
        db.session.add(restaurant)
        db.session.commit()
        return jsonify(restaurant.to_dict()), 201
    except Exception as e:
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
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    return jsonify(restaurant.to_dict())

@restaurant_bp.route('/<int:restaurant_id>', methods=['PUT'])
@jwt_required()
def update_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    user_id = int(get_jwt_identity())
    
    # Check if user is the owner
    if restaurant.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update fields
    for field in ['name', 'description', 'address', 'phone_number', 
                 'email', 'cuisine_type', 'opening_hours', 'is_active']:
        if field in data:
            setattr(restaurant, field, data[field])
    
    try:
        db.session.commit()
        return jsonify(restaurant.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update restaurant', 'details': str(e)}), 500

# Menu Item Routes
@restaurant_bp.route('/<int:restaurant_id>/menu', methods=['POST'])
@jwt_required()
def create_menu_item(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    user_id = int(get_jwt_identity())
    
    # Check if user is the owner
    if restaurant.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'price']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'missing_fields': missing_fields
        }), 400
    
    menu_item = MenuItem(
        restaurant_id=restaurant_id,
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        category=data.get('category')
    )
    
    try:
        db.session.add(menu_item)
        db.session.commit()
        return jsonify(menu_item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create menu item', 'details': str(e)}), 500

@restaurant_bp.route('/<int:restaurant_id>/menu', methods=['GET'])
def get_menu_items(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    category = request.args.get('category')
    
    query = MenuItem.query.filter_by(restaurant_id=restaurant_id)
    if category:
        query = query.filter_by(category=category)
    
    menu_items = query.all()
    return jsonify([item.to_dict() for item in menu_items]) 