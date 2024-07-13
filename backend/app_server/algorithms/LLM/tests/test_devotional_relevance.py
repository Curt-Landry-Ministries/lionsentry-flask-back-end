import json
from dotenv import load_dotenv
import openai
import os
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from backend.app_server.algorithms.LLM.generate_devotional import generate_devotional_content

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def test_devotional_relevance():
    # User information (from the test user)
    user_info = {
        "beliefs": "I believe in finding peace through spirituality.",
        "felt_alive": "During quiet moments of reflection.",
        "relationship_importance": "Trust and honesty."
    }

    # Generated devotional content based on user information
    generated_content = generate_devotional_content(user_info)

    # Example Bible passage for comparison
    example_bible_passage = "The Lord is my shepherd; I shall not want..."

    # Create and evaluate test cases for each component
    test_cases = [
        {
            "input": json.dumps(user_info),
            "actual_output": generated_content["BiblePassage"],
            "retrieval_context": [example_bible_passage],
            "description": "Bible Passage"
        },
        {
            "input": json.dumps(user_info),
            "actual_output": generated_content["Personalization"],
            "retrieval_context": [example_bible_passage],
            "description": "Personalization"
        },
        {
            "input": json.dumps(user_info),
            "actual_output": generated_content["JournalingPrompt"],
            "retrieval_context": [example_bible_passage],
            "description": "Journaling Prompt"
        },
        {
            "input": json.dumps(user_info),
            "actual_output": generated_content["Title"],
            "retrieval_context": [example_bible_passage],
            "description": "Devotional Title"
        }
    ]

    for case in test_cases:
        test_case = LLMTestCase(
            input=case["input"],
            actual_output=case["actual_output"],
            retrieval_context=case["retrieval_context"]
        )

        # Define the relevancy metric with a threshold of 0.5
        answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.5)

        # Run the test case with the specified metric
        try:
            assert_test(test_case, [answer_relevancy_metric])
            print(f"{case['description']} test passed")
        except AssertionError:
            print(f"{case['description']} test failed")

# Run the test
if __name__ == "__main__":
    test_devotional_relevance()