from flask import Flask
from .config import Config
from .model import init_db
from .views import views_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register Blueprints
    app.register_blueprint(views_bp)

    # Init DB connection pool or helpers if needed
    init_db(app)

    return app
