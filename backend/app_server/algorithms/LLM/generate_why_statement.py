import os
import json
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Construct the path relative to the current file
current_dir = os.path.dirname(__file__)
prompts_path = os.path.join(current_dir, '..', 'util', 'prompts.json')

# Load prompts data from JSON file
with open(prompts_path, 'r') as file:
    prompts_data = json.load(file)

chatgpt_role = prompts_data["chatgpt_role"]
base_prompts = prompts_data["base_prompts"]

def format_user_data(questions_answers):
    formatted_data = ""
    for qa in questions_answers:
        formatted_data += f"Question: {qa['question']}\nAnswer: {qa['answer']}\n\n"
    return formatted_data

def generate_why_statement(questions_answers):
    user_data = format_user_data(questions_answers)
    prompt = base_prompts["Why Statement"] + "\n\n" + user_data

    # Initialize the LLM with the OpenAI key
    llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4")

    # Create the PromptTemplate
    why_statement_template = PromptTemplate(
        template="{chatgpt_role}\n{prompt}",
        input_variables=["chatgpt_role", "prompt"]
    )

    # Generate the why statement
    formatted_prompt = why_statement_template.format(chatgpt_role=chatgpt_role, prompt=prompt)
    messages = [
        {"role": "system", "content": chatgpt_role},
        {"role": "user", "content": formatted_prompt}
    ]
    why_statement = llm.invoke(messages).content

    return {"whyStatement": why_statement}

# Example usage
if __name__ == "__main__":
    questions_answers = [
        {"question": "What do you believe about the world?", "answer": "I believe the world is full of opportunities."},
        {"question": "When have you felt most alive?", "answer": "During my travels and when learning new cultures."},
        {"question": "What's most important in your relationships?", "answer": "Trust and mutual respect."}
    ]
    result = generate_why_statement(questions_answers)
    print(result)