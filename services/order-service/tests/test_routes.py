import json
from app.models import Order, OrderItem
from app import db

def test_create_order(client, auth_headers, mock_user_service, mock_restaurant_service):
    data = {
        'restaurant_id': 1,
        'delivery_address': '456 New St',
        'special_instructions': 'Please deliver to the back door',
        'items': [
            {
                'menu_item_id': 1,
                'quantity': 2,
                'special_instructions': 'Extra spicy'
            },
            {
                'menu_item_id': 2,
                'quantity': 1
            }
        ]
    }
    
    response = client.post(
        '/api/orders',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    if response.status_code != 201:
        print(f"Create order error response: {response.get_data(as_text=True)}")
    assert response.status_code == 201
    assert response.json['restaurant_id'] == 1
    assert response.json['delivery_address'] == '456 New St'
    assert len(response.json['items']) == 2
    assert response.json['total_amount'] == 25.98  # (9.99 * 2) + 6.00

def test_get_orders(client, sample_order, auth_headers, mock_user_service):
    response = client.get(
        '/api/orders',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['id'] == sample_order.id
    assert response.json[0]['total_amount'] == 25.98

def test_get_orders_with_status_filter(client, sample_order, auth_headers, mock_user_service):
    response = client.get(
        '/api/orders?status=pending',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['status'] == 'pending'

def test_get_order(client, sample_order, auth_headers, mock_user_service, mock_restaurant_service):
    response = client.get(
        f'/api/orders/{sample_order.id}',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['id'] == sample_order.id
    assert response.json['total_amount'] == 25.98
    assert len(response.json['items']) == 2

def test_update_order_status(client, sample_order, auth_headers, mock_user_service, mock_restaurant_service):
    data = {
        'status': 'confirmed'
    }
    
    response = client.put(
        f'/api/orders/{sample_order.id}',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['status'] == 'confirmed'

def test_unauthorized_order_update(client, sample_order, auth_headers, mock_user_service, mock_restaurant_service):
    # Create a restaurant with different owner_id
    restaurant = {
        'id': 1,
        'name': 'Test Restaurant',
        'owner_id': 999  # Different owner
    }
    
    # Update the mock to return this restaurant
    def mock_get_restaurant(*args, **kwargs):
        return restaurant
    
    # Mock user service to return restaurant owner role
    def mock_get_user(*args, **kwargs):
        return {
            'id': 1,
            'email': 'test@example.com',
            'role': 'restaurant_owner'
        }
    
    import app.routes
    app.routes.get_restaurant_details = mock_get_restaurant
    app.routes.get_user_details = mock_get_user
    
    data = {
        'status': 'confirmed'
    }
    
    response = client.put(
        f'/api/orders/{sample_order.id}',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 403

def test_invalid_order_status(client, sample_order, auth_headers, mock_user_service, mock_restaurant_service):
    data = {
        'status': 'invalid_status'
    }
    
    response = client.put(
        f'/api/orders/{sample_order.id}',
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 422 