import pytest
from server_utils import TestAuthServerBase
from backend.email_server.email_server import app as email_server
import json
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

    def test_send_emails_for_testing(self):
        # Verify the environment variables
        email_server_api_key = os.getenv('EMAIL_SERVER_API_KEY')
        assert email_server_api_key is not None, "EMAIL_SERVER_API_KEY not set"
        
        # Generate daily devotionals for testing
        response = self.email_app.post(
            '/generate-daily-devotionals-for-all-users',
            headers={'EMAIL-SERVER-API-KEY': email_server_api_key},
            json={'for_testing': True}
        )
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
        
        # Schedule the emails
        response = self.email_app.post(
            '/schedule-emails',
            headers={'EMAIL-SERVER-API-KEY': email_server_api_key}
        )
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
        
        # Verify emails have been scheduled
        emails = self.db.collection('emailQueue').where('status', '==', 'sentToSendGrid').stream()
        email_count = sum(1 for _ in emails)
        assert email_count == 1, f"Expected 1 email to be scheduled, but found {email_count}"
