import openai
import os
import json
from dotenv import load_dotenv

# Generate a why statement for the user 

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Construct the path relative to the current file
current_dir = os.path.dirname(__file__)
prompts_path = os.path.join(current_dir, '..', 'util', 'prompts.json')

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

    messages = [{"role": "system", "content": chatgpt_role}]
    messages.append({"role": "user", "content": prompt})

    chat = openai.ChatCompletion.create(
        model="gpt-4-1106-preview", messages=messages)
    why_statement = chat['choices'][0]['message']['content']

    return {"whyStatement": why_statement}
