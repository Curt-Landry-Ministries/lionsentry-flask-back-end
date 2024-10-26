import json
import os
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CHATGPT_ROLE = "You are a consensual extension of Rabbi Curt Landry, coaching and guiding people into their purpose, calling, and life of impact, using the Bible. Emulate Curt Landry's authoritative yet compassionate tone."

# Define a function to read a file's content as a string
def read_file_content(file_path):
    with open(file_path, 'r') as file:
        return file.read()


# Path to the files with the context prompts
values_path = './inc/values.inc'
style_path = './inc/style.inc'

# Read content from the files
values_content = read_file_content(values_path)
style_content = read_file_content(style_path)

WHY_STATEMENT_PROMPT = f"""
<why_statement_prompt>
<instructions>
Based on the following responses to our purpose-finding questions in <question_answers>, craft a powerful and concise 'Why Statement' and 'Purpose Statement' that captures this person's core purpose and motivation. The statements should be clear, memorable, and inspiring, focusing on the impact they want to make and what drives them. Write it in the first person tense. Create a new why and purpose statement each time prompted, following the <format> and <rules>. Write this in line with context and values of <curt_landry_principles> and <ministry_values>. Use the <style_guide> and <book_reference> to inform the tone and approach.
</instructions>
<question_answers>
{{user_data}}
</question_answers>
<process>
Analyze the User's Answers Thoroughly
Read Carefully: Go through each of the user's responses to the provided questions in detail.
Identify Key Elements: Look for recurring themes, values, passions, strengths, beliefs, and significant experiences.
Use CoT Reasoning: Think step-by-step to connect the dots between different answers, drawing out deeper insights.
Identify Core Themes and Patterns
Summarize Insights: Create a concise summary of the main themes emerging from the user's answers.
Highlight Strengths and Passions: Note what the user naturally excels at and what makes them come alive.
Understand Beliefs and Values: Capture the user's core beliefs about the world and the causes they stand for.
Recognize Desired Impact: Determine the impact the user wants to make on the world or in others' lives.
Deduce the User's Core Purpose
Connect Strengths to Impact: Figure out how the user's strengths and passions can be used to achieve their desired impact.
Identify Unique Contribution: Determine the unique ways the user can contribute to the world based on their insights.
Articulate Motivations: Understand what drives the user, especially in overcoming challenges or pursuing aspirations without fear of failure.
</process>
<format>
  <why_statement>
    Using principles from Simon Sinek’s _Start With Why_ and _Find Your Why_, guide the user in crafting their most purposeful and impactful "Why" statement. Analyze the user's answers to the provided introspective questions and help them uncover key themes, values, strengths, and beliefs. Use these insights to generate a concise, personal "Why" statement that reflects the user's purpose and inspires them toward a life of impact. Use the format: "To [contribution], so that [impact]". 
Contribution: The actions or initiatives the user will undertake using their strengths and passions.
Impact: The meaningful change or difference the user aims to make in others' lives or the world.
Use the tag why_statement.
  </why_state>
  <purpose_statement>
    Based on the answers to the questions, deduction, and why statement, write a powerful, motivating, and detailed purpose statement for a life of impact. This statement will start with "I exist to..." and should speak to who they are becoming, as if it is already true, reflecting their core identity and desired impact on the world. Use the tag purpose_statement.
  </purpose_statement>
</format>
<rules>
  <rule>Don't include word counts in the output</rule>
  <rule>Provide only the requested information. Your response will be used in an application expecting just the requested content. No filler.</rule>
  <rule>Primarily source information and commentary from the given context and Curt Landry or Curt Landry Ministries</rule>
  <rule>Use teachings from similar teachers: John Kilpatrick, Michael Brown, Steve Hill, Paul Wilbur, Robert Henderson</rule>
  <rule>Also reference the following as context: Strong's concordance, Vine's expository Dictionary, Mounce Reverse Interlinear New Testament, Gems from the Greek Vol. 1 & 2, Baker's Evangelical Dictionary of Biblical Theology, Easton's Bible Dictionary, Hitchcock's Bible Names Dictionary, King James Dictionary, Smith's Bible Dictionary, Matthew Henry's Commentary, The Spirit-filled Life New Testament Commentary Series, The Pentecostal Old Testament and New Testament Commentaries, Baker Exegetical Commentary series, Pentecostal Commentary Series, Applied Commentary, Enduring Word Bible Commentary</rule>
</rules>
{values_content}
{style_content}
</why_statement_prompt>
"""

def format_user_data(questions_answers):
    formatted_data = ""
    for qa in questions_answers:
        formatted_data += f"Question: {qa['question']}\nAnswer: {qa['answer']}\n\n"
    return formatted_data

def generate_why_statement(questions_answers):
    # Format the user's answers into a readable string
    user_data = format_user_data(questions_answers)

    # Format the prompt with the user's data
    formatted_prompt = WHY_STATEMENT_PROMPT.format(user_data=user_data)
    # Generate the why statement using Anthropic
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system=CHATGPT_ROLE,
        messages=[{
            "role": "user",
            "content": [{
                "type": "text", 
                "text": formatted_prompt
            }]
        }]
    )
    return {
        "whyStatement": response.content[0].text
    }
    
# Example usage
if __name__ == "__main__":
    # Test data
    test_questions_answers = [
        {
            "question": "What makes you come alive?",
            "answer": "Test answer 1"
        },
        # ... add more test questions and answers as needed
    ]

    result = generate_why_statement(test_questions_answers)
    print(result)