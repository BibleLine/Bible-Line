from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# In-memory user database
users_db = {}

# In-memory sessions database
active_sessions = {}

# Initialize with a sample user (optional)
users_db['demo@bibleline.com'] = {
    'username': 'demo',
    'email': 'demo@bibleline.com',
    'password_hash': generate_password_hash('demo123'),
    'created_at': datetime.now().isoformat()
}

@app.route('/')
def home():
    """Serve the home page"""
    # Check if user is logged in via session
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    """Serve the login/signup page"""
    return render_template('login.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    """Handle user registration"""
    data = request.json
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    # Validation
    if not email or not username or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    if email in users_db:
        return jsonify({'error': 'Email already registered'}), 400
    
    # Check if username is taken
    for user_data in users_db.values():
        if user_data['username'].lower() == username.lower():
            return jsonify({'error': 'Username already taken'}), 400
    
    # Create new user
    users_db[email] = {
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'created_at': datetime.now().isoformat()
    }
    
    # Log the user in
    session['user_id'] = email
    session['username'] = username
    
    return jsonify({'success': True, 'message': 'Account created successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Check if user exists
    if email not in users_db:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    user = users_db[email]
    
    # Verify password
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Create session
    session['user_id'] = email
    session['username'] = user['username']
    
    return jsonify({'success': True, 'message': 'Logged in successfully!'}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/dashboard')
def dashboard():
    """User dashboard - protected route"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    if user_id in users_db:
        user = users_db[user_id]
        return jsonify({
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at']
        }), 200
    
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/count', methods=['GET'])
def get_users_count():
    """Get total number of registered users"""
    return jsonify({'total_users': len(users_db)}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
