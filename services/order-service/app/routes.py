from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Order, OrderItem, db
from marshmallow import Schema, fields, validate, ValidationError
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Schema definitions for request validation
class OrderItemSchema(Schema):
    menu_item_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    special_instructions = fields.Str(allow_none=True)

class OrderSchema(Schema):
    restaurant_id = fields.Int(required=True)
    delivery_address = fields.Str(required=True)
    special_instructions = fields.Str(allow_none=True)
    items = fields.List(fields.Nested(OrderItemSchema), required=True, validate=validate.Length(min=1))

class OrderUpdateSchema(Schema):
    status = fields.Str(validate=validate.OneOf(['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']))

order_schema = OrderSchema()
order_update_schema = OrderUpdateSchema()
order_item_schema = OrderItemSchema()

order_bp = Blueprint('order', __name__)

def get_user_details(user_id, app):
    """Get user details from User Service"""
    try:
        response = requests.get(
            f"{app.config['USER_SERVICE_URL']}/api/users/{user_id}",
            headers={'Authorization': request.headers.get('Authorization')}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting user details: {str(e)}")
        return None

def get_restaurant_details(restaurant_id, app):
    """Get restaurant details from Restaurant Service"""
    try:
        response = requests.get(
            f"{app.config['RESTAURANT_SERVICE_URL']}/api/restaurants/{restaurant_id}"
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting restaurant details: {str(e)}")
        return None

def get_menu_item_details(menu_item_id, restaurant_id, app):
    """Get menu item details from Restaurant Service"""
    try:
        response = requests.get(
            f"{app.config['RESTAURANT_SERVICE_URL']}/api/restaurants/{restaurant_id}/menu/{menu_item_id}"
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting menu item details: {str(e)}")
        return None

@order_bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    try:
        request_data = request.get_json()
        logger.debug(f"Create order request data: {request_data}")
        
        data = order_schema.load(request_data)
        logger.debug(f"Validated order data: {data}")
        
        user_id = get_jwt_identity()  # Already a string from JWT
        
        # Verify user exists
        user = get_user_details(user_id, current_app)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify restaurant exists
        restaurant = get_restaurant_details(data['restaurant_id'], current_app)
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        # Calculate total amount and verify menu items
        total_amount = 0
        order_items = []
        
        for item_data in data['items']:
            menu_item = get_menu_item_details(item_data['menu_item_id'], data['restaurant_id'], current_app)
            if not menu_item:
                return jsonify({'error': f'Menu item {item_data["menu_item_id"]} not found'}), 404
            
            total_amount += menu_item['price'] * item_data['quantity']
            
            order_item = OrderItem(
                menu_item_id=item_data['menu_item_id'],
                quantity=item_data['quantity'],
                price_at_time=menu_item['price'],
                special_instructions=item_data.get('special_instructions')
            )
            order_items.append(order_item)
        
        # Create order
        order = Order(
            customer_id=user_id,  # Store as string
            restaurant_id=data['restaurant_id'],
            total_amount=total_amount,
            delivery_address=data['delivery_address'],
            special_instructions=data.get('special_instructions'),
            items=order_items
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify(order.to_dict()), 201
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.messages}")
        return jsonify({'error': 'Validation error', 'details': e.messages}), 422
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create order', 'details': str(e)}), 500

@order_bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    try:
        user_id = get_jwt_identity()  # Already a string from JWT
        user = get_user_details(user_id, current_app)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        status = request.args.get('status')
        restaurant_id = request.args.get('restaurant_id')
        
        # Build query
        query = Order.query
        
        if user['role'] == 'customer':
            query = query.filter_by(customer_id=user_id)
        elif user['role'] == 'restaurant_owner':
            if not restaurant_id:
                return jsonify({'error': 'Restaurant ID required for restaurant owners'}), 400
            query = query.filter_by(restaurant_id=restaurant_id)
        
        if status:
            query = query.filter_by(status=status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict() for order in orders])
        
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        return jsonify({'error': 'Failed to get orders'}), 500

@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    try:
        user_id = get_jwt_identity()  # Already a string from JWT
        user = get_user_details(user_id, current_app)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check authorization
        if user['role'] == 'customer' and order.customer_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        elif user['role'] == 'restaurant_owner':
            restaurant = get_restaurant_details(order.restaurant_id, current_app)
            if not restaurant or restaurant['owner_id'] != user_id:
                return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify(order.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        return jsonify({'error': 'Failed to get order'}), 500

@order_bp.route('/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    try:
        request_data = request.get_json()
        data = order_update_schema.load(request_data)
        
        user_id = get_jwt_identity()  # Already a string from JWT
        user = get_user_details(user_id, current_app)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check authorization
        if user['role'] == 'customer' and order.customer_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        elif user['role'] == 'restaurant_owner':
            restaurant = get_restaurant_details(order.restaurant_id, current_app)
            if not restaurant:
                return jsonify({'error': 'Restaurant not found'}), 404
            # Convert owner_id to string for comparison since user_id is a string
            if str(restaurant['owner_id']) != user_id:
                return jsonify({'error': 'Unauthorized'}), 403
        
        # Update order status
        order.status = data['status']
        db.session.commit()
        
        return jsonify(order.to_dict())
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.messages}")
        return jsonify({'error': 'Validation error', 'details': e.messages}), 422
    except Exception as e:
        logger.error(f"Error updating order: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update order'}), 500 