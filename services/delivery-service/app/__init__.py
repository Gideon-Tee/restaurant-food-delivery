import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import logging
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(test_config=None):
    app = Flask(__name__)

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@delivery-db:5432/delivery_db'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'super-secret-jwt-key-123'),
            ORDER_SERVICE_URL=os.getenv('ORDER_SERVICE_URL', 'http://order-service:5000'),
            USER_SERVICE_URL=os.getenv('USER_SERVICE_URL', 'http://user-service:5000'),
            AWS_REGION=os.getenv('AWS_REGION', 'us-east-1'),
            SNS_TOPIC_ARN=os.getenv('SNS_TOPIC_ARN', ''),
            SQS_QUEUE_URL=os.getenv('SQS_QUEUE_URL', '')
        )
    else:
        app.config.update(test_config)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Create database tables
    with app.app_context():
        from .models import DeliveryTask, DeliveryAgent
        db.create_all()
    
    # Register blueprints
    from .routes import delivery_bp
    app.register_blueprint(delivery_bp, url_prefix='/api/delivery')
    
    return app 