from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import bcrypt

main = Blueprint('main', __name__)

testUsers = [
    { 'email': 'rahmaaloui3199@gmail.com', 'password': bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') },
    { 'email': 'john.doe@example.com', 'password': bcrypt.hashpw('password1'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') },
    { 'email': 'jane.smith@example.com', 'password': bcrypt.hashpw('password2'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') },
    { 'email': 'michael.brown@example.com', 'password': bcrypt.hashpw('password3'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') },
    { 'email': 'emily.jones@example.com', 'password': bcrypt.hashpw('password4'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') }
]

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = next((user for user in testUsers if user['email'] == email), None)
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'message': 'Invalid email or password'}), 401

    return jsonify({'message': 'Login successful'}), 200

@main.route('/base')
def base():
    return render_template('base.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')

        if password != confirm_password:
            return jsonify({'message': 'Passwords do not match'}), 400

        user_exists = next((user for user in testUsers if user['email'] == email), None)
        if user_exists:
            return jsonify({'message': 'User already exists'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        testUsers.append({'email': email, 'password': hashed_password})

        return jsonify({'message': 'User registered successfully'}), 201

    return render_template('../templates/register.html')

@main.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')

        user = next((user for user in testUsers if user['email'] == email), None)
        if not user:
            return jsonify({'message': 'Email not found'}), 404

        reset_link = f"http://127.0.0.1:5000/reset?email={email}"
        print(f"Password reset link (simulated): {reset_link}")

        return jsonify({'message': 'Password reset link sent to your email'}), 200

    return render_template('forgot.html')

@main.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        new_password = data.get('newPassword')
        confirm_new_password = data.get('confirmNewPassword')

        if new_password != confirm_new_password:
            return jsonify({'message': 'Passwords do not match'}), 400

        user = next((user for user in testUsers if user['email'] == email), None)
        if not user:
            return jsonify({'message': 'Email not found'}), 404

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user['password'] = hashed_password

        return jsonify({'message': 'Password reset successfully'}), 200

    return render_template('reset.html')

@main.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        full_name = data.get('fullName')
        dob = data.get('dob')
        address1 = data.get('address1')
        address2 = data.get('address2')
        city = data.get('city')
        state = data.get('state')
        zip_code = data.get('zip')
        skills = data.get('skills')
        preferences = data.get('preferences')
        availability = data.get('availability')

        user = next((user for user in testUsers if user['email'] == email), None)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        user.update({
            'fullName': full_name,
            'dob': dob,
            'address1': address1,
            'address2': address2,
            'city': city,
            'state': state,
            'zip': zip_code,
            'skills': skills,
            'preferences': preferences,
            'availability': availability
        })

        return jsonify({'message': 'Profile updated successfully'})

    return render_template('profile.html')