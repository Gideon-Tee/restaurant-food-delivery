import pytest
import os
import sys
from datetime import datetime, timedelta
import jwt
import uuid
from sqlalchemy.orm import sessionmaker, scoped_session

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import DeliveryAgent, DeliveryTask

@pytest.fixture(scope='session')
def app():
    """Create and configure a test application instance."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'ORDER_SERVICE_URL': 'http://order-service:5000',
        'USER_SERVICE_URL': 'http://user-service:5000',
        'AWS_REGION': 'us-east-1',
        'SNS_TOPIC_ARN': 'test-topic-arn',
        'SQS_QUEUE_URL': 'test-queue-url'
    }
    
    app = create_app(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def session(app):
    """Create a new database session for a test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Create a new session factory bound to the connection
        factory = sessionmaker(bind=connection)
        # Create a new scoped session
        _session = scoped_session(factory)
        
        # Override the default session with our test session
        db.session = _session
        
        yield _session
        
        # Cleanup
        _session.remove()
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    """Create authentication headers with a valid JWT token for testing."""
    # Create a valid token with required claims
    token_data = {
        'fresh': False,
        'iat': datetime.utcnow(),
        'jti': 'test-jwt-id',
        'type': 'access',
        'sub': '1',  # user_id
        'nbf': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=1),
        'role': 'driver'  # Important: this matches the role check in routes
    }
    
    token = jwt.encode(
        token_data,
        app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return {
        'Authorization': f'Bearer {token}'
    }

@pytest.fixture
def mock_order_response(monkeypatch):
    """Mock the order service response."""
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            
            def json(self):
                return {
                    'id': 1,
                    'restaurant_latitude': 40.7128,
                    'restaurant_longitude': -74.0060,
                    'delivery_latitude': 40.7589,
                    'delivery_longitude': -73.9851
                }
            
            def raise_for_status(self):
                pass
        
        return MockResponse()
    
    import requests
    monkeypatch.setattr(requests, 'get', mock_get)

@pytest.fixture
def mock_sns_publish(monkeypatch):
    """Mock the SNS publish function."""
    def mock_publish(*args, **kwargs):
        return {'MessageId': 'test-message-id'}
    
    class MockSNS:
        def __init__(self, *args, **kwargs):
            pass
        
        def publish(self, *args, **kwargs):
            return mock_publish(*args, **kwargs)
    
    import boto3
    monkeypatch.setattr(boto3, 'client', lambda service, region_name: MockSNS())

@pytest.fixture
def sample_agent(session):
    """Create a sample delivery agent with a unique user ID."""
    agent = DeliveryAgent(
        user_id=str(uuid.uuid4()),
        vehicle_type='motorcycle',
        current_latitude=40.7128,
        current_longitude=-74.0060,
        is_available=True
    )
    session.add(agent)
    session.commit()
    return agent

@pytest.fixture
def sample_task(session, sample_agent):
    """Create a sample delivery task."""
    task = DeliveryTask(
        order_id=1,
        agent_id=sample_agent.id,
        pickup_latitude=40.7128,
        pickup_longitude=-74.0060,
        delivery_latitude=40.7589,
        delivery_longitude=-73.9851,
        status='assigned'
    )
    session.add(task)
    session.commit()
    return task 