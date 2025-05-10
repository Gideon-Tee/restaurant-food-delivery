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
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@user-db:5432/user_db'),
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
        from .models import User, Role
        
        # Create tables
        db.create_all()
        
        # Create default roles if they don't exist
        if not Role.query.filter_by(name='customer').first():
            customer_role = Role(name='customer')
            db.session.add(customer_role)
        
        if not Role.query.filter_by(name='restaurant_owner').first():
            restaurant_role = Role(name='restaurant_owner')
            db.session.add(restaurant_role)
        
        if not Role.query.filter_by(name='delivery_person').first():
            delivery_role = Role(name='delivery_person')
            db.session.add(delivery_role)
        
        db.session.commit()
    
    # Register blueprints
    from .routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/users')
    
    return app 