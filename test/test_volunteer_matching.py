import unittest
import psycopg2
import bcrypt

from run import app
from app.volunteer_matching.routes import events, volunteers
import sys

sys.path.append("../VolunteerMatch")


class VolunteerMatchingTest(unittest.TestCase):
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

    def create_unit_test_user_profile_in_db(self):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()
        command = f"INSERT INTO user_profile(user_id, full_name, address_1, address_2, city, state, zipcode, skills, preference, availability, dob) " \
                  f"VALUES({self.user_id}, 'Unit Test', '1234 Road St.', '', 'Houston', 'Tx', '77001', 'skill1,skill2,skill3', 'skill1', date(20240831::TEXT), date(19980621::TEXT));"
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

    def delete_unit_test_user_profile_in_db(self):
        if self.user_id == -1:
            return

        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()
        command = f"DELETE FROM user_profile WHERE " \
                  f"user_id = {self.user_id}; "
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

    def create_sample_event_in_db(self, name):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f'''INSERT INTO event_details(
                    event_name, description, location, required_skills, urgency, event_date, user_id)
                    VALUES('{name}','Unit Test Event Description','Unit Test Event Location','skill1,skill2,skill3','High',date(20240831::TEXT),{self.user_id}); '''
        cursor.execute(command)
        conn.commit()
        cursor.close()
        conn.close()

    def delete_sample_event_in_db(self, name):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"DELETE FROM event_details WHERE " \
                  f"event_name = '{name}' AND description = 'Unit Test Event Description' " \
                  f"AND location = 'Unit Test Event Location' AND user_id = {self.user_id};"
        cursor.execute(command)
        conn.commit()
        cursor.close()
        conn.close()

    def delete_notification_for_unit_test_user(self):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = (f"DELETE FROM notifications "
                   f"WHERE user_id = {self.user_id};")
        cursor.execute(command)
        conn.commit()
        cursor.close()
        conn.close()

    def delete_volunteer_history_for_unit_test_user(self):
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        # delete from history
        command = f"DELETE FROM volunteer_history WHERE user_id = {self.user_id};"
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

    def setUp(self):
        self.user_id = -1
        self.delete_sample_event_in_db('Unit Test Event')
        self.delete_unit_test_user_profile_in_db()
        self.delete_unit_test_user_in_db()

    def tearDown(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = False
            sess['email'] = ''
            sess['username'] = ''
            sess['user_id'] = -1
            sess['is_admin'] = False

    def test_user_not_signed_in(self):
        response = self.tester.get('/matching/')
        self.assertIn(str.encode("Welcome! Please login to continue."), response.data)

    def test_user_signed_in_as_admin_redirects_to_volunteer_matching_page(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = -1
            sess['is_admin'] = True

        response = self.tester.get('/matching/')
        val = 'Volunteer Info'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_user_signed_in_as_non_admin_redirects_to_base_page(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = -1
            sess['is_admin'] = False

        response = self.tester.get('/matching/', content_type='text/HTML')

        self.assertIn(
            str.encode(f'<h2>Welcome, <span id="username" style="color:#44958f;">{sess["username"]}</span>!</h2>'),
            response.data)

        # since sess['is_admin'] is set to false, there should only be one btn.
        self.assertIn(str.encode("Volunteer History"), response.data)
        self.assertEqual(200, response.status_code)

    def test_assign_event_successfully_assigns_event(self):
        self.create_unit_test_user_in_db()
        self.create_unit_test_user_profile_in_db()
        self.create_sample_event_in_db('Unit Test Event')

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = self.user_id
            sess['is_admin'] = True

        data = {
            "user_id": self.user_id,
            "volunteer_name": "Unit Test",
            "event_name": "Unit Test Event"
        }
        response = self.tester.post('/matching/api/assign_event', json=data)
        val = '{"message":"Event \'Unit Test Event\' assigned to volunteer \'Unit Test\'"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        self.delete_notification_for_unit_test_user()
        self.delete_volunteer_history_for_unit_test_user()

        self.delete_sample_event_in_db('Unit Test Event')
        self.delete_unit_test_user_profile_in_db()
        self.delete_unit_test_user_in_db()

    def test_assign_event_tries_to_assign_same_event_to_same_user_twice(self):
        self.create_unit_test_user_in_db()
        self.create_unit_test_user_profile_in_db()
        self.create_sample_event_in_db('Unit Test Event')

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = self.user_id
            sess['is_admin'] = True

        data = {
            "user_id": self.user_id,
            "volunteer_name": "Unit Test",
            "event_name": "Unit Test Event"
        }
        self.tester.post('/matching/api/assign_event', json=data)
        response = self.tester.post('/matching/api/assign_event', json=data)

        val = '{"message":"Event \'Unit Test Event\' HAS ALREADY BEEN assigned to volunteer \'Unit Test\'."}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        self.delete_notification_for_unit_test_user()
        self.delete_volunteer_history_for_unit_test_user()

        self.delete_sample_event_in_db('Unit Test Event')
        self.delete_unit_test_user_profile_in_db()
        self.delete_unit_test_user_in_db()

    def test_try_to_assign_event_with_non_existing_volunteer(self):
        self.delete_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = -1
            sess['is_admin'] = True

        data = {
            "user_id": -1,
            "volunteer_name": "Unit Test",
            "event_name": "Unit Test Event"
        }
        response = self.tester.post('/matching/api/assign_event', json=data)
        val = '{"error":"Volunteer not found"}\n'
        self.assertEqual(str.encode(val), response.data)

    def test_get_volunteers_using_a_non_admin_user_gets_back_self_history(self):
        self.create_unit_test_user_in_db()
        self.create_unit_test_user_profile_in_db()
        self.create_sample_event_in_db('Unit Test Event')

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = self.user_id
            sess['is_admin'] = False

        # assign the sample event to the unit test user
        data = {
            "user_id": self.user_id,
            "volunteer_name": "Unit Test",
            "event_name": "Unit Test Event"
        }
        self.tester.post('/matching/api/assign_event', json=data)

        response = self.tester.post('/matching/api/volunteers', json={'user_id': self.user_id})

        self.assertEqual(self.user_id, response.json[0]['user_id'])
        self.assertEqual('Unit Test', response.json[0]['name'])
        self.assertEqual('1234 Road St.', response.json[0]['address1'])
        self.assertEqual('unit_test@domain.com', response.json[0]['email'])
        self.assertEqual('77001', response.json[0]['zip'])

        self.delete_notification_for_unit_test_user()
        self.delete_volunteer_history_for_unit_test_user()

        self.delete_sample_event_in_db('Unit Test Event')
        self.delete_unit_test_user_profile_in_db()
        self.delete_unit_test_user_in_db()


if __name__ == "__main__":
    unittest.main()
