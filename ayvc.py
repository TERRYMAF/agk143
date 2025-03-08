import streamlit as st
import cv2
import numpy as np
import os
from io import BytesIO
import json
import base64
import requests

# Page configuration
st.set_page_config(
    page_title="Banana Ripeness Detector",
    page_icon="🍌",
    layout="wide"
)

# App title and description
st.title("🍌 Banana Ripeness Detector")
st.markdown("""Take a picture or upload an image to analyze bananas and their ripeness levels""")

def capture_image():
    """Capture image from webcam"""
    img_file_buffer = st.camera_input("Take a picture of bananas")
    if img_file_buffer is not None:
        # Convert to OpenCV format
        bytes_data = img_file_buffer.getvalue()
        img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        return img, img_file_buffer
    return None, None

def upload_image():
    """Upload image from device"""
    uploaded_file = st.file_uploader("Or upload an image", type=['jpg', 'jpeg', 'png'])
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        return img, uploaded_file
    return None, None

def encode_image_to_base64(image_file):
    """Encode image to base64 string from file buffer"""
    try:
        if isinstance(image_file, BytesIO):
            return base64.b64encode(image_file.getvalue()).decode('utf-8')
        return base64.b64encode(image_file).decode('utf-8')
    except Exception as e:
        st.error(f"Error encoding image: {str(e)}")
        return None

def get_secret(key, default=None):
    """Get a value from streamlit secrets with a default fallback"""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

def analyze_image_with_vision_api(image_file):
    """Analyze image using Vision API from secrets configuration"""
    # Encode image to base64
    base64_image = encode_image_to_base64(image_file)
    if not base64_image:
        return None
    
    # Get settings from secrets.toml
    endpoint = get_secret("azure_endpoint")
    api_key = get_secret("azure_api_key")
    model = get_secret("azure_model", "EDM-mini")
    api_version = get_secret("api_version", "2024-02-15-preview")
    
    # Check if required settings are available
    if not endpoint or not api_key:
        st.error("Missing API configuration. Please check your secrets.toml file.")
        return None
    
    # Ensure endpoint has the right format
    if not endpoint.startswith(('http://', 'https://')):
        endpoint = 'https://' + endpoint
    endpoint = endpoint.rstrip('/')
    
    # Construct API URL
    api_url = f"{endpoint}/openai/deployments/{model}/chat/completions?api-version={api_version}"
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    # Prepare payload
    payload = {
        "messages": [
            {"role": "system", "content": "You are a computer vision assistant specialized in detecting bananas and assessing their ripeness."},
            {"role": "user", "content": [
                {"type": "text", "text": """
                    Analyze this image and identify all bananas.
                    Count them and classify each one into one of these categories:
                    - Unripe (green)
                    - Ripe (yellow with small brown spots)
                    - Overripe (significant brown spots or black)
                    
                    Return the results in this JSON format:
                    {
                      "total_count": <number>,
                      "unripe_count": <number>,
                      "ripe_count": <number>,
                      "overripe_count": <number>,
                      "detailed_analysis": "<brief description of what you see>"
                    }
                """},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        # Make the API call
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        # Check for HTTP errors
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
            return None
        
        # Parse and return the response
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        
        # Try to parse the content as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            st.error("Failed to parse response as JSON")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error in API request")
        return None

def main():
    # Add tabs for capturing or uploading images
    tab1, tab2 = st.tabs(["📷 Capture", "📤 Upload"])
    
    with tab1:
        img, img_file = capture_image()
        source = "camera" if img is not None else None
    
    with tab2:
        if source is None:  # Only try upload if capture didn't work
            img, img_file = upload_image()
            source = "upload" if img is not None else None
    
    # Process the image if available
    if img is not None and img_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Input Image")
            st.image(img, channels="BGR", use_column_width=True)
            process_button = st.button("Process Image")
        
        with col2:
            st.subheader("Analysis Results")
            
            if process_button:
                with st.spinner("Analyzing image..."):
                    # Process the image using the API
                    results = analyze_image_with_vision_api(img_file)
                    
                    if results:
                        # Display results
                        col_total, col_unripe, col_ripe, col_overripe = st.columns(4)
                        col_total.metric("Total Bananas", results.get("total_count", 0))
                        col_unripe.metric("Unripe", results.get("unripe_count", 0))
                        col_ripe.metric("Ripe", results.get("ripe_count", 0))
                        col_overripe.metric("Overripe", results.get("overripe_count", 0))
                        
                        st.success("Analysis complete!")
                        st.subheader("Detailed Analysis")
                        st.write(results.get("detailed_analysis", "No detailed analysis available."))
                    else:
                        st.error("Failed to analyze the image. Please check your configuration and try again.")

if __name__ == "__main__":
    main()
