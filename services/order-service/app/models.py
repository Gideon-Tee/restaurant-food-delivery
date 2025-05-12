from datetime import datetime
from . import db

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), nullable=False)  # References user_id from User Service as string
    restaurant_id = db.Column(db.Integer, nullable=False)  # References restaurant_id from Restaurant Service
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, preparing, ready, delivered, cancelled
    total_amount = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.String(200), nullable=False)
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship with OrderItems
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'restaurant_id': self.restaurant_id,
            'status': self.status,
            'total_amount': self.total_amount,
            'delivery_address': self.delivery_address,
            'special_instructions': self.special_instructions,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, nullable=False)  # References menu_item_id from Restaurant Service
    quantity = db.Column(db.Integer, nullable=False)
    price_at_time = db.Column(db.Float, nullable=False)  # Price of item when order was placed
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'menu_item_id': self.menu_item_id,
            'quantity': self.quantity,
            'price_at_time': self.price_at_time,
            'special_instructions': self.special_instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 