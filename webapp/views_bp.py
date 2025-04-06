from flask import Blueprint

views_bp = Blueprint('views', __name__)

from . import index  # Import your route files here, such as autocomplete.py