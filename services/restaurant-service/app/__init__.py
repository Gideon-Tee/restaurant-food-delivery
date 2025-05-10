from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(test_config=None):
    app = Flask(__name__)
    
    # Load the instance config, if it exists, when not testing
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@restaurant-db:5432/restaurant_db'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'your-secret-key')
        )
    else:
        # Load the test config if passed in
        app.config.update(test_config)
    
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