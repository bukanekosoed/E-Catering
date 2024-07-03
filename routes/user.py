# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import menus_collection
from werkzeug.utils import secure_filename
import os
from bson import ObjectId

user_bp = Blueprint('user', __name__)

# UPLOAD_FOLDER = 'static/assets/img/menu'
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'user':
            flash('Unauthorized access')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

