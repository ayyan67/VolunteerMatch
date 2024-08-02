from flask import Blueprint, render_template, jsonify, request, session
import psycopg2
from .models import Volunteer, Event

matching_bp = Blueprint('matching', __name__)

# Connect to the database
conn = psycopg2.connect(database="volunteers_db", user="postgres",
                        password="arti", host="localhost", port="5432")

events = []
volunteers = []


@matching_bp.route('/', methods=['GET'])
def volunteer_matching():
    if session.get('signed_in') is None or session["signed_in"] == False:
        return render_template("index.html")

    if not session['is_admin']:
        return render_template('base.html', email=session['email'], username=session['username'],
                               is_admin=session['is_admin'])

    # get_volunteers()
    # get_events()
    # get_events()
    return render_template('volunteer_matching.html', username=session['username'])


@matching_bp.route('/api/volunteers', methods=['GET', 'POST'])
def get_volunteers():
    global volunteers
    if len(volunteers) > 0:
        volunteers = []

    data = request.get_json()

    cursor = conn.cursor()
    user_id = data.get('user_id')

    if session['is_admin'] or user_id == -1:
        command = f"SELECT * FROM user_profile;"
    else:
        command = f"SELECT * FROM user_profile WHERE user_id = {data['user_id']};"

    cursor.execute(command)
    table_data = cursor.fetchall()

    # create Volunteer objects and store in volunteer list
    for row in table_data:
        # fetch this user's email
        command = f"SELECT email FROM usercredentials WHERE id = {row[0]};"
        cursor.execute(command)
        email = cursor.fetchone()[0]

        # Fetch volunteer's history.
        command = f"SELECT event_id FROM volunteer_history WHERE user_id = {row[0]};"
        cursor.execute(command)
        history = []
        table_data = cursor.fetchall()

        for hist in table_data:
            history.append({"event_id": hist[0], "status": "Incomplete"})
        # End volunteer history

        formatted_skills = row[7].split(',')
        volunteer = Volunteer(
            user_id=row[0],
            name=row[1],
            address1=row[2],
            address2=row[3],
            city=row[4],
            state=row[5],
            zip=row[6],
            skills=formatted_skills,
            preferences=row[8],
            availability=[row[9]],
            email=email,
            # phone="(123)-456-7890",
            history=history
        )
        volunteers.append(volunteer)

    cursor.close()

    return jsonify([volunteer.to_dict() for volunteer in volunteers])


@matching_bp.route('/api/events', methods=['GET'])
def get_events():
    global events
    if len(events) > 0:
        events = []

    cursor = conn.cursor()

    command = f"SELECT * FROM event_details;"

    cursor.execute(command)
    table_data = cursor.fetchall()
    cursor.close()

    # create Event objects and store in event list
    for row in table_data:
        formatted_required_skills = row[4].split(",")
        event = Event(
            name=row[1],
            description=row[2],
            location=row[3],
            required_skills=formatted_required_skills,
            urgency=row[5],
            date=row[6],
            id=row[0],
        )
        events.append(event)

    return jsonify([event.to_dict() for event in events])


@matching_bp.route('/api/assign_event', methods=['POST'])
def assign_event():
    data = request.get_json()
    user_id = data.get('user_id')
    volunteer_name = data.get('volunteer_name')
    event_name = data.get('event_name')

    get_volunteers()
    get_events()

    for volunteer in volunteers:
        # if volunteer.name == volunteer_name:
        if volunteer.user_id == user_id:
            volunteer.assigned_event = event_name
            cursor = conn.cursor()
            # command = f'''SELECT user_id FROM user_profile WHERE full_name = '{volunteer_name}';'''
            # cursor.execute(command)
            # user_id = cursor.fetchone()[0]

            command = f'''SELECT event_id, event_date FROM event_details WHERE event_name = '{event_name}';'''
            cursor.execute(command)
            table_data = cursor.fetchone()
            event_id = table_data[0]
            event_date = table_data[1]

            command = f'''SELECT * from volunteer_history WHERE user_id = {user_id} AND event_id = {event_id};'''
            cursor.execute(command)
            table_data = cursor.fetchone()
            if table_data:
                return jsonify({
                                   "message": f"Event '{event_name}' HAS ALREADY BEEN assigned to volunteer '{volunteer_name}'."}), 200

            command = f'''INSERT INTO volunteer_history(user_id, event_id) VALUES ('{user_id}', '{event_id}');'''
            cursor.execute(command)

            command = (f"INSERT INTO notifications (user_id, msg, notification_type) "
                       f"VALUES ({user_id}, 'You have been assigned the event {event_name} on {event_date}', {False});")
            cursor.execute(command)

            cursor.close()
            conn.commit()
            return jsonify({"message": f"Event '{event_name}' assigned to volunteer '{volunteer_name}'"}), 200

    return jsonify({"error": "Volunteer not found"}), 404
