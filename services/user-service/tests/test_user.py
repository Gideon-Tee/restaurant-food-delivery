import pytest
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Role

def test_register_user(client):
    response = client.post('/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'role': 'customer'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['email'] == 'test@example.com'
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'User'
    assert data['role'] == 'customer'

def test_login_user(client):
    # First register a user
    client.post('/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'role': 'customer'
    })
    
    # Then try to login
    response = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['email'] == 'test@example.com'

def test_get_profile(client):
    # First register and login
    client.post('/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'role': 'customer'
    })
    
    login_response = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    access_token = login_response.get_json()['access_token']
    
    # Get profile with token
    response = client.get('/profile', headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    # Print response data for debugging
    print("\nResponse Status:", response.status_code)
    print("Response Data:", response.get_json())
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['email'] == 'test@example.com'
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'User' 