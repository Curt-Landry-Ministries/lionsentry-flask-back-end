import unittest
import json
from datetime import datetime
import logging
from server_utils import TestAuthServerBase, TestAppServerBase

logging.basicConfig(level=logging.DEBUG)

class TestSaveUserDataPoint(unittest.TestCase):
    def setUp(self):
        # Initialize TestAuthServer and TestAppServer
        self.test_auth_server = TestAuthServerBase()
        self.test_auth_server.create_app()
        self.test_auth_server.setUp()

        self.test_app_server = TestAppServerBase()
        self.test_app_server.create_app()
        self.test_app_server.setUp()

        # Create and authenticate a test user
        self.test_user_id, self.test_user_token = self.test_auth_server.create_and_authenticate_user()

    def send_data_point_request(self, key, value, action='replace'):
        logging.debug(f"Sending request to /save-user-data-point for {self.test_user_id} with data: {key}, {value}")
        response = self.test_app_server.client.post(
            '/save-user-data-point',
            headers={'Authorization': self.test_user_token},
            data=json.dumps({
                'targetUserId': self.test_user_id,
                'dataPoint': key,
                'action': action,
                'value': value
            }),
            content_type='application/json'
        )
        logging.debug(f"Received response: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, 200)

    def test_save_user_datapoint(self):
        sample_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'birthday': datetime.utcnow().isoformat(),
            'sex': 'Male',
            'referredBy': 'Friend',
            'preferredBibleVersion': 'KJV',
            'isDeleted': False,
            'timeZone': 'GMT'
        }

        if self.test_user_token:
            for key, value in sample_data.items():
                self.send_data_point_request(key, value)

            # Modify a data point
            self.send_data_point_request('firstName', 'Jason')

            # Verify all data changes
            user_ref = self.test_auth_server.db.collection('users').document(self.test_user_id)
            user_doc = user_ref.get().to_dict()

            expected_data = sample_data.copy()
            expected_data['firstName'] = 'Jason'

            for key, value in expected_data.items():
                self.assertEqual(user_doc[key], value)
        else:
            logging.error("Test skipped due to failed user authentication.")
            self.skipTest("User authentication failed.")

        # Cleanup
        print("Cleanup: Deleting the test user")
        self.assertTrue(self.test_auth_server.delete_user(self.test_user_id, self.test_user_token.split(' ')[1])), "Failed to delete user"

if __name__ == '__main__':
    unittest.main()
