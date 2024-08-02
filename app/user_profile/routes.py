from flask import render_template, request, jsonify, session, Blueprint
import psycopg2

profile_bp = Blueprint('profile', __name__)

# Connect to the database
conn = psycopg2.connect(database="volunteers_db", user="postgres",
                        password="arti", host="localhost", port="5432")


@profile_bp.route('/', methods=['GET', 'POST'])
def profile():
    if session.get('signed_in') is None or session["signed_in"] == False:
        return render_template("index.html")

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

        # print(f"dob = {dob}")
        # print(f"type(dob)= {type(dob)}")

        formatted_skills = ""
        for i, skill in enumerate(skills):
            formatted_skills += skill + ("," if i < len(skills) - 1 else "")

        formatted_dob = "".join(str(dob).split('-'))
        formatted_availability_date = "".join(str(availability).split('-'))

        # check if there's already an entry in the user_profile table.
        # if yes: use UPDATE
        # else: use INSERT

        cursor = conn.cursor()

        command = f'''SELECT user_id FROM user_profile WHERE user_id = {session['user_id']};'''
        cursor.execute(command)
        table_data = cursor.fetchone()

        if table_data:  # profile row already exists
            command = f'''UPDATE user_profile
                          SET full_name = '{full_name}', address_1 = '{address1}', address_2 = '{address2}', 
                              city = '{city}', state = '{state}', zipcode = '{zip_code}', skills = '{formatted_skills}', 
                              preference = '{preferences}', availability = date({formatted_availability_date}::TEXT),
                              dob = date({formatted_dob}::TEXT)
                          WHERE user_id = {session['user_id']}'''
        else:
            command = f'''INSERT INTO user_profile(user_id, full_name, address_1, address_2, city, state, zipcode, skills, preference, availability, dob)
                        VALUES({session["user_id"]}, '{full_name}', '{address1}', '{address2}', '{city}', '{state}', '{zip_code}', '{formatted_skills}', '{preferences}', date({formatted_availability_date}::TEXT), date({formatted_dob}::TEXT));'''

        cursor.execute(command)
        cursor.close()
        conn.commit()

        return jsonify({'message': 'Profile updated successfully'}), 200

    cursor = conn.cursor()
    command = f"SELECT *\
                FROM user_profile\
                WHERE user_id = '{session['user_id']}';"
    cursor.execute(command)
    table_data = cursor.fetchone()
    cursor.close()

    if table_data:
        full_name = table_data[1]
        address1, address2 = table_data[2], table_data[3]
        city, state, zipcode = table_data[4], table_data[5], table_data[6]
        skills, preferences, availability, dob = table_data[7], table_data[8], table_data[9], table_data[10]
        skills = skills.split(',')
        print("DOB==>",dob)
    else:
        full_name = ""
        address1, address2 = "", ""
        city, state, zipcode = "", "Select your state", ""
        skills, preferences, availability, dob = [], "", "", ""

    return render_template('profile.html', username=session['username'], full_name=full_name, dob=dob,
                           preferences=preferences, address1=address1, address2=address2, city=city, state=state,
                           zipcode=zipcode, availability=availability, skills=skills)
