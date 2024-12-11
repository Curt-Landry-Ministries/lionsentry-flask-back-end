import os
import re
import json
import random
import anthropic
from datetime import datetime
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

# Load environment variables
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# System role definition
ANTHROPIC_ROLE = "You are a consensual extension of Rabbi Curt Landry, coaching and guiding people into their purpose, calling, and life of impact, using the Bible. Emulate Curt Landry's authoritative yet compassionate tone."

# Themes for each day of the week
THEMES = {
    "Monday": "Today's focus is on aligning your life with God's covenant...",
    "Tuesday": "Today, emphasize the importance of discipline in your walk...",
    "Wednesday": "Today's devotional centers on discovering your Kingdom identity...",
    "Thursday": "Today's focus is on living a life of generosity and service...",
    "Friday": "Today, focus on living in faith and expecting the supernatural...",
    "Saturday": "Today is Shabbat—a time to rest and reflect...",
    "Sunday": "Today's focus is on revival and awakening...",
}

# Consolidated content
ACTION_STEPS = """
<action_steps>
<step>Pray for the peace of Jerusalem - Align yourself with God's heart for Israel.</step>
<step>Stand with Israel - Make it clear whose side you're on.</step>
<step>Discipline leads to freedom - Be disciplined in all areas of life.</step>
<step>Cut off distractions - Remove anything that pulls you away from God's purpose.</step>
<step>Ask God for direction - Don't make a move without asking Him first.</step>
<step>Serve others - Be a giver, not a taker; look for ways to sow into lives.</step>
<step>Trust God fully - Let go of control and trust Him with every area of life.</step>
</action_steps>
"""

CURT_LANDRY_PRINCIPLES = """
<action_steps>
    <step>Pray for the peace of Jerusalem - Align yourself with God's heart for Israel.</step>
    <step>Blow the trumpet in Zion - Start your day declaring victory.</step>
    <step>Stand with Israel - Make it clear whose side you're on.</step>
    <step>Prepare for the double portion - Position yourself for God's abundant blessing.</step>
    <step>Embrace correction - Grow by receiving and applying discipline.</step>
    <step>Write your goals down - Set clear, written goals with deadlines.</step>
    <step>Align with covenant - Stay in God's covenant to receive provision and blessing.</step>
    <step>Cut off generational chains - Declare freedom from generational iniquities.</step>
    <step>Discipline leads to freedom - Be disciplined in all areas of life.</step>
    <step>Seek first the Kingdom - Prioritize God's Kingdom over everything else.</step>
    <step>Take action on resolutions - Don't just dream—move, act, and apply.</step>
    <step>Know who gives you power - Acknowledge that God is the source of your success.</step>
    <step>Walk in the Fruit of the Spirit - Stay in love, joy, peace, and self-control.</step>
    <step>Cut off distractions - Remove anything that pulls you away from God's purpose.</step>
    <step>Ask God for direction - Don't make a move without asking Him first.</step>
    <step>Break free from fear - Admit where you're stuck in fear and switch to faith.</step>
    <step>Serve others - Be a giver, not a taker; look for ways to sow into lives.</step>
    <step>Trust God fully - Let go of control and trust Him with every area of life.</step>
    <step>Walk in supernatural freedom - Declare that your DNA is in Christ, and you are free.</step>
    <step>Stay teachable - If you can't be corrected, you can't grow.</step>
    <step>Pray and proclaim the Word daily - Take 20 minutes every morning to speak life.</step>
    <step>Remember who you are in Christ - Your identity is in His victory, not your failures.</step>
    <step>Expect the supernatural - Get ready for miracles in 2024.</step>
    <step>Remove negative influences - Cut off news or social media that feeds fear.</step>
    <step>Be ready for justice - God is bringing judgment and justice—align with it.</step>
    <step>Visualize your goals - Keep a picture of your goal in front of you and speak life over it.</step>
    <step>Embrace the coming revival - Get ready for a global awakening; you're part of it.</step>
    <step>Sow aggressively - Start the year off by sowing generously.</step>
    <step>Strengthen your weaknesses - Identify areas of struggle and work on them.</step>
    <step>Choose joy and rest - Plan for joy and recreation to avoid burnout.</step>
  </action_steps>
"""

