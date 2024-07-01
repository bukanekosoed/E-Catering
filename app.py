from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_required, logout_user
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MongoClient and database initialization
client = MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('DB_NAME')]

# Login manager initialization
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

users_collection = db['users']
admins_collection = db['admins']

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

# Register blueprints
from routes.auth import create_auth_bp  # Import the factory function
app.register_blueprint(create_auth_bp(users_collection, admins_collection), url_prefix='/auth')

@app.before_request
def before_request():
    # Check if the user is authenticated and redirect based on their role
    if current_user.is_authenticated:
        if current_user.role == 'user' and request.endpoint == 'admin_dashboard':
            flash('Unauthorized access')
            return redirect(url_for('user_dashboard'))
        elif current_user.role == 'admin' and request.endpoint == 'user_dashboard':
            flash('Unauthorized access')
            return redirect(url_for('admin_dashboard'))
        
# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
