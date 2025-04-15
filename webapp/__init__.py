from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from webapp.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from webapp.views.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app