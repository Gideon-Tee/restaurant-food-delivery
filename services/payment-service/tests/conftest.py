import pytest
from app import create_app, db
from app.models import Payment
import json
from unittest.mock import patch
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    with app.app_context():
        access_token = create_access_token(identity='test-user')
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

@pytest.fixture
def sample_payment_data():
    return {
        'order_id': 1,
        'payment_method': 'card',
        'payment_details': {
            'card_last4': '4242',
            'card_brand': 'visa'
        }
    }

@pytest.fixture
def mock_order_response():
    return {
        'id': 1,
        'customer_id': 'test-user',
        'total_amount': 100.0,
        'status': 'pending'
    } 