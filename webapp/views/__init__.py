from flask import Blueprint

views_bp = Blueprint('views', __name__)

# Import your routes here
from . import index, medication, interaction_results