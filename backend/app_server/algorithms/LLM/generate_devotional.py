import json
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

CHATGPT_ROLE = "You are a non-denominational Christian pastor who wants to help people use the Bible to guide their life. Write in a modern, inspiring, upbeat and positive tone without being too over-the-top."

BIBLE_PASSAGE_PROMPT = (
    "Generate a passage from the bible, minimum 100 words, that is relevant to the user. User info: {user_info_formatted}. "
    "Here's an example: Come to me, all you who are weary and burdened, and I will give you rest. Take my yoke upon you and learn from me, for I am gentle and humble in heart, and you will find rest for your souls. For my yoke is easy and my burden is light.\"−Matthew 11:28-30 (NIV)"
)

PERSONALIZATION_PROMPT = (
    "The Bible passage generated is: '{bible_passage}'. Based on this bible passage and the reader info, generate a paragraph personalization about how this applies to the reader. {user_info}. "
    "Here's an example: The passage from Matthew 11:28-30 resonates deeply with your current circumstances. You're in a phase of life filled with challenges, both physical, due to your fractured heel, and emotional, given your professional and personal stresses. The burden of balancing a demanding role in a startup, managing finances, and the sheer frustration of being unable to pursue activities you love, such as rock climbing, can indeed feel overwhelming. Jesus' words, 'Come to me, all you who are weary and burdened, and I will give you rest,' is a beacon of hope and solace. It's an invitation to lay down the weights of our worries, frustrations, and pains, seeking comfort in Him. Living in your custom-built RV with your best friend suggests a desire for escape, exploration, and perhaps a break from the daily grind. Similarly, this scripture offers a spiritual escape, a retreat, where you can find peace and rest for your soul. The promise that His 'yoke is easy and burden is light' serves as a reminder that turning to faith can provide strength and resilience during challenging times. It's a call to trust, lean on faith, and find rejuvenation amidst life's storms."
)

JOURNALING_PROMPT = (
    "The bible passage being used is: '{bible_passage}'. Here is how it's relevant to the user: '{personalization}'. Based on the bible passage, personalization, and reader info, generate a journaling prompt. User info: {user_info_formatted}. "
    "Here's an example: Reflecting on the verse from Matthew, in what ways can you actively seek and embrace the rest and comfort Jesus offers during this period of immobility? How can this time become an opportunity to deepen your spiritual connection and discover new dimensions of joy and contentment in your life?"
)

DEVOTIONAL_TITLE_PROMPT = (
    "The journaling prompt provided is: '{journaling}'. Based on the bible passage: '{bible_passage}' and its personalization to the user, generate a title that sums up the devotional. User info: {user_info_formatted}. "
    "Here's an example: Embracing Rest in Life's Unexpected Halts"
)


def format_user_info(user_info):
    return json.dumps(user_info).replace('"', '\"')

def generate_prompt(role, content):
    return {"role": role, "content": content}

def chatgpt_request(model, messages):
    return openai.ChatCompletion.create(model=model, messages=messages)['choices'][0]['message']['content']

def generate_bible_passage(user_info_formatted):
    content = BIBLE_PASSAGE_PROMPT.format(user_info_formatted=user_info_formatted)
    prompt = generate_prompt("user", content)
    return chatgpt_request("gpt-4", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_personalization(bible_passage, user_info):
    content = PERSONALIZATION_PROMPT.format(bible_passage=bible_passage, user_info=user_info)
    prompt = generate_prompt("user", content)
    return chatgpt_request("gpt-4", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_journaling_prompt(bible_passage, personalization, user_info_formatted):
    content = JOURNALING_PROMPT.format(bible_passage=bible_passage, personalization=personalization, user_info_formatted=user_info_formatted)
    prompt = generate_prompt("user", content)
    return chatgpt_request("gpt-4", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_devotional_title(bible_passage, personalization, journaling, user_info_formatted):
    content = DEVOTIONAL_TITLE_PROMPT.format(journaling=journaling, bible_passage=bible_passage, user_info_formatted=user_info_formatted)
    prompt = generate_prompt("user", content)
    return chatgpt_request("gpt-4", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

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
