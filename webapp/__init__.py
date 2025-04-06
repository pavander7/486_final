from flask import Flask
from .views_bp import views_bp

app = Flask(__name__)
app.register_blueprint(views_bp)
