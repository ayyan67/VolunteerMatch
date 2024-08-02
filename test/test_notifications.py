import unittest
import psycopg2
import bcrypt
from run import app

import sys

sys.path.append("../VolunteerMatch")


class NotificationsTest(unittest.TestCase):
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

    def test_notification_signed_in_false(self):
        with self.tester.session_transaction() as sess:
            sess['signed_in'] = False

        response = self.tester.get('/notifications/')
        val = 'Welcome! Please login to continue.'
        self.assertIn(str.encode(val), response.data)
        self.assertEqual(200, response.status_code)

    def test_notification_signed_in_true_for_admin(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = self.user_id
            sess['is_admin'] = True

        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        # push a fake notification to the db and check for its existence in the front end.
        command = f"INSERT INTO notifications (user_id, msg, notification_type) " \
                  f"VALUES ({self.user_id}, " \
                  f"'Test notification for automated unit testing with fake user {sess['email']}...', {True});"
        cursor.execute(command)
        conn.commit()

        response = self.tester.get('/notifications/')
        self.assertIn(str.encode(f"Test notification for automated unit testing with fake user {sess['email']}..."),
                      response.data)
        self.assertEqual(200, response.status_code)

        # delete the fake notif.
        command = (f"DELETE FROM notifications "
                   f"WHERE user_id = {self.user_id};")
        cursor.execute(command)
        conn.commit()

        self.delete_unit_test_user_in_db()

    def test_notification_signed_in_true_for_users(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = self.user_id
            sess['is_admin'] = False

        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        # push a fake notification to the db and check for its existence in the front end.
        command = f"INSERT INTO notifications (user_id, msg, notification_type) " \
                  f"VALUES ({self.user_id}, " \
                  f"'Test notification for automated unit testing with fake user {sess['email']}...', {False});"
        cursor.execute(command)
        conn.commit()

        response = self.tester.get('/notifications/')
        self.assertIn(str.encode(f"Test notification for automated unit testing with fake user {sess['email']}..."),
                      response.data)
        self.assertEqual(200, response.status_code)

        # delete the fake notif.
        command = (f"DELETE FROM notifications "
                   f"WHERE user_id = {self.user_id};")
        cursor.execute(command)
        conn.commit()

        self.delete_unit_test_user_in_db()

    def test_delete_a_notification_deletes_it_from_db(self):
        self.create_unit_test_user_in_db()

        with self.tester.session_transaction() as sess:
            sess['signed_in'] = True
            sess['email'] = 'unit_test@domain.com'
            sess['username'] = 'unit_test'
            sess['user_id'] = self.user_id
            sess['is_admin'] = True

        data = {
            'notification_name': '\n\nMy test notification!\n'
        }

        # insert the notification
        conn = psycopg2.connect(database="volunteers_db", user="postgres",
                                password="arti", host="localhost", port="5432")
        cursor = conn.cursor()

        command = f"INSERT INTO notifications (user_id, msg, notification_type) " \
                  f"VALUES ({self.user_id}, '{data['notification_name']}', {True});"
        cursor.execute(command)
        conn.commit()

        self.tester.post('/notifications/delete', json=data)

        # check if the notification has been deleted from the db
        command = f"SELECT * FROM notifications WHERE msg = '{data['notification_name']}';"
        cursor.execute(command)
        table_data = cursor.fetchone()
        self.assertIsNone(table_data)

        self.delete_unit_test_user_in_db()


if __name__ == "__main__":
    unittest.main()
