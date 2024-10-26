import json
import os
import random
from dotenv import load_dotenv
from datetime import datetime
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CHATGPT_ROLE = "You are a consensual extension of Rabbi Curt Landry, coaching and guiding people into their purpose, calling, and life of impact, using the Bible. Emulate Curt Landry's authoritative yet compassionate tone."

# Define the themes for each day of the week
themes = {
    "Monday":
    "Today’s focus is on aligning your life with God’s covenant. Reflect on areas where you may need to realign your actions and decisions with God’s promises. How can you stand in faith and act in a way that honors the covenant God has made with you? Seek His wisdom, especially in how you support Israel and His Kingdom work.",
    "Tuesday":
    "Today, emphasize the importance of discipline in your walk with God. Where can you apply more focus, set boundaries, and create intentional steps toward fulfilling your calling? How is God calling you to walk in greater obedience? Commit to making decisions today that reflect discipline, knowing it leads to true freedom.",
    "Wednesday":
    "Today’s devotional centers on discovering your Kingdom identity and vision. Reflect on how God sees you and the unique calling He has placed on your life. What actions can you take today to step into that identity more fully? Ask God to give you clarity on your purpose and boldness to walk it out.",
    "Thursday":
    "Today’s focus is on living a life of generosity and service. Who can you bless today with your time, prayers, or resources? Reflect on how your life can serve as a vessel for God’s love. Consider how generosity aligns you with God’s heart and His purposes for His people.",
    "Friday":
    "Today, focus on living in faith and expecting the supernatural. Where do you need God’s miraculous intervention? Step out in faith and trust that God’s power is at work in your life. What bold steps can you take today that require trust in His provision and promises?",
    "Saturday":
    "Today is Shabbat—a time to rest and reflect. Take a step back from action and enter into God’s rest. Reflect on the past week’s victories and lessons, and thank God for His faithfulness. How can you rest in His presence today, knowing He provides all you need?",
    "Sunday":
    "Today’s focus is on revival and awakening. Reflect on how God is stirring your heart and where He is calling you to bring revival. What steps can you take to carry His light into your community? Pray for awakening, both in your life and in the lives of those around you, as you walk boldly in your calling."
}

# Get the current day of the week
current_day = datetime.now().strftime("%A")

# Retrieve the theme based on the current day
theme_content = themes.get(
    current_day,
    "Today, focus on living in faith and expecting the supernatural.")


# Define a function to read a file's content as a string
def read_file_content(file_path):
    with open(file_path, 'r') as file:
        return file.read()


# Path to the files with the context prompts
action_path = './inc/action.inc'
values_path = './inc/values.inc'
style_path = './inc/style.inc'

# Read content from the files
action_content = read_file_content(action_path)
values_content = read_file_content(values_path)
style_content = read_file_content(style_path)

