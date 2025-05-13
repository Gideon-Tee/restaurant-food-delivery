from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Payment, db
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy.exc import NoResultFound
import requests
import logging
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Schema definitions for request validation
class PaymentSchema(Schema):
    order_id = fields.Int(required=True)
    payment_method = fields.Str(required=True, validate=validate.OneOf(['card', 'mobile_money', 'cash']))
    payment_details = fields.Dict(allow_none=True)

payment_schema = PaymentSchema()

payment_bp = Blueprint('payment', __name__)

def get_order_details(order_id, app):
    """Get order details from Order Service"""
    try:
        response = requests.get(
            f"{app.config['ORDER_SERVICE_URL']}/api/orders/{order_id}",
            headers={'Authorization': request.headers.get('Authorization')}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting order details: {str(e)}")
        return None

@payment_bp.route('/', methods=['GET'])
@jwt_required()
def get_payments():
    try:
        user_id = str(get_jwt_identity())
        payments = Payment.query.filter_by(customer_id=user_id).all()
        response = make_response(jsonify([payment.to_dict() for payment in payments]))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error("Error getting payments: %s", str(e))
        return jsonify({'error': 'Failed to get payments'}), 500

@payment_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_payment(id):
    try:
        user_id = str(get_jwt_identity())
        payment = Payment.query.filter_by(id=id, customer_id=user_id).first()
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        response = make_response(jsonify(payment.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error("Error getting payment: %s", str(e))
        return jsonify({'error': 'Failed to get payment'}), 500

@payment_bp.route('/', methods=['POST'])
@jwt_required()
def create_payment():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': ['order_id', 'payment_method']
            }), 400
        
        # Validate required fields
        required_fields = ['order_id', 'payment_method']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Get order details
        order = get_order_details(data['order_id'], current_app)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get user ID from JWT
        user_id = str(get_jwt_identity())
        
        # Verify user owns the order
        if order['customer_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create payment record
        payment = Payment(
            order_id=data['order_id'],
            customer_id=user_id,
            amount=order['total_amount'],
            payment_method=data['payment_method'],
            payment_details=data.get('payment_details'),
            transaction_id=str(uuid.uuid4())  # Generate a unique transaction ID
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # TODO: Integrate with actual payment provider
        # For now, we'll simulate a successful payment
        payment.status = 'completed'
        db.session.commit()
        
        response = make_response(jsonify(payment.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 201
        
    except Exception as e:
        logger.error("Error creating payment: %s", str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to create payment'}), 500

@payment_bp.route('/<int:id>/refund', methods=['POST'])
@jwt_required()
def refund_payment(id):
    try:
        payment = Payment.query.filter_by(id=id).first()
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
            
        user_id = str(get_jwt_identity())
        
        # Verify user owns the payment
        if payment.customer_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if payment can be refunded
        if payment.status != 'completed':
            return jsonify({'error': 'Payment cannot be refunded'}), 400
        
        # TODO: Integrate with actual payment provider for refund
        # For now, we'll just update the status
        payment.status = 'refunded'
        db.session.commit()
        
        response = make_response(jsonify(payment.to_dict()))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error("Error refunding payment: %s", str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to refund payment'}), 500 