import json
import os
from dotenv import load_dotenv
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

CHATGPT_ROLE = "You are a consensual extension of Rabbi Curt Landry, guiding people using the Bible. Write in a modern, inspiring, upbeat, and positive tone without being too over-the-top."
BASE_PROMPT_SUFFIX = "ONLY provide the asked-for information. Do not include any filler text, greetings, or sign-offs. Do not include any text that is not explicitly demanded by the prompt."

BIBLE_PASSAGE_PROMPT = (
    "Generate a passage from the bible, minimum 100 words, that is relevant to the user based on their writing. User info: {user_info_formatted}. "
    "Here's an example: 'The Lord is my shepherd; I shall not want. He makes me lie down in green pastures. He leads me beside still waters. He restores my soul.' − Psalm 23:1-3 (NIV). " + BASE_PROMPT_SUFFIX
)

PERSONALIZATION_PROMPT = (
    "The Bible passage generated is: '{bible_passage}'. Based on this bible passage and the reader info, generate a paragraph personalization about how this applies to the reader. {user_info}. Make sure to talk about how something in the user info ties into the passage, but do this in a way that seems and feels natural."
    "Here's an example: This passage from Psalm 23 brings comfort and reassurance in times of uncertainty. It reminds you that even in your busiest days, God provides peace and restoration. Your new role at work, while exciting, has been overwhelming. Trust that God is guiding you and offering you the rest you need. " + BASE_PROMPT_SUFFIX
)

JOURNALING_PROMPT = (
    "The bible passage being used is: '{bible_passage}'. Here is how it's relevant to the user: '{personalization}'. Based on the bible passage, personalization, and reader info, generate a journaling prompt. User info: {user_info_formatted}. "
    "Here's an example: Reflect on Psalm 23 and consider how God has provided moments of peace in your life recently. Write about a time when you felt overwhelmed and how you found comfort in your faith. " + BASE_PROMPT_SUFFIX
)

DEVOTIONAL_TITLE_PROMPT = (
    "The journaling prompt provided is: '{journaling}'. Based on the bible passage: '{bible_passage}' and its personalization to the user, generate a title that sums up the devotional. User info: {user_info_formatted}. "
    "Here's an example: God's Peace in Times of Change. " + BASE_PROMPT_SUFFIX
)

def format_user_info(user_info):
    formatted_user_info = {}
    for key, value in user_info.items():
        if isinstance(value, datetime):
            formatted_user_info[key] = value.isoformat()
        else:
            formatted_user_info[key] = value
    return json.dumps(formatted_user_info).replace('"', '\"')

llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4")

def generate_bible_passage(user_info_formatted):
    prompt = PromptTemplate(template=BIBLE_PASSAGE_PROMPT, input_variables=["user_info_formatted"])
    formatted_prompt = prompt.format(user_info_formatted=user_info_formatted)
    messages = [
        {"role": "system", "content": CHATGPT_ROLE},
        {"role": "user", "content": formatted_prompt}
    ]
    response = llm.invoke(messages)
    return response.content

def generate_personalization(bible_passage, user_info):
    prompt = PromptTemplate(template=PERSONALIZATION_PROMPT, input_variables=["bible_passage", "user_info"])
    formatted_prompt = prompt.format(bible_passage=bible_passage, user_info=user_info)
    messages = [
        {"role": "system", "content": CHATGPT_ROLE},
        {"role": "user", "content": formatted_prompt}
    ]
    response = llm.invoke(messages)
    return response.content

def generate_journaling_prompt(bible_passage, personalization, user_info_formatted):
    prompt = PromptTemplate(template=JOURNALING_PROMPT, input_variables=["bible_passage", "personalization", "user_info_formatted"])
    formatted_prompt = prompt.format(bible_passage=bible_passage, personalization=personalization, user_info_formatted=user_info_formatted)
    messages = [
        {"role": "system", "content": CHATGPT_ROLE},
        {"role": "user", "content": formatted_prompt}
    ]
    response = llm.invoke(messages)
    return response.content

def generate_devotional_title(bible_passage, personalization, journaling, user_info_formatted):
    prompt = PromptTemplate(template=DEVOTIONAL_TITLE_PROMPT, input_variables=["bible_passage", "personalization", "journaling", "user_info_formatted"])
    formatted_prompt = prompt.format(bible_passage=bible_passage, personalization=personalization, journaling=journaling, user_info_formatted=user_info_formatted)
    messages = [
        {"role": "system", "content": CHATGPT_ROLE},
        {"role": "user", "content": formatted_prompt}
    ]
    response = llm.invoke(messages)
    return response.content

def generate_devotional_content(user_info):
    user_info_formatted = format_user_info(user_info)
    
    bible_passage = generate_bible_passage(user_info_formatted)
    personalization = generate_personalization(bible_passage, user_info)
    journaling = generate_journaling_prompt(bible_passage, personalization, user_info_formatted)
    title = generate_devotional_title(bible_passage, personalization, journaling, user_info_formatted)
    
    devotional_content = {
        "Title": title.strip(),
        "BiblePassage": bible_passage.strip(),
        "Personalization": personalization.strip(),
        "JournalingPrompt": journaling.strip()
    }

    return devotional_content

# Example usage
if __name__ == "__main__":
    user_info = {
        "beliefs": "I believe in finding peace through spirituality.",
        "felt_alive": "During quiet moments of reflection.",
        "relationship_importance": "Trust and honesty."
    }
    result = generate_devotional_content(user_info)
    print(result)