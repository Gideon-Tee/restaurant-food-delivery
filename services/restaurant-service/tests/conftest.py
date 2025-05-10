import pytest
from app import create_app, db
from app.models import Restaurant, MenuItem

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
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
def auth_headers():
    # This is a mock JWT token for testing
    return {'Authorization': 'Bearer test-token'}

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
        opening_hours='{"monday": "9:00-17:00"}'
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
        category='Main Course'
    )
    db.session.add(menu_item)
    db.session.commit()
    return menu_item 