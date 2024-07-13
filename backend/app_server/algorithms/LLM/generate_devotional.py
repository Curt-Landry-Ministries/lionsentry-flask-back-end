import json
import openai
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

CHATGPT_ROLE = "You are a consensual extension of Rabbi Curt Landry, guiding people using the Bible. Write in a modern, inspiring, upbeat tone."

BASE_PROMPT_SUFFIX = "Provide only the requested information. Your response will be used in an application expecting just the requested content. No filler, greetings, or sign-offs. Do not output as 'title: x'. Just output the content."

BIBLE_PASSAGE_PROMPT = (
    "Select and output a Bible passage relevant to the user. Only select one pasasge. User info: {user_info_formatted}. "
    "Example: 'The Lord is my shepherd; I shall not want. He makes me lie down in green pastures. He leads me beside still waters. He restores my soul.' − Psalm 23:1-3 (NIV). " + BASE_PROMPT_SUFFIX
)

PERSONALIZATION_PROMPT = (
    "Bible passage: '{bible_passage}'. Based on this and the user info, write a paragraph in 100 tokens or less applying it to the user. {user_info}. "
    "Example: This passage from Psalm 23 brings comfort in uncertainty. It reminds you that God provides peace and restoration even in your busiest days. " + BASE_PROMPT_SUFFIX
)

JOURNALING_PROMPT = (
    "Bible passage: '{bible_passage}'. Relevance: '{personalization}'. Based on these and the user info, generate a one-sentence journaling prompt. {user_info_formatted}. "
    "Example: Reflect on Psalm 23 and write about recent moments of peace provided by God. " + BASE_PROMPT_SUFFIX
)

DEVOTIONAL_TITLE_PROMPT = (
    "Journaling prompt: '{journaling}'. Based on the Bible passage: '{bible_passage}' and its personalization, generate a devotional title. {user_info_formatted}. "
    "Example: God's Peace in Times of Change. " + BASE_PROMPT_SUFFIX
)

def format_user_info(user_info):
    return json.dumps(user_info, default=str).replace('"', '\"')

def chatgpt_request(model, messages):
    response = openai.ChatCompletion.create(model=model, messages=messages)
    return response['choices'][0]['message']['content']

def generate_bible_passage(user_info_formatted):
    content = BIBLE_PASSAGE_PROMPT.format(user_info_formatted=user_info_formatted)
    prompt = {"role": "user", "content": content}
    return chatgpt_request("gpt-4o", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_personalization(bible_passage, user_info):
    content = PERSONALIZATION_PROMPT.format(bible_passage=bible_passage, user_info=user_info)
    prompt = {"role": "user", "content": content}
    return chatgpt_request("gpt-4o", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_journaling_prompt(bible_passage, personalization, user_info_formatted):
    content = JOURNALING_PROMPT.format(bible_passage=bible_passage, personalization=personalization, user_info_formatted=user_info_formatted)
    prompt = {"role": "user", "content": content}
    return chatgpt_request("gpt-4o", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_devotional_title(bible_passage, personalization, journaling, user_info_formatted):
    content = DEVOTIONAL_TITLE_PROMPT.format(journaling=journaling, bible_passage=bible_passage, user_info_formatted=user_info_formatted)
    prompt = {"role": "user", "content": content}
    return chatgpt_request("gpt-4o", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_devotional_content(user_info):
    user_info_formatted = format_user_info(user_info)
    
    bible_passage = generate_bible_passage(user_info_formatted)
    personalization = generate_personalization(bible_passage, user_info)
    journaling = generate_journaling_prompt(bible_passage, personalization, user_info_formatted)
    title = generate_devotional_title(bible_passage, personalization, journaling, user_info_formatted)
    
    return {
        "Title": title.strip(),
        "BiblePassage": bible_passage.strip(),
        "Personalization": personalization.strip(),
        "JournalingPrompt": journaling.strip()
    }