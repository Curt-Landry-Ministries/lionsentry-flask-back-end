import os
from dotenv import load_dotenv
from backend.app_server.algorithms.LLM.generate_devotional import base_prompts, example_outputs, user_info, DevotionalPrompt
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

class ChatGPT:
    @staticmethod
    def generate_devotional():
        # Initialize the LLM with the OpenAI key
        llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4", temperature=0.7)

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
            
            # Create the ChatPromptTemplate
            messages = [
                {"role": "system", "content": "You are a Christian pastor who wants to help people use the Bible to guide their life."},
                {"role": "user", "content": prompt.input_with_example},
                {"role": "assistant", "content": prompt.example_output},
                {"role": "user", "content": prompt.input + user_info}
            ]

            # Generate the response using LangChain's LLM
            response = llm.invoke(messages).content
            
            responses[prompt.title] = response

        # Format the output
        formatted_output = f"Title\n{responses['Devotional Title']}"
        formatted_output += f"\nDevotional\n{responses['Bible Passage']}"
        formatted_output += f"\nPersonalization\n{responses['Personalization']}"
        formatted_output += f"\nJournaling Prompt:\n{responses['Journaling Prompt']}"

        # Remove escape characters before double quotes
        formatted_output = formatted_output.replace('\\"', '"')

        return formatted_output

# Example usage
if __name__ == "__main__":
    chatgpt = ChatGPT()
    result = chatgpt.generate_devotional()
    print(result)