# List of Bible verses
verses = [
    "Jeremiah 29:11", "Proverbs 16:9", "Philippians 3:14",
    "Colossians 3:23-24", "Matthew 5:16", "Ephesians 2:10", "Proverbs 19:21",
    "Romans 8:28", "1 Corinthians 10:31", "Psalm 37:4", "Proverbs 3:5-6",
    "Isaiah 41:10", "2 Timothy 1:9", "Micah 6:8", "Philippians 4:13",
    "Joshua 1:9", "Ecclesiastes 3:1", "Matthew 6:33", "Galatians 6:9",
    "1 Peter 4:10", "Romans 12:2", "Proverbs 16:3", "James 1:12",
    "Philippians 1:6", "Psalm 20:4", "1 Corinthians 9:24-25", "Isaiah 40:31",
    "2 Corinthians 5:20", "Proverbs 29:18", "Hebrews 12:1-2", "Psalm 138:8",
    "Deuteronomy 31:8", "2 Thessalonians 1:11", "1 Timothy 4:12",
    "Romans 12:6-8", "Proverbs 16:1", "Psalm 139:13-14", "Galatians 1:15-16",
    "Exodus 9:16", "Isaiah 43:7", "John 15:16", "Acts 13:36", "Ephesians 4:1",
    "Philippians 2:13", "1 Corinthians 7:17", "Romans 11:29", "2 Peter 1:10",
    "Colossians 1:16", "1 Peter 2:9", "Isaiah 42:6", "Jeremiah 1:5",
    "Romans 8:30", "1 Corinthians 1:9", "Ephesians 1:11", "2 Timothy 2:15",
    "Titus 2:14", "1 Peter 3:9", "Revelation 3:8", "Psalm 57:2",
    "Proverbs 21:5", "Isaiah 46:10", "Matthew 28:19-20", "Luke 12:48",
    "John 17:4", "Acts 20:24", "Romans 12:1", "1 Corinthians 15:58",
    "2 Corinthians 5:9", "Galatians 5:13", "Ephesians 5:15-17",
    "Philippians 3:12-14", "Colossians 4:17", "1 Thessalonians 5:24",
    "2 Timothy 4:7", "Hebrews 10:36", "James 2:14-17", "1 Peter 2:21",
    "2 Peter 3:9", "1 John 3:8", "Psalm 138:8", "Proverbs 16:4",
    "Ecclesiastes 12:13", "Isaiah 43:21", "Jeremiah 32:19", "Daniel 1:8",
    "Hosea 6:6", "Habakkuk 2:2-3", "Zechariah 4:6", "Matthew 5:13-14",
    "Mark 10:45", "Luke 19:10", "John 4:34", "Acts 26:16-18", "Romans 14:8",
    "1 Corinthians 3:9", "2 Corinthians 6:1", "Galatians 2:20",
    "Ephesians 3:20-21", "Philippians 1:21", "Colossians 2:6-7",
    "1 Thessalonians 2:12", "2 Timothy 2:21", "Titus 3:1", "Hebrews 13:21",
    "James 4:8", "1 Peter 5:10", "2 Peter 1:3", "1 John 2:17", "Psalm 33:11",
    "Proverbs 19:21", "Ecclesiastes 3:11", "Isaiah 55:8-9", "Jeremiah 17:7-8",
    "Lamentations 3:24", "Ezekiel 36:26-27", "Daniel 2:20-21", "Joel 2:28",
    "Amos 3:7", "Micah 7:7", "Habakkuk 3:19", "Zephaniah 3:17", "Haggai 2:9",
    "Zechariah 8:13", "Malachi 3:1", "Matthew 10:16", "Mark 16:15",
    "Luke 9:23", "John 6:38", "Acts 1:8", "Romans 5:2-5", "1 Corinthians 2:9",
    "2 Corinthians 3:18", "Galatians 5:22-23", "Ephesians 4:22-24",
    "Philippians 2:3-4", "Colossians 3:2",
    "2 Timothy 3:16-17", "Titus 2:11-12", "Hebrews 11:1", "James 1:22",
    "1 Peter 1:13", "2 Peter 3:18", "1 John 4:19", "Jude 1:20-21",
    "Revelation 21:5"
]

# Select a random verse
selected_verse = random.choice(verses)

