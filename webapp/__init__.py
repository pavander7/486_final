from flask import Flask

app = Flask(__name__)

# Import views_bp after app is created to avoid circular import
from webapp.views import views_bp
app.register_blueprint(views_bp)