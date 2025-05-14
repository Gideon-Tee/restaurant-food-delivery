from datetime import datetime
from . import db
from geopy.distance import geodesic

class DeliveryAgent(db.Model):
    __tablename__ = 'delivery_agents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    current_latitude = db.Column(db.Float)
    current_longitude = db.Column(db.Float)
    is_available = db.Column(db.Boolean, default=True)
    last_location_update = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with delivery tasks
    tasks = db.relationship('DeliveryTask', backref='agent', lazy=True)
    
    def update_location(self, latitude, longitude):
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.last_location_update = datetime.utcnow()
    
    def calculate_distance_to(self, latitude, longitude):
        if not all([self.current_latitude, self.current_longitude, latitude, longitude]):
            return None
        return geodesic(
            (self.current_latitude, self.current_longitude),
            (latitude, longitude)
        ).kilometers
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_type': self.vehicle_type,
            'current_latitude': self.current_latitude,
            'current_longitude': self.current_longitude,
            'is_available': self.is_available,
            'last_location_update': self.last_location_update.isoformat() if self.last_location_update else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class DeliveryTask(db.Model):
    __tablename__ = 'delivery_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('delivery_agents.id'))
    pickup_latitude = db.Column(db.Float, nullable=False)
    pickup_longitude = db.Column(db.Float, nullable=False)
    delivery_latitude = db.Column(db.Float, nullable=False)
    delivery_longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, assigned, picked_up, delivered, cancelled
    pickup_time = db.Column(db.DateTime)
    delivery_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'agent_id': self.agent_id,
            'pickup_latitude': self.pickup_latitude,
            'pickup_longitude': self.pickup_longitude,
            'delivery_latitude': self.delivery_latitude,
            'delivery_longitude': self.delivery_longitude,
            'status': self.status,
            'pickup_time': self.pickup_time.isoformat() if self.pickup_time else None,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 