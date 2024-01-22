import json
import os
import pytest
from server_utils import TestAuthServerBase, TestAppServerBase

class TestSubmitAnswerEndpoint:
    @classmethod
    def setup_class(cls):
        cls.test_auth_server = TestAuthServerBase()
        cls.test_auth_server.create_app()
        cls.test_auth_server.setUp()
        cls.test_app_server = TestAppServerBase()
        cls.test_app_server.create_app()
        cls.test_app_server.setUp()
        cls.test_user_id, cls.test_user_token = cls.test_auth_server.create_and_authenticate_user()

    def test_submit_and_get_answers(self):
        # Fetch questions to set the context for answers
        response = self.test_app_server.client.get('/get-questions')
        assert response.status_code == 200

        test_data_path = os.path.join(os.path.dirname(__file__), 'res', 'onboarding_responses.json')        
        with open(test_data_path, 'r') as file:
            test_data = json.load(file)["Deborah's Responses"]

        # Submit each answer and verify it saves correctly
        for i, qa in enumerate(test_data):
            question = qa['question']
            answer = qa['answer']
            response = self.test_app_server.client.post('/submit-onboarding-answer', headers={'Authorization':self.test_user_token}, json={
                'answer': answer,
                'question': question,
                'questionIndex': i
            })
            assert response.status_code == 200, f"Failed to submit answer for question {i}"

        # Submit a second, different answer for the first question
        second_answer = "This is a second test answer."
        response = self.test_app_server.client.post('/submit-onboarding-answer', headers={'Authorization': self.test_user_token}, json={
            'answer': second_answer,
            'question': test_data[0]['question'],
            'questionIndex': 0
        })
        assert response.status_code == 200, "Failed to submit second answer for the first question"

        # Fetch all answers and verify they are saved correctly
        response = self.test_app_server.client.get('/get-all-answers', headers={'Authorization': self.test_user_token})
        assert response.status_code == 200, "Failed to fetch all answers"

        all_answers = json.loads(response.data)
        assert isinstance(all_answers, list), "Retrieved answers should be in a list"
        assert len(all_answers) > 0, "Should retrieve at least one answer set"

        # Verify that the second answer appears in the retrieved data for the first question
        first_question_answers = [answer_set for answer_set in all_answers if answer_set['question'] == test_data[0]['question']]
        assert any(second_answer == answer['answer'] for answer_set in first_question_answers for answer in answer_set['answers']), "Second answer not found in the answers"

    @classmethod
    def teardown_class(cls):
        cls.test_auth_server.delete_user(cls.test_user_id, cls.test_user_token)
        cls.test_auth_server.tearDown()
        cls.test_app_server.tearDown()
