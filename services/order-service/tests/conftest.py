import os
import sys
import pytest
from flask_jwt_extended import create_access_token
import json

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db, jwt
from app.models import Order, OrderItem

@pytest.fixture
def app():
    app = create_app('test')
    
    # Configure JWT for testing
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return identity
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers():
    """Create a JWT token for testing"""
    access_token = create_access_token(identity="1")  # Convert to string
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def sample_order(app):
    """Create a sample order for testing"""
    order = Order(
        customer_id="1",  # Changed to string to match JWT identity
        restaurant_id=1,
        status='pending',
        total_amount=25.98,
        delivery_address='123 Test St',
        special_instructions='Test instructions'
    )
    
    # Add order items
    order_item1 = OrderItem(
        menu_item_id=1,
        quantity=2,
        price_at_time=9.99,
        special_instructions='Extra spicy'
    )
    order_item2 = OrderItem(
        menu_item_id=2,
        quantity=1,
        price_at_time=6.00
    )
    
    order.items.append(order_item1)
    order.items.append(order_item2)
    
    db.session.add(order)
    db.session.commit()
    
    return order

@pytest.fixture
def mock_user_service(app, monkeypatch):
    """Mock the user service responses"""
    def mock_get_user(*args, **kwargs):
        return {
            'id': 1,
            'email': 'test@example.com',
            'role': 'customer'
        }
    
    monkeypatch.setattr('app.routes.get_user_details', mock_get_user)

@pytest.fixture
def mock_restaurant_service(app, monkeypatch):
    """Mock the restaurant service responses"""
    def mock_get_restaurant(*args, **kwargs):
        return {
            'id': 1,
            'name': 'Test Restaurant',
            'address': '123 Restaurant St',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'owner_id': 1
        }
    
    def mock_get_menu_item(*args, **kwargs):
        # Return different prices based on menu_item_id
        menu_items = {
            1: {'id': 1, 'name': 'Test Item 1', 'price': 9.99},
            2: {'id': 2, 'name': 'Test Item 2', 'price': 6.00}
        }
        return menu_items.get(args[0], {'id': args[0], 'name': 'Unknown Item', 'price': 0.00})
    
    monkeypatch.setattr('app.models.requests.get', mock_get_restaurant)
    monkeypatch.setattr('app.routes.get_restaurant_details', mock_get_restaurant)
    monkeypatch.setattr('app.routes.get_menu_item_details', mock_get_menu_item) 