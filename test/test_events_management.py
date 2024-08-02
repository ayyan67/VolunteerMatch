import unittest
import sys
import psycopg2
import bcrypt

sys.path.append("../VolunteerMatch")
from run import app


class EventManagementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tester = app.test_client(cls)

    def get_user_id_from_db(self, email):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        cursor.execute(f"SELECT id FROM usercredentials"
                       f" WHERE email='{email}';")
        self.user_id = cursor.fetchone()[0]
        cursor.close()
        conn.close()

    def create_unit_test_user_in_db(self):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        password = 'super_secret_password'
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        command = f"INSERT INTO usercredentials (username, email, password, is_admin)" \
                  f" VALUES ('unit_test', 'unit_test@domain.com', '{hashed_password}', true);"
        cursor.execute(command)
        conn.commit()
        cursor.close()
        conn.close()

        self.get_user_id_from_db('unit_test@domain.com')

    def delete_unit_test_user_in_db(self):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"DELETE FROM usercredentials " \
                  f"WHERE id = {self.user_id};"
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

        self.user_id = -1

    def setUp(self):
        self.user_id = -1
        self.delete_unit_test_user_in_db()

    def tearDown(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = False
            sess['email'] = ''
            sess['username'] = ''
            sess['user_id'] = -1
            sess['is_admin'] = False

    def test_event_management_signed_in_false(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = False

        response = self.tester.get('/events/')
        val = 'Welcome! Please login to continue.'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_event_management_signed_in_true(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True

        response = self.tester.get('/events/')
        val = 'Event Management Form'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_event_management_signed_in_true_for_non_admins_returns_base_page(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = False

        response = self.tester.get('/events/', content_type='text/HTML')

        self.assertIn(
            str.encode(f'<h2>Welcome, <span id="username" style="color:#44958f;">{sess["username"]}</span>!</h2>'),
            response.data)

        # since sess['is_admin'] is set to false, there should only be one btn.
        self.assertIn(str.encode("Volunteer History"), response.data)
        self.assertEqual(200, response.status_code)

    def test_display_signed_in_false(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = False

        response = self.tester.get('/events/display.html')
        val = 'Welcome! Please login to continue.'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_display_signed_in_true(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = self.user_id
            sess['is_admin'] = True

        data = {"eventName": "My Event",
                "eventDescription": "This is an event",
                "location": 'Houston',
                "requiredSkills": "ms",
                "urgency": "low",
                "eventDate": "2024-07-08"
                }

        response = self.tester.get('/events/display.html', query_string=data)
        formatted_event_date = "".join(str(data['eventDate']).split('-'))

        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"SELECT user_id, event_id FROM event_details " \
                  f"WHERE event_name = \'{data['eventName']}\' AND description = \'{data['eventDescription']}\' AND " \
                  f"location = \'{data['location']}\' AND required_skills = \'{data['requiredSkills']}\' AND " \
                  f"urgency = \'{data['urgency']}\' AND event_date = date({formatted_event_date}::TEXT);"
        cursor.execute(command)
        table_data = cursor.fetchone()

        self.assertEqual(table_data[0], self.user_id)  # asserts that the event was stored in the db
        self.assertIn(str.encode("Event Details"), response.data)  # asserts that the event details page was displayed
        self.assertEqual(200, response.status_code)

        command = (f"DELETE FROM event_details "
                   f"WHERE event_id = {table_data[1]};")
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

        self.delete_unit_test_user_in_db()

    def test_display_signed_in_true_for_non_admins_redirects_to_base(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = False

        response = self.tester.get('/events/display.html', content_type='text/HTML')

        self.assertIn(
            str.encode(f'<h2>Welcome, <span id="username" style="color:#44958f;">{sess["username"]}</span>!</h2>'),
            response.data)

        # since sess['is_admin'] is set to false, there should only be one btn.
        self.assertIn(str.encode("Volunteer History"), response.data)
        self.assertEqual(200, response.status_code)


if __name__ == "__main__":
    unittest.main()
