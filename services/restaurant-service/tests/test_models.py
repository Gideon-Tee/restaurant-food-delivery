from app.models import Restaurant, MenuItem
from datetime import datetime
from app import db

def test_restaurant_creation(app):
    with app.app_context():
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
        
        assert restaurant.name == 'Test Restaurant'
        assert restaurant.email == 'test@restaurant.com'
        assert restaurant.owner_id == 1
        assert restaurant.is_active == True
        assert isinstance(restaurant.created_at, datetime)
        assert isinstance(restaurant.updated_at, datetime)

def test_restaurant_to_dict(app):
    with app.app_context():
        restaurant = Restaurant(
            name='Test Restaurant',
            description='A test restaurant',
            address='123 Test St',
            phone_number='1234567890',
            email='test@restaurant.com',
            owner_id=1
        )
        db.session.add(restaurant)
        db.session.commit()
        
        restaurant_dict = restaurant.to_dict()
        assert restaurant_dict['name'] == 'Test Restaurant'
        assert restaurant_dict['email'] == 'test@restaurant.com'
        assert restaurant_dict['owner_id'] == 1
        assert 'created_at' in restaurant_dict
        assert 'updated_at' in restaurant_dict

def test_menu_item_creation(app, sample_restaurant):
    with app.app_context():
        menu_item = MenuItem(
            restaurant_id=sample_restaurant.id,
            name='Test Item',
            description='A test menu item',
            price=9.99,
            category='Main Course'
        )
        db.session.add(menu_item)
        db.session.commit()
        
        assert menu_item.name == 'Test Item'
        assert menu_item.price == 9.99
        assert menu_item.restaurant_id == sample_restaurant.id
        assert menu_item.is_available == True
        assert isinstance(menu_item.created_at, datetime)
        assert isinstance(menu_item.updated_at, datetime)

def test_menu_item_to_dict(app, sample_restaurant):
    with app.app_context():
        menu_item = MenuItem(
            restaurant_id=sample_restaurant.id,
            name='Test Item',
            description='A test menu item',
            price=9.99,
            category='Main Course'
        )
        db.session.add(menu_item)
        db.session.commit()
        
        menu_item_dict = menu_item.to_dict()
        assert menu_item_dict['name'] == 'Test Item'
        assert menu_item_dict['price'] == 9.99
        assert menu_item_dict['restaurant_id'] == sample_restaurant.id
        assert 'created_at' in menu_item_dict
        assert 'updated_at' in menu_item_dict 