DEVOTIONAL_PROMPT = f"""
<devotional_prompt>
<instructions>
Generate a personalized daily devotional based on <devotional_parameters> and <reader_profile> that encourages the reader to live a life of impact and fulfill their God-given purpose. Create a new devotional each time prompted, following the <format> and <rules>. This devotional should encourage them to take action in alignment with <action_steps>, and be consistent and grounded in <curt_landry_principles> and <ministry_values>. Use the <style_guide> and <book_reference> to inform the tone and approach.
</instructions>

<format>
  <introduction>
    Write a 2-sentence encouragement to the reader, by name, combining today's topic, context of the verse, their personal purpose statement, and related context into a powerful statement. Speak over them the goodness of God, their purpose, their identity, and that they do and will live a life of purpose. Output in introduction tag.
  </introduction>
  <verse>
    Quote the given verse using the NKJV Bible, be sure to reference the book, chapter, and verse (Example: - Hebrews 11:1). Output in verse tag.
  </verse>
  <insight>
    Combine the most impactful revelation and insight into the power and meaning of this verse, distilled from all sources, including Curt Landry's teachings, and focused on encouraging the reader forward in purpose, impact, and in alignment with their purpose statement in 3 sentences. Output in insight tag.
  </insight>
  <life_application>
    Focus on the verse and its context. Pull from all sources and related topics to find the most important positive and hope-filled life application for the reader in 2 sentences that encourages them to live a life of impact and fulfill their purpose. Tailor this to who they are and the context given. Output in life_application tag.
  </life_application>
  <declaration>
    Turn the main life application and the reader's purpose statement into a 1-sentence positive affirmation and declaration that the reader can declare over themselves. Output in declaration tag.
  </declaration>
  <prayer>
    Turn the main life application into a short prayer for the reader, asking God to make the application real in their life. End by calling out and reminding them of their identity and purpose in Christ in alignment with their purpose statement. Output in prayer tag.
  </prayer>
<journal>
  Turn the main life application in the context of the reader's purpose statement into a journaling prompt that challenges them to think more deeply about how this message applies to their life and what action steps they can take today to move into a place of greater impact and purpose. Output in journal tag. 
</journal>
</format>

<rules>
  <rule>Tailor the output to the context and reader's profile and purpose statement</rule>
  <rule>Don't include word counts in the output</rule>
  <rule>Provide only the requested information. Your response will be used in an application expecting just the requested content. No filler.</rule>
  <rule>Speak directly to the reader named in the reader profile</rule>
  <rule>Primarily source information and commentary from the given context and Curt Landry or Curt Landry Ministries</rule>
  <rule>Use teachings from similar teachers: John Kilpatrick, Michael Brown, Steve Hill, Paul Wilbur, Robert Henderson</rule>
  <rule>Also reference the following as context: Strong's concordance, Vine's expository Dictionary, Mounce Reverse Interlinear New Testament, Gems from the Greek Vol. 1 & 2, Baker's Evangelical Dictionary of Biblical Theology, Easton's Bible Dictionary, Hitchcock's Bible Names Dictionary, King James Dictionary, Smith's Bible Dictionary, Matthew Henry's Commentary, The Spirit-filled Life New Testament Commentary Series, The Pentecostal Old Testament and New Testament Commentaries, Baker Exegetical Commentary series, Pentecostal Commentary Series, Applied Commentary, Enduring Word Bible Commentary</rule>
</rules>

<devotional_parameters>
  <theme>{theme_content}</theme>
  <focus_verse>{selected_verse}</focus_verse>
</devotional_parameters>

<reader_profile>
  <name>{{reader_name}}</name>
  <sex>{{reader_sex}}</sex>
  <purpose_statement>{{reader_purpose_statement}}
</reader_profile>

{action_content}
{values_content}
{style_content}

</devotional_prompt>
"""

#def format_user_info(user_info):
#   return json.dumps(user_info, default=str).replace('"', '\"')
#user_info_formatted = format_user_info(user_info)

def generate_devotional_content(user_info=None):
    if user_info is None:
        user_info = {}

    reader_name = user_info.get('reader_name', '')
    reader_sex = user_info.get('reader_sex', '')
    reader_purpose_statement = user_info.get('reader_purpose_statement', '')
    
    # Now format the DEVOTIONAL_PROMPT with the user info
    personalized_prompt = DEVOTIONAL_PROMPT.format(
        reader_name=reader_name,
        reader_sex=reader_sex,
        reader_purpose_statement=reader_purpose_statement
    )

    #testing
    #return personalized_prompt
    
    # Check if we have user info to proceed with generating content
    if not any([reader_name, reader_sex, reader_purpose_statement]):
        return "Please provide user information to generate a devotional."
    


    devotional = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system=
        "You are a consensual extension of Rabbi Curt Landry, coaching and guiding people into their purpose, calling, and life of impact, using the Bible. Emulate Curt Landry's authoritative yet compassionate tone.",
        messages=[{
            "role": "user",
            "content": [{
                "type": "text",
                "text": personalized_prompt
            }]
        }])
    return devotional.content[0].text

def main():
    # Example user information
    user_info = {
        "reader_name": "John",
        "reader_sex": None,
        "reader_purpose_statement": "To inspire and guide others in their spiritual journey, showing them the path to fulfillment in God's love and wisdom."
    }

    # Generate and display the devotional content
    devotional_content = generate_devotional_content(user_info)
    print("Generated Devotional Content:\n")
    print(devotional_content)

if __name__ == "__main__":
    main()
