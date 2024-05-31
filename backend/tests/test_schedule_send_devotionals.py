import pytest
from server_utils import TestAuthServerBase
from backend.email_server.email_server import app as email_server
import json
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv

class TestEmailForAllUsers(TestAuthServerBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup for Email Server
        cls.email_app = email_server.test_client()
        load_dotenv()

    def setUp(self):
        super().setUp()
        # Clean up email queue before each test
        email_queue_docs = self.db.collection('emailQueue').stream()
        for doc in email_queue_docs:
            doc.reference.delete()

    def test_send_emails_to_all_users(self):
        # Verify the environment variables
        email_server_api_key = os.getenv('EMAIL_SERVER_API_KEY')
        app_server_api_key = os.getenv('APP_SERVER_API_KEY')
        assert email_server_api_key is not None, "EMAIL_SERVER_API_KEY not set"
        assert app_server_api_key is not None, "APP_SERVER_API_KEY not set"
        
        print(f"EMAIL_SERVER_API_KEY: {email_server_api_key}")
        print(f"APP_SERVER_API_KEY: {app_server_api_key}")
        
        # Login user using the Auth server
        user_id, token = self.login_user("dev@lionsentry.com", "Password")
        assert user_id is not None, "User ID not returned"
        assert token is not None, "Token not returned"
        
        print("Generated user_id and token:", user_id, token)
        
        response = self.email_app.post(
            '/generate-daily-devotionals-for-all-users',
            headers={
                'EMAIL-SERVER-API-KEY': email_server_api_key,
                'Authorization': f'Bearer {token}'
            }
        )
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Data: {response.data}")
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
        print("Emails created for all users")
        
        # Schedule the emails
        response = self.email_app.post(
            '/schedule-emails',
            headers={'EMAIL-SERVER-API-KEY': email_server_api_key}
        )
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Data: {response.data}")
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
        print("Emails scheduled")
        
        # Verify emails have been scheduled
        emails = self.db.collection('emailQueue').where('status', '==', 'sentToSendGrid').stream()
        email_count = sum(1 for _ in emails)
        users = self.db.collection('users').stream()
        user_count = sum(1 for _ in users)
        
        assert email_count == user_count, f"Expected {user_count} emails to be scheduled, but found {email_count}"
        print(f"Successfully scheduled {email_count} emails for {user_count} users")

    def login_user(self, email, password):
        # Making a POST request to the /login-user endpoint of the Flask application
        response = self.client.post('/login-user', data=json.dumps({
            'email': email,
            'password': password
        }), content_type='application/json')

        # Check if the response is successful
        if response.status_code == 200:
            # Parse the JSON response
            data = json.loads(response.data.decode())
            # Extract user_id and id_token from the response
            user_id = data['user']['userID']
            id_token = data['idToken']
            return user_id, id_token
        else:
            return None, None
