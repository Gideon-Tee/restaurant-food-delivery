import pytest
import json
from unittest.mock import patch
from app.models import Payment
from app import db

def test_get_payments_empty(client, auth_headers):
    """Test getting payments when none exist"""
    response = client.get('/api/payments/', headers=auth_headers)
    assert response.status_code == 200
    assert json.loads(response.data) == []

def test_get_payments_with_data(client, auth_headers):
    """Test getting payments when some exist"""
    # Create a test payment
    payment = Payment(
        order_id=1,
        customer_id='test-user',
        amount=100.0,
        payment_method='card',
        status='completed'
    )
    
    with client.application.app_context():
        db.session.add(payment)
        db.session.commit()
    
    response = client.get('/api/payments/', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['order_id'] == 1
    assert data[0]['amount'] == 100.0

def test_get_payment_not_found(client, auth_headers):
    """Test getting a non-existent payment"""
    response = client.get('/api/payments/999', headers=auth_headers)
    assert response.status_code == 404

def test_get_payment_success(client, auth_headers):
    """Test getting an existing payment"""
    # Create a test payment
    payment = Payment(
        order_id=1,
        customer_id='test-user',
        amount=100.0,
        payment_method='card',
        status='completed'
    )
    
    with client.application.app_context():
        db.session.add(payment)
        db.session.commit()
        payment_id = payment.id
    
    response = client.get(f'/api/payments/{payment_id}', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['order_id'] == 1
    assert data['amount'] == 100.0

@patch('app.routes.get_order_details')
def test_create_payment_success(mock_get_order, client, auth_headers, sample_payment_data, mock_order_response):
    """Test creating a payment successfully"""
    mock_get_order.return_value = mock_order_response
    
    response = client.post(
        '/api/payments/',
        headers=auth_headers,
        data=json.dumps(sample_payment_data)
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['order_id'] == sample_payment_data['order_id']
    assert data['payment_method'] == sample_payment_data['payment_method']
    assert data['status'] == 'completed'

@patch('app.routes.get_order_details')
def test_create_payment_order_not_found(mock_get_order, client, auth_headers, sample_payment_data):
    """Test creating a payment for non-existent order"""
    mock_get_order.return_value = None
    
    response = client.post(
        '/api/payments/',
        headers=auth_headers,
        data=json.dumps(sample_payment_data)
    )
    
    assert response.status_code == 404
    assert b'Order not found' in response.data

def test_create_payment_missing_fields(client, auth_headers):
    """Test creating a payment with missing required fields"""
    response = client.post(
        '/api/payments/',
        headers=auth_headers,
        data=json.dumps({})
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'missing_fields' in data

def test_refund_payment_success(client, auth_headers):
    """Test refunding a payment successfully"""
    # Create a completed payment
    payment = Payment(
        order_id=1,
        customer_id='test-user',
        amount=100.0,
        payment_method='card',
        status='completed'
    )
    
    with client.application.app_context():
        db.session.add(payment)
        db.session.commit()
        payment_id = payment.id
    
    response = client.post(
        f'/api/payments/{payment_id}/refund',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'refunded'

def test_refund_payment_not_found(client, auth_headers):
    """Test refunding a non-existent payment"""
    response = client.post(
        '/api/payments/999/refund',
        headers=auth_headers
    )
    
    assert response.status_code == 404

def test_refund_payment_wrong_status(client, auth_headers):
    """Test refunding a payment that's not completed"""
    # Create a pending payment
    payment = Payment(
        order_id=1,
        customer_id='test-user',
        amount=100.0,
        payment_method='card',
        status='pending'
    )
    
    with client.application.app_context():
        db.session.add(payment)
        db.session.commit()
        payment_id = payment.id
    
    response = client.post(
        f'/api/payments/{payment_id}/refund',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert b'Payment cannot be refunded' in response.data