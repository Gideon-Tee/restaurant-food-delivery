import json
from app.models import Restaurant, MenuItem

def test_create_restaurant(client, auth_headers):
    data = {
        'name': 'New Restaurant',
        'description': 'A new restaurant',
        'address': '456 New St',
        'phone_number': '9876543210',
        'email': 'new@restaurant.com',
        'cuisine_type': 'Mexican',
        'opening_hours': '{"monday": "10:00-22:00"}'
    }
    
    response = client.post(
        '/api/restaurants',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json['name'] == 'New Restaurant'
    assert response.json['email'] == 'new@restaurant.com'

def test_get_restaurants(client, sample_restaurant):
    response = client.get('/api/restaurants')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['name'] == 'Test Restaurant'

def test_get_restaurant(client, sample_restaurant):
    response = client.get(f'/api/restaurants/{sample_restaurant.id}')
    assert response.status_code == 200
    assert response.json['name'] == 'Test Restaurant'
    assert response.json['email'] == 'test@restaurant.com'

def test_update_restaurant(client, sample_restaurant, auth_headers):
    data = {
        'name': 'Updated Restaurant',
        'description': 'Updated description'
    }
    
    response = client.put(
        f'/api/restaurants/{sample_restaurant.id}',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['name'] == 'Updated Restaurant'
    assert response.json['description'] == 'Updated description'

def test_create_menu_item(client, sample_restaurant, auth_headers):
    data = {
        'name': 'New Menu Item',
        'description': 'A new menu item',
        'price': 12.99,
        'category': 'Appetizer'
    }
    
    response = client.post(
        f'/api/restaurants/{sample_restaurant.id}/menu',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json['name'] == 'New Menu Item'
    assert response.json['price'] == 12.99

def test_get_menu_items(client, sample_restaurant, sample_menu_item):
    response = client.get(f'/api/restaurants/{sample_restaurant.id}/menu')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['name'] == 'Test Item'

def test_get_menu_items_by_category(client, sample_restaurant, sample_menu_item):
    response = client.get(f'/api/restaurants/{sample_restaurant.id}/menu?category=Main Course')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['category'] == 'Main Course'

def test_unauthorized_restaurant_update(client, sample_restaurant, auth_headers):
    # Create a restaurant with different owner_id
    restaurant = Restaurant(
        name='Other Restaurant',
        description='Another restaurant',
        address='789 Other St',
        phone_number='5555555555',
        email='other@restaurant.com',
        owner_id=2  # Different owner
    )
    db.session.add(restaurant)
    db.session.commit()
    
    data = {'name': 'Unauthorized Update'}
    response = client.put(
        f'/api/restaurants/{restaurant.id}',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 403 