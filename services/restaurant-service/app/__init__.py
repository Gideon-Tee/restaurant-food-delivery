import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(test_config=None):
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Load the instance config, if it exists, when not testing
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@restaurant-db:5432/restaurant_db'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'super-secret-jwt-key-123'),
            JWT_ACCESS_TOKEN_EXPIRES=86400,  # 24 hours
            JWT_ERROR_MESSAGE_KEY='error',
            JWT_JSON_KEY='access_token',
            JWT_HEADER_NAME='Authorization',
            JWT_HEADER_TYPE='Bearer',
            JWT_TOKEN_LOCATION=['headers'],
            JWT_ALGORITHM='HS256',
            JSON_AS_ASCII=False,
            JSONIFY_MIMETYPE='application/json; charset=utf-8'
        )
    else:
        # Load the test config if passed in
        app.config.from_mapping(
            TESTING=True,
            SECRET_KEY='test',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY='super-secret-jwt-key-123',
            JWT_ACCESS_TOKEN_EXPIRES=86400,
            JWT_ERROR_MESSAGE_KEY='error',
            JWT_JSON_KEY='access_token',
            JWT_HEADER_NAME='Authorization',
            JWT_HEADER_TYPE='Bearer',
            JWT_TOKEN_LOCATION=['headers'],
            JWT_ALGORITHM='HS256',
            JSON_AS_ASCII=False,
            JSONIFY_MIMETYPE='application/json; charset=utf-8'
        )
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Create database tables
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from .models import Restaurant, MenuItem
        
        # Create tables
        db.create_all()
    
    # Register blueprints
    from .routes import restaurant_bp
    app.register_blueprint(restaurant_bp, url_prefix='/api/restaurants')
    
    return app 