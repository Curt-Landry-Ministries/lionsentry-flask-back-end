import unittest
import json
import string
import requests
import os
import random
import firebase_admin
import logging
from firebase_admin import credentials, auth, firestore
from pathlib import Path
from flask_testing import TestCase
from backend.auth_server.auth_server import auth_app
from backend.app_server.app_server import app as app_app

from dotenv import load_dotenv

# Adhering to DRY, we can create a base class that contains all of the common functionality that we want to use in our tests for our App and Auth servers

class TestAuthServerBase(TestCase):
    def create_app(self):
        auth_app.config['TESTING'] = True
        load_dotenv()
        return auth_app

    def setUp(self):
        # Load environment variables and initialize Firebase
        if not firebase_admin._apps:
            project_root = Path(__file__).resolve().parents[2]
            firebase_credentials_path = project_root / "backend/firebase/lionsentry-firebase-adminsdk.json"
            cred = credentials.Certificate(str(firebase_credentials_path))
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.client = auth_app.test_client()

    def create_user_manually(self, email, password):
        response = self.client.post('/create-user-manually', data=json.dumps({
            'email': email, 'password': password
        }), content_type='application/json')
        return response

    def create_and_login_user(self, email=None, password=None):
        # if there's an email and password, use that. Otherwise use a random email and password
        if not email and not password:
            email = self.generate_random_email()
            password = "testpassword"

        response = self.client.post('/create-user-manually', data=json.dumps({
            'email': email, 'password': password
        }), content_type='application/json')

        if response.status_code == 200:
            data = json.loads(response.data.decode())
            user_id = data.get('uid')
            id_token = self.get_id_token(email, password)  # Fetch ID token for the created user
            return user_id, email, id_token
        else:
            return None, None, None
        
    def login_user(self, email, password):
        # Making a POST request to the /login-user endpoint of the Flask application
        response = self.client.post('/login-user', data=json.dumps({
            'email': email, 'password': password
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
    
    def create_and_authenticate_user(self):
        # Generate a random email and password
        email = self.generate_random_email()
        password = "testpassword"
        
        # Create user
        self.create_user_manually(email, password)

        # Authenticate user and get token
        id_token = self.authenticate_test_user(email, password)
        if id_token:
            # Fetch user ID using Firebase Admin SDK
            user_id = auth.get_user_by_email(email).uid
            return user_id, 'Bearer ' + id_token
        else:
            return None, None
    
    def authenticate_test_user(self, email, password):
        try:
            response = self.client.post('/get-id-token', data=json.dumps({
                'email': email,
                'password': password
            }), content_type='application/json')

            if response.status_code == 200:
                response_data = json.loads(response.data)
                return response_data.get("idToken")
            else:
                logging.error(f"Failed to authenticate user with email {email}: {response.text}")
                return None
        except Exception as e:
            logging.error(f"Exception during authentication: {str(e)}")
            return None

    def generate_random_email(self):
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f'testuser{random_part}@example.com'

    def create_user_with_credentials(self, email, password):
        response = self.client.post('/create-user-manually', data=json.dumps({
            'email': email, 'password': password
        }), content_type='application/json')
        return json.loads(response.data.decode())

    def get_id_token(self, email, password):
        response = self.client.post('/get-id-token', data=json.dumps({
            'email': email, 'password': password
        }), content_type='application/json')
        return json.loads(response.data.decode()).get('idToken')

    def delete_user(self, user_id, id_token):
        try:
            # Log the request details for deletion
            logging.info(f"Attempting to delete user with ID: {user_id}")

            # Send the deletion request to the server
            response = self.client.post('/delete-user', data=json.dumps({
                'userID': user_id, 'idToken': id_token
            }), content_type='application/json')

            # Log the response status and data
            logging.info(f"Response status code for user deletion: {response.status_code}")
            logging.info(f"Response data: {response.data}")

            # Check if the deletion was successful
            if response.status_code == 200:
                logging.info("User deleted successfully.")
                return True
            else:
                logging.error(f"Failed to delete user. Status code: {response.status_code}")
                return False

        except Exception as e:
            # Log any exceptions that occur during the process
            logging.error(f"Exception occurred while deleting user: {e}")
            return False

class TestAppServerBase(TestCase):
    def create_app(self):
        # Load environment variables
        load_dotenv()

        # Configure the Flask app for testing
        app_app.config['TESTING'] = True

        # Assign the Flask app instance to self.app
        self.app = app_app

        return self.app

    def setUp(self):
        self.firebase_api_key = os.environ.get('FIREBASE_API_KEY')

        if not self.firebase_api_key:
            self.fail("FIREBASE_API_KEY not set in environment variables.")

        if not firebase_admin._apps:
            project_root = Path(__file__).resolve().parents[2]
            firebase_credentials_path = project_root / "backend/firebase/lionsentry-firebase-adminsdk.json"
            cred = credentials.Certificate(str(firebase_credentials_path))
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

        # Now self.app is set, so we can create the test client
        self.client = self.app.test_client()

    def authenticate_test_user(self, email, password):
        if not self.firebase_api_key:
            logging.error("Firebase API Key is missing.")
            return None

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.firebase_api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get("idToken")
        else:
            logging.error(f"Failed to authenticate user: Status Code: {response.status_code}, Response: {response.text}")
            return None

