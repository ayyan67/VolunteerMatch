from flask import Blueprint, render_template, session
import psycopg2

history_bp = Blueprint('history', __name__)

# Connect to the database
conn = psycopg2.connect(database="volunteers_db", user="postgres",
                        password="arti", host="localhost", port="5432")


@history_bp.route('/', methods=['GET', 'POST'])
def volunteer_history():
    if session.get('signed_in') is None or session["signed_in"] == False:
        return render_template("index.html")

    return render_template('volunteer_history.html', username=session['username'], user_id=session['user_id'])
