import pytest
import json
import logging
from backend.tests.server_utils import TestAppServerBase, TestAuthServerBase
from google.cloud.firestore import Query

logging.basicConfig(level=logging.DEBUG)

class TestGenerateDevotional:
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

        self.setup_why_statement_for_user()

    def setup_why_statement_for_user(self):
        why_statement_content = "My precious, the one ring, it's all I need."
        # Setting a why statement instead of generating one because the generate endpoint is tested elsewhere
        self.test_app_server.db.collection('whyStatements').document(self.test_user_id).set({
            "whyStatement": why_statement_content,
            "forUser": self.test_user_id
        })

    def test_generate_devotional(self):
        assert self.test_user_id is not None, "User creation failed"
        assert self.test_user_token is not None, "Authentication failed"

        headers = {
            'Authorization': self.test_user_token,
            'Content-Type': 'application/json'
        }

        response = self.client.post('/generate-devotional', headers=headers)
        logging.debug(f"Response status code: {response.status_code}, Response data: {response.data}")
        response_data = json.loads(response.data.decode())

        assert response.status_code == 200, "POST request to generate devotional failed"

        # Verify devotional is stored in Firestore and check its values
        devotionals = self.test_app_server.db.collection('devotionals').where('forUser', '==', self.test_user_id).order_by('dateTimeCreated', direction=Query.DESCENDING).limit(1).get()
        assert len(devotionals) > 0, "Devotional not found in Firestore"

        stored_devotional = devotionals[0].to_dict()
        assert stored_devotional['forUser'] == self.test_user_id, "Stored devotional user ID mismatch"
        assert stored_devotional['title'] == response_data['Title'], "Stored devotional title mismatch"
        assert stored_devotional['biblePassage'] == response_data['BiblePassage'], "Stored devotional bible passage mismatch"
        assert stored_devotional['personalization'] == response_data['Personalization'], "Stored devotional personalization mismatch"
        assert stored_devotional['journalingPrompt'] == response_data['JournalingPrompt'], "Stored devotional journaling prompt mismatch"
        # Clean up: Delete the test user
        assert self.test_auth_server.delete_user(self.test_user_id, self.test_user_token.split(' ')[1]), "Failed to delete user"

if __name__ == "__main__":
    pytest.main()
