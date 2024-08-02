from flask import render_template, request, jsonify, session, Blueprint
import bcrypt
import psycopg2
import re

auth_bp = Blueprint('auth', __name__)

# Connect to the database
conn = psycopg2.connect(database="volunteers_db", user="postgres",
                        password="arti", host="localhost", port="5432")


@auth_bp.route('/')
def index():
    if "signed_in" in session and session["signed_in"]:
        return render_template("base.html", email=session['email'], username=session['username'],
                               is_admin=session['is_admin'])
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        cursor = conn.cursor()

        command = f"SELECT id, password, is_admin FROM usercredentials where email='{email}';"

        cursor.execute(command)
        db_id_password = cursor.fetchone()
        cursor.close()

        if not db_id_password or not bcrypt.checkpw(password.encode('utf-8'), db_id_password[1].encode('utf-8')):
            session["signed_in"] = False
            return jsonify({'message': 'Invalid email or password'}), 401

        session['signed_in'] = True
        session['email'] = email
        session['username'] = session['email'].split('@')[0]
        session['user_id'] = db_id_password[0]
        session['is_admin'] = db_id_password[2]

        return jsonify({'message': 'Login successful'}), 200
    return render_template('index.html')


@auth_bp.route('/base')
def base():
    if session.get('signed_in') is None or session["signed_in"] == False:
        return render_template("index.html")

    return render_template('base.html', email=session['email'], username=session['username'],
                           is_admin=session['is_admin'])


@auth_bp.route("/logout")
def logout():
    session['signed_in'] = False
    session['email'] = ''
    session['username'] = ''
    return render_template("index.html")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        admin_or_user = data.get('is_admin')  # True -> admin
        cursor = conn.cursor()

        if password != confirm_password:
            return jsonify({'message': 'Passwords do not match'}), 400

        if not re.fullmatch(r'[A-Za-z0-9@#$%^&+=_]{8,}', password):
            return jsonify({
                'message': 'The password should be at least 8 characters long. The password may include uppercase letters: A-Z, lowercase letters: a-z, numbers: 0-9, any of the special characters: @#$%^&+=_'}), 400

        command = f"SELECT * from usercredentials where email='{email}';"
        cursor.execute(command)
        user_exists = len(cursor.fetchall())

        if user_exists > 0:
            return jsonify({'message': 'User already exists'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        session["signed_in"] = True

        session["email"] = email
        session['username'] = session['email'].split('@')[0]
        session['is_admin'] = admin_or_user

        command = f"INSERT INTO usercredentials (username, email, password, is_admin) VALUES ('{session['username']}', '{session['email']}','{hashed_password}', {session['is_admin']});"
        cursor.execute(command)

        cursor.execute(f"SELECT id FROM usercredentials WHERE email='{session['email']}'")
        session['user_id'] = cursor.fetchone()[0]

        command = (f"INSERT INTO notifications (user_id, msg, notification_type) "
                   f"VALUES ({session['user_id']}, '{session['username']} signed up!', {True});")
        cursor.execute(command)

        cursor.close()
        conn.commit()

        return jsonify({'message': 'User registered successfully'}), 201

    return render_template('register.html')


@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        cursor = conn.cursor()

        command = f"SELECT email FROM usercredentials where email='{email}';"

        cursor.execute(command)
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({'message': 'Email not found'}), 404

        reset_link = f"http://127.0.0.1:5000/reset?email={email}"
        print(f"Password reset link (simulated): {reset_link}")

        return jsonify({'message': 'Password reset link sent to your email'}), 200

    return render_template('forgot.html')


@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        new_password = data.get('newPassword')
        confirm_new_password = data.get('confirmNewPassword')
        cursor = conn.cursor()

        if new_password != confirm_new_password:
            return jsonify({'message': 'Passwords do not match'}), 400

        if not re.fullmatch(r'[A-Za-z0-9@#$%^&+=_]{8,}', new_password):
            return jsonify({'message': 'The password should be at least 8 characters long. The password may include uppercase letters: A-Z, lowercase letters: a-z, numbers: 0-9, any of the special characters: @#$%^&+=_'}), 400

        command = f"SELECT email FROM usercredentials where email='{email}';"

        cursor.execute(command)
        user = cursor.fetchone()

        if not user:
            return jsonify({'message': 'Email not found'}), 404

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        command = f"UPDATE usercredentials SET password = '{hashed_password}' where email='{email}';"
        cursor.execute(command)
        cursor.close()
        conn.commit()

        return jsonify({'message': 'Password reset successfully'}), 200
    email = request.args.get('email')
    return render_template('reset.html', email=email)
