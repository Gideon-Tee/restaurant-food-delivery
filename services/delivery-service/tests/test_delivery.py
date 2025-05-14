import pytest
from app.models import DeliveryAgent, DeliveryTask
from datetime import datetime

def test_register_agent(client, auth_headers):
    """Test registering a new delivery agent."""
    response = client.post('/api/delivery/agents', 
        json={'vehicle_type': 'motorcycle'},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['vehicle_type'] == 'motorcycle'
    assert data['user_id'] == '1'
    assert data['is_available'] == True

def test_register_agent_missing_vehicle_type(client, auth_headers):
    """Test registering an agent without vehicle type."""
    response = client.post('/api/delivery/agents', 
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Vehicle type is required'

def test_update_agent_location(client, auth_headers, sample_agent):
    """Test updating agent location."""
    response = client.put('/api/delivery/agents/location',
        json={
            'latitude': 40.7589,
            'longitude': -73.9851
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['current_latitude'] == 40.7589
    assert data['current_longitude'] == -73.9851
    assert datetime.fromisoformat(data['last_location_update'])

def test_update_agent_location_missing_coordinates(client, auth_headers, sample_agent):
    """Test updating agent location with missing coordinates."""
    response = client.put('/api/delivery/agents/location',
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Latitude and longitude are required'

def test_create_delivery_task(client, auth_headers, mock_order_response, mock_sns_publish, sample_agent, session):
    """Test creating a new delivery task."""
    # Ensure agent is available and has location set
    sample_agent.is_available = True
    sample_agent.current_latitude = 40.7128  # Same as restaurant location
    sample_agent.current_longitude = -74.0060
    session.add(sample_agent)  # Ensure the agent is in the session
    session.commit()
    session.refresh(sample_agent)  # Refresh the agent to ensure changes are visible

    response = client.post('/api/delivery/tasks',
        json={'order_id': 1},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['order_id'] == 1
    assert data['status'] == 'assigned'
    assert data['agent_id'] == sample_agent.id
    assert data['pickup_latitude'] == 40.7128
    assert data['pickup_longitude'] == -74.0060

def test_create_delivery_task_missing_order_id(client, auth_headers):
    """Test creating a delivery task without order ID."""
    response = client.post('/api/delivery/tasks',
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Order ID is required'

def test_update_task_status(client, auth_headers, mock_sns_publish, sample_task):
    """Test updating task status."""
    response = client.put(f'/api/delivery/tasks/{sample_task.id}/status',
        json={'status': 'picked_up'},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'picked_up'
    assert datetime.fromisoformat(data['pickup_time'])

def test_update_task_status_invalid_status(client, auth_headers, sample_task):
    """Test updating task status with invalid status."""
    response = client.put(f'/api/delivery/tasks/{sample_task.id}/status',
        json={'status': 'invalid_status'},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid status'

def test_update_task_status_unauthorized(client, auth_headers, sample_task):
    """Test updating task status for unauthorized agent."""
    # Modify the task's agent_id to simulate unauthorized access
    sample_task.agent_id = 999
    
    response = client.put(f'/api/delivery/tasks/{sample_task.id}/status',
        json={'status': 'picked_up'},
        headers=auth_headers
    )
    
    assert response.status_code == 403
    assert response.get_json()['error'] == 'Unauthorized'

def test_get_task(client, auth_headers, sample_task):
    """Test getting task details."""
    response = client.get(f'/api/delivery/tasks/{sample_task.id}',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == sample_task.id
    assert data['order_id'] == sample_task.order_id
    assert data['status'] == 'assigned'

def test_get_nonexistent_task(client, auth_headers):
    """Test getting a nonexistent task."""
    response = client.get('/api/delivery/tasks/999',
        headers=auth_headers
    )
    
    assert response.status_code == 404

def test_complete_delivery_workflow(client, auth_headers, mock_sns_publish, sample_task, sample_agent):
    """Test the complete delivery workflow."""
    # 1. Update location near pickup
    response = client.put('/api/delivery/agents/location',
        json={
            'latitude': 40.7128,
            'longitude': -74.0060
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # 2. Mark as picked up
    response = client.put(f'/api/delivery/tasks/{sample_task.id}/status',
        json={'status': 'picked_up'},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json()['status'] == 'picked_up'
    
    # 3. Update location near delivery
    response = client.put('/api/delivery/agents/location',
        json={
            'latitude': 40.7589,
            'longitude': -73.9851
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # 4. Mark as delivered
    response = client.put(f'/api/delivery/tasks/{sample_task.id}/status',
        json={'status': 'delivered'},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'delivered'
    assert datetime.fromisoformat(data['delivery_time'])
    
    # Verify agent is available again
    assert sample_agent.is_available == True 