MINISTRY_VALUES = """
<curt_landry_principles>
    <principle>Discipline as Freedom: Discipline is foundational for personal freedom and success.</principle>
    <principle>Written Goals and Boundaries: Set clear, written goals as boundaries for the mind and personal values.</principle>
    <principle>Covenant Alignment: Align with the right values and disciplines for blessings to flow naturally.</principle>
    <principle>Problems as Opportunities for Growth: View problems as opportunities for correction and growth.</principle>
    <principle>The Importance of Correction: Be open to correction without taking offense for growth.</principle>
    <principle>Spiritual Connection: Seek divine wisdom and align with higher spiritual purposes.</principle>
    <principle>Global Awareness and Action: Understand broader global issues to make a meaningful impact.</principle>
    <principle>Blow the Trumpet and Pray: Pray for the peace of Jerusalem to align with God's purpose.</principle>
    <principle>Stand with God's Covenant: Align yourself with God's plan and covenant people.</principle>
    <principle>Embrace God's Abundance: Position yourself for God's outpouring through obedience.</principle>
    <principle>Be Ready for Justice: Stand bold in truth as God restores justice.</principle>
    <principle>Prepare for Revival: Position yourself as a vessel for God's revival fire.</principle>
    <principle>Align with God's Timing: Declare and receive God's favor in this season.</principle>
    <principle>Break Generational Chains: Walk in supernatural freedom as a co-heir with Christ.</principle>
    <principle>Pursue Focused Goals: Narrow down priorities to key goals aligned with God's purpose.</principle>
    <principle>Seek Covenant Provision: Stay in covenant alignment for natural provision flow.</principle>
    <principle>Address Root Issues: Look for underlying principles needing reinforcement in challenges.</principle>
    <principle>Embrace Growth through Correction: Be teachable and open to correction for maturity.</principle>
    <principle>Actively Engage with God's Word: Write, speak, and pray God's Word daily for transformation.</principle>
  </curt_landry_principles>

  <ministry_values>
    <value>Integrity: Walk in integrity, committed to truth and honor.</value>
    <value>Honoring God and Others: Honor God's Word and treat others with respect.</value>
    <value>Purpose-Driven: Achieve results driven by purpose, not ego.</value>
    <value>Biblical Principles: Adhere to biblically based, moral, and ethical principles.</value>
    <value>Trustworthiness: Be dependable and communicate openly and honestly.</value>
    <value>High Ethical Standards: Embrace high standards that strengthen integrity.</value>
    <value>Living in Truth: Live, speak, and operate in the freedom of truth.</value>
    <value>Transparency: Voice concerns to ensure open and honest communication.</value>
    <value>Excellence and Endurance: Operate with excellence and perseverance.</value>
    <value>Faith and Holiness: Produce good fruit through a lifestyle of holiness.</value>
    <value>Devotion and Unity: Be devoted, loyal, and unified in love and generosity.</value>
    <value>Truth and Vision: Commit to living in truth and passionately pursuing vision.</value>
  </ministry_values>
"""

