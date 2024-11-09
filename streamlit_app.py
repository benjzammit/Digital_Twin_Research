import streamlit as st
import openai
from io import BytesIO
from PIL import Image
import json
import os
from openai import OpenAI


# Load OpenAI API key from Streamlit secrets
client = OpenAI(
    api_key=st.secrets["api_keys"]["OPENAI_API_KEY"]
)


# Load personas from JSON file
def load_personas():
    with open('personas.json', 'r') as f:
        personas_data = json.load(f)
    return personas_data

personas_data = load_personas()

# Function to format persona sections
def format_persona_section(section_title, section_data):
    formatted_section = f"{section_title}:\n"
    for key, value in section_data.items():
        if isinstance(value, dict):
            formatted_section += f"  {key}:\n"
            for sub_key, sub_value in value.items():
                formatted_section += f"    {sub_key}: {sub_value}\n"
        elif isinstance(value, list):
            formatted_section += f"  {key}: {', '.join(map(str, value))}\n"
        else:
            formatted_section += f"  {key}: {value}\n"
    return formatted_section + "\n"

# Helper function to generate feedback and perform sentiment analysis
def generate_digital_twin_feedback(persona_description, testing_material):
    # Construct the prompt
    prompt = (
        f"As a digital twin of the following customer persona:\n\n"
        f"{persona_description}\n"
        f"Provide 3-5 critical, actionable insights on the following material. "
        f"Focus on how it meets or fails to meet the persona's needs and preferences. "
        f"Present your feedback in bullet points:\n\n"
        f"{testing_material}"
    )
    try:
        # Generate feedback
        response =  client.chat.completions.create(
            model="gpt-4",  # Use "gpt-4" if you have access; else use "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a customer digital twin providing realistic feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,  # Reduced to limit output length
            temperature=0.7,
        )
        feedback = response.choices[0].message.content.strip()
        
        # Perform sentiment analysis on the feedback
        sentiment_prompt = (
            "Analyze the sentiment of the following feedback and classify it as Positive, Neutral, or Negative. "
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
            max_tokens=50,
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

# Custom CSS for modern styling
st.markdown("""
    <style>
        /* Add your custom CSS styles here */
        /* Brand Colors and Fonts */
        :root {
            --primary-color: #4A90E2; /* Reflective brand blue */
            --secondary-color: #2E3B4E; /* Dark slate color */
            --accent-color: #F5A623; /* Accent orange */
            --background-color: #F4F7FA; /* Light background */
            --text-color: #333; /* Standard dark text */
            --positive-color: #2ECC71; /* Green */
            --neutral-color: #95A5A6; /* Gray */
            --negative-color: #E74C3C; /* Red */
        }

        /* Main Header */
        .main-header {
            text-align: center; 
            color: var(--primary-color);
            margin-top: -40px;
            font-size: 2.5em;
            font-weight: 700;
        }

        /* Tagline */
        .tagline {
            text-align: center;
            color: var(--secondary-color);
            font-size: 1.2em;
            font-weight: 400;
            margin-bottom: 30px;
        }

        /* Feedback Boxes */
        .feedback-box {
            background-color: var(--background-color);
            padding: 15px; 
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            color: var(--text-color);
        }

        /* Sentiment Label */
        .sentiment-label {
            font-weight: bold;
            font-size: 1em;
        }

        /* Positive Sentiment */
        .positive {
            color: var(--positive-color);
        }

        /* Neutral Sentiment */
        .neutral {
            color: var(--neutral-color);
        }

        /* Negative Sentiment */
        .negative {
            color: var(--negative-color);
        }

        /* Sidebar Persona Details */
        .persona-details {
            margin-top: 10px;
            margin-bottom: 10px;
        }
        .persona-details h4 {
            margin-bottom: 5px;
        }
        .persona-details p {
            margin: 0;
        }

        /* Footer */
        .footer {
            text-align: center;
            color: var(--secondary-color);
            margin-top: 50px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for feedback
if 'feedback_dict' not in st.session_state:
    st.session_state['feedback_dict'] = {}

# Set up the Reflective brand layout
st.markdown("<h1 class='main-header'>Reflective</h1>", unsafe_allow_html=True)
st.markdown("<div class='tagline'>Real-world reactions, instantly delivered.</div>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar Input Section for Testing Material
st.sidebar.header("💡 Testing Material")
testing_material = st.sidebar.text_area("Describe what you want feedback on:", height=150, placeholder="Enter a concept, image description, or idea...")

# Sidebar for Creative Uploads
st.sidebar.header("🎨 Upload Creative (Optional)")
creative = st.sidebar.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
if creative:
    image = Image.open(creative)
    # Convert image to bytes (if needed for future use)
    img_bytes = BytesIO()
    image.save(img_bytes, format=image.format)
    img_bytes = img_bytes.getvalue()

# Sidebar for Digital Twin Selection
st.sidebar.header("👥 Select Digital Twin Personas")

# Create a dictionary to map persona titles to their data
personas_dict = {persona['title']: persona for persona in personas_data}

# List of persona titles for selection
personas_list = [persona['title'] for persona in personas_data]

personas_selected = st.sidebar.multiselect(
    "Choose personas for feedback",
    personas_list,
    default=[personas_list[0]],  # Default to the first persona
    help="Search and select personas"
)

# Sidebar - Persona Descriptions using expanders
st.sidebar.markdown("### Persona Details")
for title in personas_selected:
    persona = personas_dict[title]
    with st.sidebar.expander(f"{persona['name']}, {persona['age']} - {persona['occupation']}"):
        st.write(persona['description'])
        if persona.get('image'):
            if os.path.exists(persona['image']):
                st.image(persona['image'], width=100)
            else:
                st.write("Image not found.")

# Generate Feedback Button in Sidebar
if st.sidebar.button("Generate Feedback", key="generate"):
    if not testing_material and not creative:
        st.error("Please enter or upload testing material to receive feedback.")
    elif not personas_selected:
        st.error("Please select at least one digital twin persona to generate feedback.")
    else:
        # Initialize feedback dictionary
        st.session_state['feedback_dict'] = {}

        # Collect feedback from all personas
        all_feedbacks = []
        for title in personas_selected:
            persona = personas_dict[title]
            # Create a detailed description
            # Basic information
            persona_description = (
                f"Name: {persona['name']}\n"
                f"Age: {persona['age']}\n"
                f"Gender: {persona['gender']}\n"
                f"Location: {persona['location']}\n"
                f"Marital Status: {persona['marital_status']}\n"
                f"Education: {persona['education']}\n"
                f"Occupation: {persona['occupation']}\n"
                f"Income: {persona['income']}\n"
                f"Ethnicity: {persona['ethnicity']}\n"
                f"Religion: {persona['religion']}\n\n"
            )
            
            # Sections to include
            sections = [
                ('Personality Traits', persona['personality_traits']),
                ('Values and Beliefs', persona['values_and_beliefs']),
                ('Behavioral Patterns', persona['behavioral_patterns']),
                ('Preferences and Interests', persona['preferences_and_interests']),
                ('Emotional Responses', persona['emotional_responses']),
                ('Communication Style', persona['communication_style']),
                ('Consumer Behavior', persona['consumer_behavior']),
                ('Technology Usage', persona['technology_usage']),
                ('Additional Insights', persona['additional_insights'])
            ]
            
            for section_title, section_data in sections:
                persona_description += format_persona_section(section_title, section_data)
            
            # Generate feedback
            with st.spinner(f"Generating feedback from {persona['name']}..."):
                feedback, sentiment_data = generate_digital_twin_feedback(persona_description, testing_material)
                if sentiment_data:
                    sentiment = sentiment_data.get("sentiment", "Neutral")
                    confidence = sentiment_data.get("confidence", "N/A")
                    
                    st.session_state['feedback_dict'][title] = {
                        "feedback": feedback,
                        "sentiment": sentiment,
                        "confidence": confidence
                    }
                    all_feedbacks.append(feedback)
                else:
                    st.session_state['feedback_dict'][title] = {
                        "feedback": feedback,
                        "sentiment": "Error",
                        "confidence": "N/A"
                    }
                    all_feedbacks.append(feedback)
        
        # Create tabs for output
        tab1, tab2 = st.tabs(["📊 Overall Analysis", "📝 Individual Feedback"])

        with tab1:
            st.markdown("## 📊 Overall Analysis")
            combined_feedback = "\n\n".join(all_feedbacks)
            try:
                analysis_prompt = (
                    "Analyze the following feedbacks from different personas and summarize the common trends, themes, "
                    "and overall sentiment. Provide actionable insights in bullet points:\n\nFeedbacks:\n"
                    f"{combined_feedback}"
                )
                analysis_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an analysis assistant that provides summaries and insights."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7,
                )
                overall_analysis = analysis_response.choices[0].message.content.strip()
                st.markdown(f"<div class='feedback-box'>{overall_analysis}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"An error occurred during overall analysis: {str(e)}")

        with tab2:
            st.markdown("## 📝 Individual Feedback")
            for title in personas_selected:
                persona = personas_dict[title]
                data = st.session_state['feedback_dict'][title]
                feedback = data['feedback']
                sentiment = data['sentiment']
                confidence = data['confidence']
                
                icon = sentiment_icon(sentiment)
                with st.expander(f"{icon} Feedback from {persona['name']} ({sentiment} - {confidence})"):
                    st.markdown(feedback)
                    # Download option for each persona's feedback
                    feedback_file = BytesIO()
                    feedback_file.write(feedback.encode())
                    feedback_file.seek(0)
                    st.download_button(
                        label=f"Download {persona['name']}'s Feedback",
                        data=feedback_file,
                        file_name=f"{persona['name']}_feedback.txt",
                        mime="text/plain",
                    )
        st.success("Feedback generated successfully!")

# Main Section - Display the Testing Material or Creative Asset if uploaded
st.markdown("## 👁️ Testing Material Preview")
if creative:
    st.image(creative, caption="Uploaded Creative", use_column_width=True)
if testing_material:
    st.markdown(f"**Testing Material Description:** {testing_material}")
elif not creative:
    st.info("Upload an image or describe your concept to get started.")

# Footer
st.markdown("---")
st.markdown("<div class='footer'>Built with ❤️ by Reflective - Real-world reactions, instantly delivered.</div>", unsafe_allow_html=True)
