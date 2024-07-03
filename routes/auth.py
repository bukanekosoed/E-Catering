from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
import re
from models import User  # Correctly import User model


# Initialize Flask-Bcrypt
bcrypt = Bcrypt()

def create_auth_bp(users_collection, admins_collection):
    auth_bp = Blueprint('auth', __name__)

    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            user = users_collection.find_one({'email': email})
            if user and bcrypt.check_password_hash(user['password'], password):
                user_obj = User(id=str(user['_id']), email=user['email'], role='user')
                login_user(user_obj)
                return redirect(url_for('index'))

            admin = admins_collection.find_one({'email': email})
            if admin and bcrypt.check_password_hash(admin['password'], password):
                admin_obj = User(id=str(admin['_id']), email=admin['email'], role='admin')
                login_user(admin_obj)
                return redirect(url_for('admin.dashboard'))

            flash('Invalid email or password')

        return render_template('auth/login.html')

    @auth_bp.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email']
            name = request.form['name']
            phone = request.form['phone']
            password = request.form['password']
            confirm_password = request.form['confirmPassword']
            role = 'user'  # Assuming registration is only for users

            

            

            # Validasi bahwa semua field diisi
            if not email or not name or not phone or not password or not confirm_password:
                flash('Silakan lengkapi semua kolom.')
                return redirect(url_for('auth.register'))
            # Validasi panjang nomor telepon
            elif len(phone) < 10 or len(phone) > 15:  # Sesuaikan panjang yang diinginkan
                flash('Panjang nomor telepon harus antara 10 dan 15 karakter.')
                return redirect(url_for('auth.register'))
            # Validasi panjang dan kompleksitas password dengan regex
            elif not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()-+=]).{8,}$', password):
                flash('Password harus terdiri dari setidaknya satu angka, satu huruf kecil, satu huruf besar, satu karakter khusus, dan minimal 8 karakter.')
                return redirect(url_for('auth.register'))
            elif password != confirm_password:
                flash('Passwords do not match')
                return redirect(url_for('auth.register'))
            
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            

            if users_collection.find_one({'email': email}):
                flash('Email already exists')
            else:
                users_collection.insert_one({
                    'email': email,
                    'name': name,
                    'phone': phone,
                    'password': hashed_password
                })
                flash('Registration successful. Please log in.')
                return redirect(url_for('auth.login'))

        return render_template('auth/register.html')


    return auth_bp
