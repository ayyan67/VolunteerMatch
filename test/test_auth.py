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
        if self.user_id == -1:
            return

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

    def delete_notifications_using_user_id(self):
        if self.user_id == -1:
            return

        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"DELETE FROM notifications " \
                  f"WHERE user_id = {self.user_id};"
        cursor.execute(command)
        cursor.close()
        conn.commit()
        conn.close()

    def setUp(self):
        self.user_id = -1
        self.delete_notifications_using_user_id()
        self.delete_unit_test_user_in_db()

    def tearDown(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = False
            sess['email'] = ''
            sess['username'] = ''
            sess['user_id'] = -1
            sess['is_admin'] = False

    def test_canary(self):
        self.assertTrue(True)

    def test_index_get_back_index_when_not_signed_in(self):
        response = self.tester.get('/', content_type='text/HTML')
        val = 'Welcome! Please login to continue.'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_index_get_back_base_when_signed_in(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True

        response = self.tester.get('/', content_type='text/HTML')

        self.assertIn(
            str.encode(f'<h2>Welcome, <span id="username" style="color:#44958f;">{sess["username"]}</span>!</h2>'),
            response.data)

        # since sess['is_admin'] is set to true, there should be the following two btns.
        self.assertIn(str.encode("Event Management Form"), response.data)
        self.assertIn(str.encode("Volunteer Matching Form"), response.data)
        self.assertIn(str.encode("Volunteer History"), response.data)
        self.assertEqual(200, response.status_code)

    def test_login_send_get_request(self):
        response = self.tester.get('/login')
        val = 'Welcome! Please login to continue.'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_login_incorrect_pwd(self):
        # Create test account, try logging in with wrong pwd.
        self.create_unit_test_user_in_db()

        data = {
            "email": "unit_test@domain.com",
            "password": "abcd"
        }

        response = self.tester.post('/login', json=data)
        val = '{"message":"Invalid email or password"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(401, response.status_code)

        self.delete_unit_test_user_in_db()

    def test_login_correct_pwd(self):
        # Create test account, try logging in with the correct pwd.
        self.create_unit_test_user_in_db()

        data = {
            "email": "unit_test@domain.com",
            "password": "super_secret_password"
        }

        response = self.tester.post('/login', json=data)
        val = '{"message":"Login successful"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        self.delete_unit_test_user_in_db()

    def test_base_not_signed_in(self):
        response = self.tester.get('/base')
        self.assertIn(str.encode("Welcome! Please login to continue."), response.data)

    def test_base_signed_in(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True

        response = self.tester.get('/base')
        self.assertIn(str.encode(sess['username']), response.data)

    def test_logout(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = sess['email'].split('@')[0]
            sess['is_admin'] = True

        self.tester.get('/logout')

        with self.tester.session_transaction() as sess:
            self.assertEqual(sess['signed_in'], False)
            self.assertEqual(sess['email'], "")
            self.assertEqual(sess['username'], "")

    def test_register_send_get_request(self):
        response = self.tester.get('/register')
        val = "Create your account. It's free and only takes a minute."
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_register_password_do_not_match(self):
        data = {
            "email": "unit_test@domain.com",
            "password": "1111",
            "confirmPassword": "1234"
        }

        response = self.tester.post('/register', json=data)
        val = '{"message":"Passwords do not match"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(400, response.status_code)

    def test_register_password_with_password_that_does_not_follow_the_requirements(self):
        data = {
            "email": "unit_test@domain.com",
            "password": "1111",
            "confirmPassword": "1111"
        }

        response = self.tester.post('/register', json=data)
        val = '{"message":"The password should be at least 8 characters long. The password may include uppercase letters: A-Z, lowercase letters: a-z, numbers: 0-9, any of the special characters: @#$%^&+=_"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(400, response.status_code)

    def test_register_email_already_exists(self):
        self.create_unit_test_user_in_db()

        data = {
            "email": "unit_test@domain.com",
            "password": "super_secret_password",
            "confirmPassword": "super_secret_password"
        }

        response = self.tester.post('/register', json=data)
        val = '{"message":"User already exists"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(400, response.status_code)

        self.delete_unit_test_user_in_db()

    def test_register_with_new_email(self):
        self.delete_unit_test_user_in_db()
        data = {
            "email": "unit_test@domain.com",
            "password": "super_secret_password",
            "confirmPassword": "super_secret_password",
            "is_admin": True
        }

        response = self.tester.post('/register', json=data)
        val = '{"message":"User registered successfully"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(201, response.status_code)

        with self.tester.session_transaction() as sess:
            self.assertEqual(sess['signed_in'], True)
            self.assertEqual(sess['email'], "unit_test@domain.com")

        self.get_user_id_from_db('unit_test@domain.com')

        self.delete_notifications_using_user_id()
        self.delete_unit_test_user_in_db()

    def test_forgot_send_get_request(self):
        response = self.tester.get('/forgot')
        val = 'Forgot Password'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_forgot_send_post_request_with_existing_user(self):
        self.create_unit_test_user_in_db()

        data = {
            "email": "unit_test@domain.com",
        }

        response = self.tester.post('/forgot', json=data)
        val = '{"message":"Password reset link sent to your email"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        self.delete_unit_test_user_in_db()

    def test_forgot_send_post_request_with_non_existing_user(self):
        self.delete_unit_test_user_in_db()

        data = {
            "email": "unit_test@domain.com",
        }

        response = self.tester.post('/forgot', json=data)
        val = '{"message":"Email not found"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(404, response.status_code)

    def test_reset_send_get_request(self):
        response = self.tester.get('/reset')
        self.assertIn(str.encode('Reset Password'), response.data)
        self.assertEqual(200, response.status_code)

    def test_reset_password_with_password_that_does_not_follow_the_requirements(self):
        data = {
            "email": "unit_test@domain.com",
            "newPassword": "1111",
            "confirmNewPassword": "1111"
        }

        response = self.tester.post('/reset', json=data)
        val = '{"message":"The password should be at least 8 characters long. The password may include uppercase letters: A-Z, lowercase letters: a-z, numbers: 0-9, any of the special characters: @#$%^&+=_"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(400, response.status_code)

    def test_reset_send_post_request_with_matching_password_and_existing_email(self):
        self.create_unit_test_user_in_db()
        new_password = "new_super_secret_password"
        data = {
            "email": "unit_test@domain.com",
            "newPassword": new_password,
            "confirmNewPassword": new_password

        }
        response = self.tester.post('/reset', json=data)
        val = '{"message":"Password reset successfully"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

        # check if the new pwd has been set in the db or not.
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        cursor.execute(f"SELECT password FROM usercredentials"
                       f" WHERE id='{self.user_id}';")
        password_from_db = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        self.assertTrue(bcrypt.checkpw(new_password.encode('utf-8'), password_from_db.encode('utf-8')))

        self.delete_unit_test_user_in_db()

    def test_reset_send_post_request_with_non_matching_password_and_existing_email(self):
        self.create_unit_test_user_in_db()

        data = {
            "email": "unit_test@domain",
            "newPassword": "super_secret_password",
            "confirmNewPassword": "super_secret_password_2"

        }
        response = self.tester.post('/reset', json=data)
        val = '{"message":"Passwords do not match"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(400, response.status_code)

        self.delete_unit_test_user_in_db()

    def test_reset_send_post_request_with_matching_password_and_non_existing_email(self):
        data = {
            "email": "unit_test@gmail.com",
            "newPassword": "super_secret_password",
            "confirmNewPassword": "super_secret_password"

        }
        response = self.tester.post('/reset', json=data)
        val = '{"message":"Email not found"}\n'
        self.assertEqual(str.encode(val), response.data)
        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
