from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Order, OrderItem, db
from marshmallow import Schema, fields, validate, ValidationError
import requests
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Schema definitions for request validation
class OrderItemSchema(Schema):
    menu_item_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    special_instructions = fields.Str(allow_none=True)

class OrderSchema(Schema):
    restaurant_id = fields.Int(required=True)
    items = fields.List(fields.Nested(OrderItemSchema), required=True)
    delivery_address = fields.Str(required=True)
    delivery_latitude = fields.Float(allow_none=True)
    delivery_longitude = fields.Float(allow_none=True)
    special_instructions = fields.Str(allow_none=True)

class OrderUpdateSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(['pending', 'confirmed', 'preparing', 'ready_for_delivery', 'out_for_delivery', 'delivered', 'cancelled']))

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

@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    try:
        user_id = str(get_jwt_identity())  # Convert to string since customer_id is String(50)
        orders = Order.query.filter_by(customer_id=user_id).all()
        response = make_response(jsonify([order.to_dict() for order in orders]))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error("Error getting orders: %s", str(e))
        return jsonify({'error': 'Failed to get orders'}), 500

@order_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    try:
        user_id = str(get_jwt_identity())  # Convert to string since customer_id is String(50)
        order = Order.query.filter_by(id=id, customer_id=user_id).first_or_404()
        response = make_response(jsonify(order.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error("Error getting order: %s", str(e))
        return jsonify({'error': 'Failed to get order'}), 500

@order_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['restaurant_id', 'delivery_address', 'items']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
            
        # Validate items
        if not isinstance(data['items'], list) or not data['items']:
            return jsonify({
                'error': 'Invalid items',
                'details': 'Items must be a non-empty list'
            }), 400
            
        for item in data['items']:
            if not isinstance(item, dict) or 'menu_item_id' not in item or 'quantity' not in item:
                return jsonify({
                    'error': 'Invalid item format',
                    'details': 'Each item must have menu_item_id and quantity'
                }), 400
        
        # Get user ID from JWT
        user_id = str(get_jwt_identity())  # Convert to string since customer_id is String(50)
        
        # Create new order
        order = Order(
            customer_id=user_id,
            restaurant_id=data['restaurant_id'],
            delivery_address=data['delivery_address'],
            delivery_latitude=data.get('delivery_latitude'),
            delivery_longitude=data.get('delivery_longitude'),
            special_instructions=data.get('special_instructions'),
            status='pending',
            total_amount=0.0  # This will be calculated later
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID without committing
        
        # Create order items
        for item_data in data['items']:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_data['menu_item_id'],
                quantity=item_data['quantity'],
                price_at_time=0.0,  # This will be fetched from restaurant service
                special_instructions=item_data.get('special_instructions')
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        response = make_response(jsonify(order.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 201
        
    except Exception as e:
        logger.error("Error creating order: %s", str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to create order'}), 500

@order_bp.route('/<int:id>', methods=['PATCH'])
@jwt_required()
def update_order_status(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
            
        # Validate status
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready_for_delivery', 'out_for_delivery', 'delivered', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({
                'error': 'Invalid status',
                'valid_statuses': valid_statuses
            }), 400
        
        # Get order
        order = Order.query.get_or_404(id)
        
        # Update status
        order.status = data['status']
        db.session.commit()
        
        response = make_response(jsonify(order.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error("Error updating order status: %s", str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to update order status'}), 500 