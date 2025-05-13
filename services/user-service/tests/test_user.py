import pytest
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from app.models import User

@pytest.fixture(autouse=True)
def cleanup_database():
    # This runs before each test
    yield
    # This runs after each test
    User.query.delete()
    db.session.commit()

def test_register_user(client):
    response = client.post('/api/users/register', json={
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
    client.post('/api/users/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'role': 'customer'
    })
    
    # Then try to login
    response = client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['email'] == 'test@example.com'

def test_get_profile(client):
    # First register and login
    client.post('/api/users/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'role': 'customer'
    })
    
    login_response = client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    access_token = login_response.get_json()['access_token']
    
    # Get profile with token
    response = client.get('/api/users/profile', headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['email'] == 'test@example.com'
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'User' 