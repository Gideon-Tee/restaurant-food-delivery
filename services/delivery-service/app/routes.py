from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from .models import DeliveryAgent, DeliveryTask, db
from datetime import datetime
import requests
import logging
import boto3
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

delivery_bp = Blueprint('delivery', __name__)

def get_order_details(order_id):
    """Get order details from Order Service"""
    try:
        response = requests.get(
            f"{current_app.config['ORDER_SERVICE_URL']}/api/orders/{order_id}",
            headers={'Authorization': request.headers.get('Authorization')}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting order details: {str(e)}")
        return None

def notify_status_update(delivery_task):
    """Notify order service about delivery status updates"""
    try:
        sns = boto3.client('sns', region_name=current_app.config['AWS_REGION'])
        message = {
            'order_id': delivery_task.order_id,
            'delivery_status': delivery_task.status,
            'timestamp': datetime.utcnow().isoformat()
        }
        sns.publish(
            TopicArn=current_app.config['SNS_TOPIC_ARN'],
            Message=json.dumps(message)
        )
    except Exception as e:
        logger.error(f"Error publishing to SNS: {str(e)}")

@delivery_bp.route('/agents', methods=['POST'])
@jwt_required()
def register_agent():
    try:
        claims = get_jwt()
        if claims.get('role') != 'delivery_person':
            return jsonify({'error': 'Unauthorized'}), 403
            
        data = request.get_json()
        if not data or 'vehicle_type' not in data:
            return jsonify({'error': 'Vehicle type is required'}), 400
            
        # Create new delivery agent
        agent = DeliveryAgent(
            user_id=str(get_jwt_identity()),
            vehicle_type=data['vehicle_type']
        )
        
        db.session.add(agent)
        db.session.commit()
        
        logger.info(f"New delivery agent registered: {agent.id}")
        return jsonify(agent.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error registering delivery agent: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to register delivery agent'}), 500

@delivery_bp.route('/agents/location', methods=['PUT'])
@jwt_required()
def update_location():
    try:
        data = request.get_json()
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
            
        agent = DeliveryAgent.query.filter_by(user_id=str(get_jwt_identity())).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        agent.update_location(data['latitude'], data['longitude'])
        db.session.commit()
        
        return jsonify(agent.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating agent location: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update location'}), 500

@delivery_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_delivery_task():
    try:
        data = request.get_json()
        if not data or 'order_id' not in data:
            return jsonify({'error': 'Order ID is required'}), 400
            
        # Verify order exists and get details
        order = get_order_details(data['order_id'])
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Check for required coordinate fields from order details
        # All these are nullable=False in DeliveryTask model
        required_coordinate_fields = [
            'restaurant_latitude', 
            'restaurant_longitude', 
            'delivery_latitude', 
            'delivery_longitude'
        ]
        missing_or_null_fields = []
        for field in required_coordinate_fields:
            if order.get(field) is None: # Check if key exists and value is not None
                missing_or_null_fields.append(field)
        
        if missing_or_null_fields:
            error_message = f"Missing or null required coordinate fields from order details for order_id {data['order_id']}: {missing_or_null_fields}"
            logger.error(error_message)
            return jsonify({
                'error': 'Missing or null required coordinate fields in order details provided by order-service.',
                'missing_fields': missing_or_null_fields
            }), 400
            
        # Create delivery task
        task = DeliveryTask(
            order_id=data['order_id'],
            pickup_latitude=order['restaurant_latitude'],
            pickup_longitude=order['restaurant_longitude'],
            delivery_latitude=order['delivery_latitude'],
            delivery_longitude=order['delivery_longitude'],
            status='pending'  # Set initial status
        )
        
        # Find nearest available agent before saving the task
        available_agents = DeliveryAgent.query.filter_by(is_available=True).all()
        nearest_agent = None
        min_distance = float('inf')
        
        for agent in available_agents:
            distance = agent.calculate_distance_to(task.pickup_latitude, task.pickup_longitude)
            if distance is not None and distance < min_distance:  # Changed condition to handle zero distance
                min_distance = distance
                nearest_agent = agent
        
        if nearest_agent:
            task.agent_id = nearest_agent.id
            task.status = 'assigned'  # Update status when agent is assigned
            nearest_agent.is_available = False
        
        db.session.add(task)
        db.session.commit()
        
        # Notify about the assignment if an agent was found
        if nearest_agent:
            notify_status_update(task)
        
        logger.info(f"New delivery task created: {task.id}")
        return jsonify(task.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating delivery task: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create delivery task'}), 500

@delivery_bp.route('/tasks/<int:task_id>/status', methods=['PUT'])
@jwt_required()
def update_task_status(task_id):
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
            
        task = db.session.get(DeliveryTask, task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
            
        agent = DeliveryAgent.query.filter_by(user_id=str(get_jwt_identity())).first()
        
        if not agent or task.agent_id != agent.id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        valid_statuses = {'picked_up', 'delivered', 'cancelled'}
        if data['status'] not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
            
        task.status = data['status']
        if data['status'] == 'picked_up':
            task.pickup_time = datetime.utcnow()
        elif data['status'] == 'delivered':
            task.delivery_time = datetime.utcnow()
            agent.is_available = True
            
        db.session.commit()
        notify_status_update(task)
        
        return jsonify(task.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update task status'}), 500

@delivery_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    try:
        task = db.session.get(DeliveryTask, task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(task.to_dict())
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}")
        return jsonify({'error': 'Failed to get task'}), 500 