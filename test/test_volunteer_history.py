import unittest
from run import app
import sys
import psycopg2
import bcrypt

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

    def test_user_not_signed_in_returns_login_page(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = False

        response = self.tester.get('/history/')
        self.assertIn(str.encode("Welcome! Please login to continue."), response.data)

    def test_user_signed_in_gets_to_volunteer_history_page(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['user_id'] = self.user_id
            sess['is_admin'] = False

        response = self.tester.get('/history/')
        val = 'Volunteer Participation History'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        self.delete_unit_test_user_in_db()


if __name__ == "__main__":
    unittest.main()
