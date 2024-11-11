import streamlit as st
import openai
from io import BytesIO
import json
import os
from openai import OpenAI
import matplotlib.pyplot as plt
import re

# Initialize OpenAI client
client = OpenAI(
    api_key=st.secrets["api_keys"]["OPENAI_API_KEY"]
)

# Load personas from JSON file with caching for performance
@st.cache_data
def load_personas():
    with open('personas.json', 'r') as f:
        personas_data = json.load(f)
    return personas_data

personas_data = load_personas()

# Enhanced Feedback Generation Function
def generate_digital_twin_feedback(persona, testing_material, response_type):
    """
    Generates feedback from a digital twin persona.

    Args:
        persona (dict): The persona dictionary containing all attributes.
        testing_material (str): The material to be reviewed.
        response_type (str): 'Short' or 'Detailed' response.

    Returns:
        tuple: Feedback string and sentiment data dictionary.
    """
    # Construct the system message with detailed persona information
    system_message = (
        f"You are {persona['name']}, a {persona['age']}-year-old {persona['title']} from {persona['location']}. "
        f"Your background includes a {persona['education']} and you work as a {persona['occupation']}. "
        f"Your income ranges between {persona['income']}. "
        f"Your key characteristics include: {', '.join([f'{k}: {v}' for k, v in persona['personality_traits'].items()])}. "
        f"You value {', '.join(persona['values_and_beliefs']['value_priorities'])}. "
        f"Your daily routine involves {persona['behavioral_patterns']['daily_routine']}. "
        f"You prefer {', '.join(persona['preferences_and_interests']['favorite_social_media'])} for social media. "
        f"Your communication style is {persona['communication_style']['information_preference'][0].lower()}."
    )

    # Adjust the user prompt based on response type
    if response_type == 'Detailed':
        user_prompt = (
            f"As {persona['name']}, provide exactly 3-4 critical, actionable insights on the following material. "
            f"Include concrete suggestions or improvements if applicable, and conclude with a summary statement or overall opinion."
            f"\n\nMaterial for Review:\n{testing_material}"
        )
    elif response_type == 'Short':
        user_prompt = (
            f"As {persona['name']}, provide 2-3 concise feedback points on the following material. "
            f"Focus on high-level insights, but include specific examples, names, brands, or places that relate to your perspective or lifestyle. "
            f"Keep each point brief but context-specific. "
            f"Present feedback in bullet points."
            f"\n\nMaterial for Review:\n{testing_material}"
        )

    try:
        # Generate feedback
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=400,
            temperature=0.7,
        )
        feedback = response.choices[0].message.content.strip()

        # Perform sentiment analysis on the feedback
        sentiment_prompt = (
            "Analyze the overall sentiment of the following feedback and classify it as Positive, Neutral, or Negative. "
            "Provide a confidence score between 0% and 100%. "
            "Return the result in JSON format like {\"sentiment\": \"Positive\", \"confidence\": \"85%\"}.\n\n"
            f"Feedback:\n{feedback}"
        )
        sentiment_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis assistant."},
                {"role": "user", "content": sentiment_prompt}
            ],
            max_tokens=60,
            temperature=0,
        )
        sentiment_content = sentiment_response.choices[0].message.content.strip()
        sentiment_data = json.loads(sentiment_content)

        return feedback, sentiment_data
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return error_message, None

# Function to get sentiment icon
def sentiment_icon(sentiment):
    if sentiment.lower() == 'positive':
        return '🟢'
    elif sentiment.lower() == 'negative':
        return '🔴'
    else:
        return '🟡'

# Initialize session state for feedback
if 'feedback_dict' not in st.session_state:
    st.session_state['feedback_dict'] = {}

