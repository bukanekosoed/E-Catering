# app.py

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_required, logout_user
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from models import menus_collection, carts_collection,users_collection,admins_collection
from routes.admin import admin_bp
from routes.user import user_bp  # Import the new user blueprint

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
  # Sesuaikan dengan domain Ngrok Anda
app.secret_key = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'static/assets/img/menu'
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)  # Register the new user blueprint

# MongoClient and database initialization
client = MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('DB_NAME')]

# Login manager initialization
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'



@login_manager.user_loader
def load_user(user_id):
    from models import User  # Import here to avoid circular import issues
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        return User(id=str(user['_id']), email=user['email'], role='user')
    
    admin = admins_collection.find_one({'_id': ObjectId(user_id)})
    if admin:
        return User(id=str(admin['_id']), email=admin['email'], role='admin')
    
    return None

def get_cart_items_count():
    cart_items_count = 0
    if current_user.is_authenticated:
        user_id = current_user.id  # Assuming 'carts' is the collection name
        cart = carts_collection.find_one({'user_id': user_id})
        if cart:
            cart_items_count = len(cart.get('cart_items', []))
    return cart_items_count

def format_idr(angka):
    return f'Rp {angka:,}'.replace(',', '.')

app.jinja_env.filters['format_idr'] = format_idr


# Register blueprints
from routes.auth import create_auth_bp  # Import the factory function
app.register_blueprint(create_auth_bp(users_collection, admins_collection), url_prefix='/auth')

@app.before_request
def before_request():
    # Check if the user is authenticated and redirect based on their role
    if current_user.is_authenticated:
        if current_user.role == 'user' and request.endpoint == 'dashboard':
            flash('Unauthorized access','danger')
            return redirect(url_for('index'))
        elif current_user.role == 'admin' and request.endpoint == 'index':
            flash('Unauthorized access','danger')
            return redirect(url_for('admin.dashboard'))

# Routes
@app.route('/')
def index():
    cart_items_count = get_cart_items_count()
    menus = list(menus_collection.find({}))
    categories = menus_collection.distinct('kategori')
    return render_template('index.html', menus=menus, categories=categories, cart_items_count=cart_items_count)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
