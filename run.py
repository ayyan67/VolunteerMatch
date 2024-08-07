from flask import Flask
from app.auth.routes import auth_bp
from app.user_profile.routes import profile_bp
from app.events_management.routes import events_bp
from app.volunteer_matching.routes import matching_bp
from app.notifications.routes import notifications_bp
from app.volunteer_history.routes import history_bp
from app.reporting.routes import reporting_bp
# import psycopg2

app = Flask(__name__)
app.config["SECRET_KEY"] = "4567"

# # Connect to the database
# conn = psycopg2.connect(database="volunteers_db", user="postgres",
#                         password="arti", host="localhost", port="5432")
#
# # create a cursor
# cur = conn.cursor()
#
#
# # Select all products from the table
# cur.execute('''SELECT * from "UserCredentials";''')
#
# # Fetch the data
# data = cur.fetchall()
# print("data from table==>",data)
# # close the cursor and connection
# cur.close()
# conn.close()



app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(events_bp, url_prefix='/events')
app.register_blueprint(matching_bp, url_prefix='/matching')
app.register_blueprint(notifications_bp, url_prefix='/notifications')
app.register_blueprint(history_bp, url_prefix='/history')
app.register_blueprint(reporting_bp, url_prefix='/reporting')


if __name__ == '__main__':
    app.run(debug=True)