STYLE_GUIDE = """
<style_guide>
    <voice>Emulate Curt Landry's authoritative yet compassionate tone</voice>
    <word_choice>Use terminology and phrasing consistent with "Reclaiming Our Forgotten Heritage"</word_choice>
    <theological_emphasis>Focus on the believer's identity in Christ and walking out their purpose in covenant with God</theological_emphasis>
  </style_guide>
  
  <book_reference>
    <book_info>
      <title>Reclaiming Our Forgotten Heritage</title>
      <author>Curt Landry</author>
      <description>A guide to understanding the Jewish roots of Christian faith, emphasizing covenant relationships and reconnecting with biblical heritage.</description>
    </book_info>

    <key_elements>
      <concepts>
        <item>Covenant Relationship</item>
        <item>Jewish Roots of Christianity</item>
        <item>Identity in Christ</item>
        <item>Alignment with God's Timing</item>
        <item>Kingdom Mindset</item>
        <item>Spiritual Warfare</item>
        <item>Generational Blessings and Curses</item>
        <item>Prophetic Insight</item>
        <item>Restoration of Biblical Feasts</item>
        <item>One New Man</item>
      </concepts>

      <language_style>
        <hebrew_terms>
          <item>Yeshua</item>
          <item>Shalom</item>
          <item>Shofar</item>
        </hebrew_terms>
        <covenant_language>
          <item>blood covenant</item>
          <item>covenant alignment</item>
          <item>Abrahamic blessing</item>
        </covenant_language>
        <other_elements>
          <item>Prophetic Declarations</item>
          <item>Warfare Terminology</item>
          <item>Biblical Imagery</item>
        </other_elements>
      </language_style>

      <theological_emphases>
        <item>Covenant Theology</item>
        <item>Kingdom Now Perspective</item>
        <item>Hebraic Worldview</item>
        <item>Prophetic Interpretation of Current Events</item>
        <item>Spiritual Warfare Mindset</item>
        <item>Restoration Theology</item>
      </theological_emphases>

      <themes>
        <item>Identity and Purpose</item>
        <item>Alignment with God's Timing</item>
        <item>Spiritual Inheritance</item>
        <item>Israel and the Church</item>
        <item>Supernatural Living</item>
        <item>Generational Impact</item>
      </themes>

      <writing_style>
        <item>Direct Address</item>
        <item>Personal Anecdotes</item>
        <item>Authoritative Tone</item>
        <item>Passionate Exhortation</item>
        <item>Prophetic Insight</item>
      </writing_style>

      <unique_perspectives>
        <item>Hebraic Time Concept</item>
        <item>Dual Covenant Theology</item>
        <item>Spiritual DNA</item>
        <item>Prophetic Intercession</item>
      </unique_perspectives>
    </key_elements>

    <content_guidelines>
      <guideline>Use Hebrew terms and covenant language.</guideline>
      <guideline>Interpret current events through a prophetic, Israel-centric lens.</guideline>
      <guideline>Emphasize the believer's authority and responsibility in manifesting God's Kingdom.</guideline>
      <guideline>Encourage readers to discover their true identity in Christ and fulfill their God-given purpose.</guideline>
      <guideline>Incorporate teachings on biblical feasts and their relevance to Christians.</guideline>
      <guideline>Address spiritual warfare and the importance of standing firm in faith.</guideline>
      <guideline>Stress the interconnected destinies of Israel and the Christian Church.</guideline>
      <guideline>Use passionate, declarative language to motivate readers to action.</guideline>
      <guideline>Share personal anecdotes to illustrate spiritual principles.</guideline>
      <guideline>Promote a supernatural lifestyle and expectation of God's intervention.</guideline>
    </content_guidelines>
  </book_reference>
"""

# Bible Verses
VERSES = [    
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

# Select the theme and verse for the current day
current_day = datetime.now().strftime("%A")
theme_content = THEMES.get(current_day, "Today, focus on living in faith and expecting the supernatural.")
selected_verse = random.choice(VERSES)

# Devotional prompt template
DEVOTIONAL_PROMPT_TEMPLATE = f"""
<devotional_prompt>
<instructions>
Generate a daily devotional based on <theme> and <verse>, grounded in <action_steps>, <curt_landry_principles>, and <ministry_values>. Use the <style_guide> for tone and approach. Provide response in json format.
</instructions>
<format>
  <introduction>Write a 2-sentence encouragement combining today's theme and verse.</introduction>
  <verse>Quote the given verse using NKJV format: "{selected_verse}".</verse>
  <insight>Provide an impactful revelation based on the verse in 3 sentences.</insight>
  <life_application>Offer a hope-filled life application tailored to the reader in 2 sentences.</life_application>
  <declaration>Write a 1-sentence affirmation based on the theme and verse.</declaration>
  <prayer>Offer a short prayer aligned with the theme and reader's purpose.</prayer>
</format>
<theme>{theme_content}</theme>
<verse>{selected_verse}</verse>
{ACTION_STEPS}
{CURT_LANDRY_PRINCIPLES}
{MINISTRY_VALUES}
{STYLE_GUIDE}
</devotional_prompt>
"""

def generate_devotional_content(reader_name="", reader_purpose_statement=""):
    """Generate devotional content personalized for the reader."""
    personalized_prompt = DEVOTIONAL_PROMPT_TEMPLATE.replace("{{name}}", reader_name)
    
    # Generate devotional via Anthropic API
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system=ANTHROPIC_ROLE,
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": personalized_prompt}]
        }]
    )
     # Clean the response content
    raw_response = response.content[0].text
    return raw_response

def parse_xml_to_json(xml_string):
    """Parse XML string into a clean JSON dictionary."""
    try:
        root = ET.fromstring(xml_string)
        devotional = {}
        for child in root:
            devotional[child.tag] = re.sub(r'\s+', ' ', child.text.strip()) if child.text else ""
        return devotional
    except ET.ParseError:
        return {"error": "Failed to parse XML response."}

# Example usage
if __name__ == "__main__":
    user_info = {
        "reader_name": "John",
        "reader_purpose_statement": "To inspire and lead others to faith and purpose."
    }
    devotional_content = generate_devotional_content(
        reader_name=user_info['reader_name'],
        reader_purpose_statement=user_info['reader_purpose_statement']
    )
    print(devotional_content)
