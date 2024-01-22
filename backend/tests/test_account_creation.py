import unittest
import argparse
from server_utils import TestAuthServerBase

parser = argparse.ArgumentParser(description='Run tests for auth server')
parser.add_argument('-m', '--manual', action='store_true', help='Run in manual mode without cleanup')
args, unknown = parser.parse_known_args()

class TestCreateUserManually(unittest.TestCase):
    def setUp(self):
        self.test_auth_server = TestAuthServerBase()
        self.test_auth_server.create_app()
        self.test_auth_server.setUp()

    def test_create_user_manually(self):
        # Create and login user
        user_id, email, id_token = self.test_auth_server.create_and_login_user()
        self.assertIsNotNone(user_id, "User creation failed")
        self.assertIsNotNone(email, "Email generation failed")
        self.assertIsNotNone(id_token, "User authentication failed")

        if not args.manual:
            # Use the delete-user method from TestAuthServer
            # Corrected to use local variables `user_id` and `id_token`
            self.assertTrue(self.test_auth_server.delete_user(user_id, id_token), "Failed to delete user")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
