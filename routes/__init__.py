# routes/__init__.py

from flask import Blueprint

# Inisialisasi blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_bp = Blueprint('user', __name__, url_prefix='/user')

# Import route handlers
from . import admin, user