# Set up the Reflective brand layout
st.markdown("<h1 class='main-header'>Reflective</h1>", unsafe_allow_html=True)
st.markdown("<div class='tagline'>Real-world reactions, instantly delivered.</div>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar Input Section for Feedback Content
st.sidebar.header("💡 Brief")
feedback_content = st.sidebar.text_area(
    "Enter your idea, strategy, or concept to receive group feedback on",
    height=150,
    placeholder="Enter a concept, image description, or idea..."
)

# Sidebar - Response Type Selection
st.sidebar.header("Response Type")
response_type = st.sidebar.selectbox(
    "Select the type of response:",
    options=["Short", "Detailed"],
    index=0,
    help="Choose between a detailed or short response from the personas"
)

# Sidebar for Digital Twin Selection
st.sidebar.header("Select Digital Twins")

# Create a dictionary to map persona titles to their data
personas_dict = {persona['id']: persona for persona in personas_data}

# List of persona titles for selection
personas_list = [f"{persona['name']} - {persona['title']}" for persona in personas_data]
personas_ids = [persona['id'] for persona in personas_data]

# Mapping for multiselect
personas_map = {f"{persona['name']} - {persona['title']}": persona_id for persona, persona_id in zip(personas_data, personas_ids)}

personas_selected = st.sidebar.multiselect(
    "Choose personas for feedback",
    options=list(personas_map.keys()),
    default=[list(personas_map.keys())[0]],
    help="Search and select personas"
)

# Sidebar - Persona Descriptions using expanders
st.sidebar.markdown("### Persona Details")
for persona_title in personas_selected:
    persona_id = personas_map[persona_title]
    persona = personas_dict[persona_id]
    with st.sidebar.expander(f"{persona['name']}, {persona['age']} - {persona['occupation']}"):
        st.write(persona['description'])
        if persona.get('image') and os.path.exists(persona['image']):
            st.image(persona['image'], width=100)
        elif persona.get('image'):
            st.write("Image not found.")

# Generate Feedback Button in Sidebar
if st.sidebar.button("Generate Feedback", key="generate"):
    if not feedback_content:
        st.error("Please enter feedback content to receive feedback.")
    elif not personas_selected:
        st.error("Please select at least one digital twin persona to generate feedback.")
    else:
        # Initialize feedback dictionary
        st.session_state['feedback_dict'] = {}

        # Collect feedback from all personas
        all_feedbacks = []
        sentiment_counts = {'Positive': 0, 'Neutral': 0, 'Negative': 0}

        for persona_title in personas_selected:
            persona_id = personas_map[persona_title]
            persona = personas_dict[persona_id]

            # Generate feedback
            with st.spinner(f"Generating feedback from {persona['name']}..."):
                feedback, sentiment_data = generate_digital_twin_feedback(persona, feedback_content, response_type)
                if sentiment_data:
                    sentiment = sentiment_data.get("sentiment", "Neutral")
                    confidence = sentiment_data.get("confidence", "N/A")

                    st.session_state['feedback_dict'][persona_id] = {
                        "feedback": feedback,
                        "sentiment": sentiment,
                        "confidence": confidence
                    }
                    all_feedbacks.append(feedback)

                    # Update sentiment counts for visualization
                    if sentiment in sentiment_counts:
                        sentiment_counts[sentiment] += 1
                    else:
                        sentiment_counts['Neutral'] += 1
                else:
                    st.session_state['feedback_dict'][persona_id] = {
                        "feedback": feedback,
                        "sentiment": "Error",
                        "confidence": "N/A"
                    }
                    all_feedbacks.append(feedback)

        # Create tabs for output with Individual Feedback first
        tab1, tab2 = st.tabs(["📝 Individual Feedback", "📊 Overall Analysis"])

        with tab1:
            st.markdown("## 📝 Individual Feedback")
            for persona_title in personas_selected:
                persona_id = personas_map[persona_title]
                persona = personas_dict[persona_id]
                data = st.session_state['feedback_dict'][persona_id]
                feedback = data['feedback']
                sentiment = data['sentiment']
                confidence = data['confidence']

                icon = sentiment_icon(sentiment)
                with st.expander(f"{icon} Feedback from {persona['name']} ({sentiment} - {confidence}%)"):
                    st.markdown(feedback)
                    # Download option for each persona's feedback
                    feedback_file = BytesIO()
                    feedback_file.write(feedback.encode())
                    feedback_file.seek(0)
                    st.download_button(
                        label=f"Download {persona['name']}'s Feedback",
                        data=feedback_file,
                        file_name=f"{persona['name'].replace(' ', '_')}_feedback.txt",
                        mime="text/plain",
                    )

        with tab2:
            st.markdown("## 📊 Overall Analysis")
            # Generate overall analysis using OpenAI
            combined_feedback = "\n\n".join(all_feedbacks)
            try:
                analysis_prompt = (
                    "Analyze the following feedbacks from different personas and summarize the common trends, themes, "
                    "and overall sentiment. Provide actionable insights in bullet points, avoiding repetitive points."
                    "\n\nFeedbacks:\n"
                    f"{combined_feedback}"
                )
                analysis_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an analysis assistant that provides concise summaries and key insights."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.5,
                )
                overall_analysis = analysis_response.choices[0].message.content.strip()
                st.markdown(f"<div class='feedback-box'>{overall_analysis}</div>", unsafe_allow_html=True)

                # Visual Representation: Sentiment Distribution
                st.markdown("### Sentiment Distribution")
                sentiments = list(sentiment_counts.keys())
                counts = list(sentiment_counts.values())

                fig, ax = plt.subplots()
                ax.pie(counts, labels=sentiments, autopct='%1.1f%%', colors=['#2ECC71', '#95A5A6', '#E74C3C'])
                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                st.pyplot(fig)

            except Exception as e:
                st.error(f"An error occurred during overall analysis: {str(e)}")

        st.success("Feedback generated successfully!")

# Main Section - Display the Feedback Content
if feedback_content:
    st.markdown("### 📝 Your Feedback Content")
    st.markdown(f"> {feedback_content}")  # Blockquote for emphasis
else:
    st.markdown("## 👁️ Feedback Preview")
    st.info("Describe your concept or idea to get started.")

# Footer
st.markdown("---")
st.markdown("<div class='footer'>Built with ❤️ by Reflective - Real-world reactions, instantly delivered.</div>", unsafe_allow_html=True)
