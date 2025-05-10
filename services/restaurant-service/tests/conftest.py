import os
import sys
import pytest
from flask_jwt_extended import create_access_token

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Restaurant, MenuItem

@pytest.fixture
def app():
    app = create_app('test')  # Pass 'test' to indicate test mode
    
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
    # Create a token with a string subject (user_id)
    access_token = create_access_token(identity=str(1))  # Convert user_id to string
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def sample_restaurant(app):
    restaurant = Restaurant(
        name='Test Restaurant',
        description='A test restaurant',
        address='123 Test St',
        phone_number='1234567890',
        email='test@restaurant.com',
        owner_id=1,
        cuisine_type='Italian',
        opening_hours='{"monday": "09:00-22:00"}',
        is_active=True
    )
    db.session.add(restaurant)
    db.session.commit()
    return restaurant

@pytest.fixture
def sample_menu_item(app, sample_restaurant):
    menu_item = MenuItem(
        restaurant_id=sample_restaurant.id,
        name='Test Item',
        description='A test menu item',
        price=9.99,
        category='Main Course',
        is_available=True
    )
    db.session.add(menu_item)
    db.session.commit()
    return menu_item 