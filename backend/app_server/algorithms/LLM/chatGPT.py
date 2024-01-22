import openai
import os
from dotenv import load_dotenv
from backend.app_server.algorithms.LLM.generate_devotional import base_prompts, example_outputs, user_info, DevotionalPrompt

"""

The idea here is to have one static chatGPT class that can be used everywhere we want to generate a chat response. 
This way, once we start introducing validators, tree of thought (ToT), etc., we can just add them to this class and they're reusable
"""
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class ChatGPT:
    @staticmethod
    def generate_devotional():
        # Generate the prompts with example data
        prompts = []
        previous_outputs = []
        responses = {}  # Dictionary to hold the responses

        for title in base_prompts.keys():
            input_with_example = base_prompts[title] + "\n\n" + \
                "\n\n".join(previous_outputs) + "\n\n" + user_info

            prompts.append(
                DevotionalPrompt(
                    title=title,
                    input=base_prompts[title],
                    input_with_example=input_with_example,
                    example_output=example_outputs[title]
                )
            )

            previous_outputs.append(example_outputs[title])

        # Collect the values of each prompt
        for prompt in prompts:
            print("Working on prompt: " + prompt.title)
            messages = [
                {"role": "system", "content": "You are a Christian pastor who wants to help people use the Bible to guide their life."}]
            messages.append(
                {"role": "user", "content": prompt.input_with_example})
            messages.append(
                {"role": "assistant", "content": prompt.example_output})
            messages.append(
                {"role": "user", "content": prompt.input + user_info})
            chat = openai.ChatCompletion.create(
                model="gpt-4-1106-preview",
                messages=messages
            )
            # Store the response
            responses[prompt.title] = chat['choices'][0]['message']['content']

        # Format the output
        formatted_output = f"Title\n{responses['Devotional Title']}"
        formatted_output += f"\nDevotional\n{responses['Bible Passage']}"
        formatted_output += f"\nPersonalization\n{responses['Personalization']}"
        formatted_output += f"\nJournaling Prompt:\n{responses['Journaling Prompt']}"

        # Remove escape characters before double quotes
        formatted_output = formatted_output.replace('\\"', '"')

        return formatted_output
