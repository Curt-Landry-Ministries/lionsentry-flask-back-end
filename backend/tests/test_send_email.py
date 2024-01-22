import pytest
from server_utils import TestAuthServerBase
from backend.email_server.email_server import app as email_server
import json
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
import time
import requests

class TestEmailScheduling(TestAuthServerBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup for Email Server
        cls.email_app = email_server.test_client()
        load_dotenv()

    def test_schedule_emails_happy_path(self):

        # try creating the dev user. If it exists, log into it
        try:
            user_id, token = self.login_user("dev@lionsentry.com", "password123")
            print("logged in with id: ", user_id)
        except:
            print("dev user does not exist. Creating it now.")
            user_id, email, token = self.create_and_login_user("dev@lionsentry.com", "password123")
            print("created dev user with id: ", user_id)

        
        # Add email to the queue in Firestore
        now = datetime.now(pytz.timezone('America/Los_Angeles'))
        send_at = (now + timedelta(minutes=1)).isoformat()
        content = f"This is a test email. Written at: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}. " \
          f"Should be received by: {send_at}. Time zone: America/Los_Angeles."

        email_doc_ref = self.db.collection('emailQueue').add({
            'recipient': user_id,
            'subject': 'Test Email From test_send_email.py',
            'content': content,
            'sendAt': send_at,
            'status': 'written'
        })[1]

        print("added doc to email queue")

        # Schedule the email using the Email Server
        response = self.email_app.post('/schedule-emails', headers={'EMAIL-SERVER-API-KEY': os.getenv('EMAIL_SERVER_API_KEY')})
        assert response.status_code == 200

        # Wait and poll for the status update in Firestore
        timeout = 60  # seconds
        start_time = time.time()
        while time.time() - start_time < timeout:
            updated_email_doc = email_doc_ref.get().to_dict()
            if updated_email_doc['status'] == 'sentToSendGrid':
                break
            time.sleep(5)  # wait for 5 seconds before the next poll

        assert updated_email_doc['status'] == 'sentToSendGrid', "Email status not updated to 'sentToSendGrid' within timeout period"



# Additional tests to be written:
"""
- Test scheduling emails with invalid API key
- Test scheduling emails with no API key
- Test response of SendGrid webhook endpoint with different scenarios
- Test edge cases like scheduling emails for invalid time or non-existent users
"""

