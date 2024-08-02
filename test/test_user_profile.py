import unittest
import psycopg2
import bcrypt
from run import app
import sys

sys.path.append("../VolunteerMatch")


class AuthTest(unittest.TestCase):
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

    def test_user_not_signed_in(self):
        response = self.tester.get('/profile/')
        self.assertIn(str.encode("Welcome! Please login to continue."), response.data)

    def test_user_signed_in_goes_to_profile(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True

        response = self.tester.get('/profile/')
        val = 'User Profile Management'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_save_user_profile_info_for_the_first_time(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = "unit_test@domain.com"
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True
            sess['user_id'] = self.user_id

        data = {
            'email': 'unit_test@domain.com',
            'fullName': 'Unit Test',
            'dob': '1998-06-21',
            'address1': '1234 Road St.',
            'address2': '',
            'city': 'Houston',
            'state': 'Tx',
            'zip': '77001',
            'skills': ['Skill1', 'Skill2'],
            'preferences': 'Skill1',
            'availability': '2024-08-31'
        }

        response = self.tester.post('/profile/', json=data)
        val = '{"message":"Profile updated successfully"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        # delete the user profile row from table user_profile
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"DELETE FROM user_profile " \
                  f"WHERE user_id = {self.user_id};"
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

        self.delete_unit_test_user_in_db()

    def test_save_user_profile_info_update_the_old_record(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = "unit_test@domain.com"
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True
            sess['user_id'] = self.user_id

        data = {
            'email': 'unit_test@domain.com',
            'fullName': 'Unit Test',
            'dob': '1998-06-21',
            'address1': '1234 Road St.',
            'address2': '',
            'city': 'Houston',
            'state': 'Tx',
            'zip': '77001',
            'skills': ['Skill1', 'Skill2'],
            'preferences': 'Skill1',
            'availability': '2024-08-31'
        }

        formatted_skills = ""
        for i, skill in enumerate(data['skills']):
            formatted_skills += skill + ("," if i < len(data['skills']) - 1 else "")

        formatted_dob = "".join(str(data['dob']).split('-'))
        formatted_availability_date = "".join(str(data['availability']).split('-'))

        # save the user_profile
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()
        command = f'''INSERT INTO user_profile(user_id, full_name, address_1, address_2, city, state, zipcode, skills, preference, availability, dob)
                                VALUES({sess["user_id"]}, 'Old Name', 'Old Address', '{data['address2']}', '{data['city']}', '{data['state']}', '{data['zip']}', '{formatted_skills}', '{data['preferences']}', date({formatted_availability_date}::TEXT), date({formatted_dob}::TEXT));'''
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

        response = self.tester.post('/profile/', json=data)
        val = '{"message":"Profile updated successfully"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        # check if it has indeed been updated
        # delete the user profile row from table user_profile
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"SELECT * FROM user_profile where user_id = {self.user_id};"
        cursor.execute(command)
        table_data = cursor.fetchone()
        self.assertEqual('Unit Test', table_data[1])
        self.assertEqual('1234 Road St.', table_data[2])

        command = f"DELETE FROM user_profile " \
                  f"WHERE user_id = {self.user_id};"
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

        self.delete_unit_test_user_in_db()

    def test_get_request_user_data_already_exists_in_db(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = "unit_test@domain.com"
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True
            sess['user_id'] = self.user_id

        data = {
            'email': 'unit_test@domain.com',
            'fullName': 'Unit Test',
            'dob': '1998-06-21',
            'address1': '1234 Road St.',
            'address2': '',
            'city': 'Houston',
            'state': 'Tx',
            'zip': '77001',
            'skills': ['Skill1', 'Skill2'],
            'preferences': 'Skill1',
            'availability': '2024-08-31'
        }

        formatted_skills = ""
        for i, skill in enumerate(data['skills']):
            formatted_skills += skill + ("," if i < len(data['skills']) - 1 else "")

        formatted_dob = "".join(str(data['dob']).split('-'))
        formatted_availability_date = "".join(str(data['availability']).split('-'))

        # save the user_profile
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()
        command = f'''INSERT INTO user_profile(user_id, full_name, address_1, address_2, city, state, zipcode, skills, preference, availability, dob)
                                VALUES({sess["user_id"]}, '{data['fullName']}', '{data['address1']}', '{data['address2']}', '{data['city']}', '{data['state']}', '{data['zip']}', '{formatted_skills}', '{data['preferences']}', date({formatted_availability_date}::TEXT), date({formatted_dob}::TEXT));'''
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

        response = self.tester.get('/profile/', json=data)
        self.assertIn(str.encode(f"{data['fullName']}"), response.data)
        self.assertIn(str.encode(f"{data['address1']}"), response.data)

        # delete the user profile row from table user_profile
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"DELETE FROM user_profile " \
                  f"WHERE user_id = {self.user_id};"
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

        self.delete_unit_test_user_in_db()


if __name__ == "__main__":
    unittest.main()
