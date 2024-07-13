import streamlit as st
from datetime import datetime
from generate_devotional import generate_devotional_content

def main():
    st.title("Devotional Content Generator")
    
    st.header("User Information")
    
    user_info = {}
    
    user_info['beliefs'] = st.text_area("1. What do you believe about the world?", "")
    user_info['felt_alive'] = st.text_area("2. When have you felt most alive?", "")
    user_info['relationship_importance'] = st.text_area("3. What's most important in your relationships?", "")
    user_info['why_statement'] = st.text_area("Why Statement", "")
    
    if st.button("Generate Devotional Content"):
        if all(user_info.values()):
            user_info['timestamp'] = datetime.now().isoformat()
            
            with st.spinner("Generating content..."):
                devotional_content = generate_devotional_content(user_info)
            
            st.header("Generated Devotional Content")
            st.subheader("Title")
            st.write(devotional_content.get('Title', ''))
            st.subheader("Bible Passage")
            st.write(devotional_content.get('BiblePassage', ''))
            st.subheader("Personalization")
            st.write(devotional_content.get('Personalization', ''))
            st.subheader("Journaling Prompt")
            st.write(devotional_content.get('JournalingPrompt', ''))
        else:
            st.warning("Please answer all the questions and provide a Why Statement.")

if __name__ == "__main__":
    main()