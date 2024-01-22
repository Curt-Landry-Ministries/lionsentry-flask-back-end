import unittest
import json
import requests
import os
import logging
import firebase_admin
from firebase_admin import credentials
from pathlib import Path
from flask_testing import TestCase
from backend.auth_server.auth_server import auth_app
from dotenv import load_dotenv

# This test is designed to test Firebase independent of the rest of the stack
class TestFirebaseIntegration(TestCase):
    def create_app(self):
        auth_app.config['TESTING'] = True
        return auth_app

    def setUp(self):
        super().setUp()
        load_dotenv()
        self.firebase_api_key = os.environ.get('FIREBASE_API_KEY')
        self.assertIsNotNone(self.firebase_api_key, "FIREBASE_API_KEY is not set in environment variables.")
        
        if not firebase_admin._apps:
            project_root = Path(__file__).resolve().parents[2]
            firebase_credentials_path = project_root / "backend/firebase/lionsentry-firebase-adminsdk.json"
            cred = credentials.Certificate(str(firebase_credentials_path))
            # firebase_admin.initialize_app(cred)
        
        self.test_email = "testAccount@lionsentry.com"  # Valid test account email
        self.test_password = "Password"  # Corresponding password

    def authenticate_test_user(self, email, password):
        if not self.firebase_api_key:
            logging.error("Firebase API Key is missing.")
            return None

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.firebase_api_key}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(url, json=payload)
        return response

    def test_firebase_api_key_presence(self):
        self.assertIsNotNone(self.firebase_api_key, "FIREBASE_API_KEY is not set in environment variables.")

    def test_token_generation(self):
        response = self.authenticate_test_user(self.test_email, self.test_password)
        self.assertEqual(response.status_code, 200, "Failed to generate token with valid credentials.")
        response_data = response.json()
        token = response_data.get("idToken")
        self.assertIsNotNone(token, "Token should not be None.")
        self.assertIsInstance(token, str, "Token should be a string.")
        self.assertTrue(len(token) > 0, "Token should not be empty.")

    def test_invalid_credentials(self):
        response = self.authenticate_test_user("invalid@example.com", "wrongpassword")
        self.assertNotEqual(response.status_code, 200, "Token should not be generated with invalid credentials.")

if __name__ == '__main__':
    unittest.main()
