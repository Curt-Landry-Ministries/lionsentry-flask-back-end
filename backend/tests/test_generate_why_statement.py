import os
import pytest
import json
import logging
from backend.tests.server_utils import TestAppServerBase, TestAuthServerBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class TestGenerateWhyStatement:
    @pytest.fixture(autouse=True)
    def setup_class(self):
        self.test_auth_server = TestAuthServerBase()
        self.test_auth_server.create_app()
        self.test_auth_server.setUp()
        self.test_app_server = TestAppServerBase()
        self.test_app_server.create_app()
        self.test_app_server.setUp()

        self.client = self.test_app_server.client
        self.test_user_id, self.test_user_token = self.test_auth_server.create_and_authenticate_user()

    def test_generate_and_get_latest_why_statement(self):
        assert self.test_user_id is not None, "User creation failed"
        assert self.test_user_token is not None, "Authentication failed"

        headers = {
            'Authorization': self.test_user_token,
            'Content-Type': 'application/json'
        }

# Gollum's answer
        gollum_answer = "My precious, the one ring, it's all I need."
        question = "What drives you?"

        # Submit Gollum's answer
        response = self.client.post(
            '/submit-onboarding-answer',
            headers=headers,
            json={
                'question': question,
                'answer': gollum_answer,
                'questionIndex': 0  # Assuming questionIndex 0 for this example
            }
        )
        assert response.status_code == 200, "POST request to submit Gollum's answer failed"

        # Generate Why Statement
        response = self.client.post(
            '/generate-why-statement',
            headers=headers,
            json={'saveToFirestore': True}
        )
        assert response.status_code == 200, "POST request to generate why statement failed"
        gollum_why_statement_response = json.loads(response.data.decode())['whyStatement']

        # Get the latest Why Statement and assert it's Gollum's
        response = self.client.get('/get-latest-why-statement', headers=headers)
        assert response.status_code == 200, "GET request to retrieve latest why statement failed"
        latest_why_statement_data = json.loads(response.data.decode())
        assert 'whyStatement' in latest_why_statement_data, "Latest Why Statement was not returned in the response"
        assert latest_why_statement_data['whyStatement'] == gollum_why_statement_response, "The latest why statement does not match Gollum's generated statement"

        # Smeagol's answer
        smeagol_answer = "Finding peace and a new beginning away from the ring."

        # Update the answer to Smeagol's using submit-onboarding-answer endpoint
        response = self.client.post(
            '/submit-onboarding-answer',
            headers=headers,
            json={
                'question': question,
                'answer': smeagol_answer,
                'questionIndex': 0  # Same question index as before
            }
        )
        assert response.status_code == 200, "POST request to submit Smeagol's answer failed"

        # Generate a new Why Statement for Smeagol
        response = self.client.post(
            '/generate-why-statement',
            headers=headers,
            json={'saveToFirestore': True}
        )
        assert response.status_code == 200, "POST request to generate Smeagol's why statement failed"
        smeagol_why_statement_response = json.loads(response.data.decode())['whyStatement']

        # Get the latest Why Statement and assert it's the same as Smeagol's response
        response = self.client.get('/get-latest-why-statement', headers=headers)
        assert response.status_code == 200, "GET request to retrieve latest why statement failed"
        latest_why_statement_data = json.loads(response.data.decode())
        assert 'whyStatement' in latest_why_statement_data, "Latest Why Statement was not returned in the response"
        assert latest_why_statement_data['whyStatement'] == smeagol_why_statement_response, "The latest why statement does not match Smeagol's generated statement"

        # Clean up: Delete the test user
        assert self.test_auth_server.delete_user(self.test_user_id, self.test_user_token.split(' ')[1]), "Failed to delete user"