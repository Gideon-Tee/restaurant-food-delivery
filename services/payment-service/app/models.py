from datetime import datetime
from . import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)  # References order_id from Order Service
    customer_id = db.Column(db.String(50), nullable=False)  # References user_id from User Service
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='GHS')
    payment_method = db.Column(db.String(20), nullable=False)  # card, mobile_money, cash
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100), unique=True)  # External payment provider's transaction ID
    payment_details = db.Column(db.JSON)  # Store additional payment details like card last 4 digits, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'payment_details': self.payment_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 