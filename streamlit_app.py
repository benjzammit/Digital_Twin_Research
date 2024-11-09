import streamlit as st
import openai
from io import BytesIO
from PIL import Image
from openai import OpenAI
import json

# Load OpenAI API key from Streamlit secrets
client = OpenAI(
    api_key= st.secrets["api_keys"]["OPENAI_API_KEY"]
    )
if not openai.api_key:
    st.error("OpenAI API key not found. Please add it to Streamlit secrets.")
    st.stop()

# Helper function to generate feedback and perform sentiment analysis
def generate_digital_twin_feedback(persona, testing_material):
    prompt = f"You are a digital twin of a real customer persona: {persona}. Provide feedback on the following material: {testing_material}."
    # Use client.chat.completions.create with model="gpt-4o"

    try:
        # Generate feedback
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a customer digital twin providing realistic feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
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

# Custom CSS for modern styling
st.markdown("""
    <style>
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

        /* Sidebar Header */
        .sidebar-section {
            margin-top: 20px;
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

        /* Button Styling */
        .stButton>button {
            width: 100%; 
            border-radius: 8px;
            padding: 10px 0;
            background-color: var(--accent-color);
            color: #fff;
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        /* Button Hover Effect */
        .stButton>button:hover {
            background-color: #e68920;
        }

        /* Download Button */
        .download-button {
            margin-top: 20px;
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
testing_material = st.sidebar.text_area("Describe or upload what you want feedback on:", height=150, placeholder="Enter a concept, image description, or idea...")

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
personas = st.sidebar.multiselect(
    "Choose personas for feedback",
    ["Tech-Savvy Millennial", "Eco-Conscious Consumer", "Health Enthusiast", "Frequent Traveler", "Parent with Young Kids"],
    default=["Tech-Savvy Millennial"]
)

# Main Section - Display the Testing Material or Creative Asset if uploaded
st.markdown("## 👁️ Testing Material Preview")
if creative:
    st.image(creative, caption="Uploaded Creative", use_column_width=True)
if testing_material:
    st.markdown(f"**Testing Material Description:** {testing_material}")
elif not creative:
    st.info("Upload an image or describe your concept to get started.")

# Generate Feedback Button
st.markdown("### 💡 Generate Feedback from Digital Twins")
if st.button("Generate Feedback", key="generate"):
    if not testing_material and not creative:
        st.error("Please enter or upload testing material to receive feedback.")
    elif not personas:
        st.error("Please select at least one digital twin persona to generate feedback.")
    else:
        st.markdown("### 📋 Feedback Summary")
        
        # Construct the testing material
        if testing_material and creative:
            material_for_feedback = f"{testing_material}\n\nPlease also consider the following image."
        elif testing_material:
            material_for_feedback = testing_material
        elif creative:
            material_for_feedback = "Please provide feedback on the following image."
        else:
            material_for_feedback = "No testing material provided."
        
        # Initialize feedback dictionary
        st.session_state['feedback_dict'] = {}

        # Loop through each persona and display feedback
        for persona in personas:
            st.markdown(f"#### Feedback from {persona}")
            with st.spinner(f"Generating feedback from {persona}..."):
                feedback, sentiment_data = generate_digital_twin_feedback(persona, material_for_feedback)
                if sentiment_data:
                    sentiment = sentiment_data.get("sentiment", "Neutral")
                    confidence = sentiment_data.get("confidence", "N/A")
                    
                    # Determine sentiment class for styling
                    sentiment_class = "neutral"
                    if sentiment.lower() == "positive":
                        sentiment_class = "positive"
                    elif sentiment.lower() == "negative":
                        sentiment_class = "negative"
                    
                    sentiment_label = f"Sentiment: <span class='sentiment-label {sentiment_class}'>{sentiment} ({confidence})</span>"
                    st.markdown(sentiment_label, unsafe_allow_html=True)
                    st.markdown(f"<div class='feedback-box'>{feedback}</div>", unsafe_allow_html=True)
                    st.session_state['feedback_dict'][persona] = {
                        "feedback": feedback,
                        "sentiment": sentiment,
                        "confidence": confidence
                    }
                else:
                    st.markdown(f"<div class='feedback-box'>{feedback}</div>", unsafe_allow_html=True)
                    st.session_state['feedback_dict'][persona] = {
                        "feedback": feedback,
                        "sentiment": "Error",
                        "confidence": "N/A"
                    }

        st.success("Feedback generated successfully!")

        # Download option for feedback
        if st.session_state['feedback_dict']:
            feedback_text = "\n\n".join([
                f"Feedback from {persona}:\n"
                f"Sentiment: {data['sentiment']} ({data['confidence']})\n"
                f"{data['feedback']}"
                for persona, data in st.session_state['feedback_dict'].items()
            ])
            feedback_file = BytesIO()
            feedback_file.write(feedback_text.encode())
            feedback_file.seek(0)
            st.download_button(
                label="Download Feedback as .txt",
                data=feedback_file,
                file_name="reflective_feedback.txt",
                mime="text/plain",
            )

# Optional Future Feature - Chat to Persona Placeholder
st.markdown("## 🗨️ Chat to Digital Twin (Coming Soon)")
st.text("This section will allow real-time conversation with digital twin personas.")

# Footer
st.markdown("---")
st.markdown("<div class='footer'>Built with ❤️ by Reflective - Real-world reactions, instantly delivered.</div>", unsafe_allow_html=True)