import streamlit as st
import cv2
import numpy as np
import os
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

def process_image(img):
    """Process the image using OpenCV to identify bananas and their ripeness
    This is a placeholder for your custom image processing logic
    """
    # Simple placeholder function - replace with your actual image processing logic
    
    # Example results (hardcoded for demonstration)
    results = {
        "total_count": 3,
        "unripe_count": 1,
        "ripe_count": 1, 
        "overripe_count": 1,
        "detailed_analysis": "Sample image contains 3 bananas: 1 unripe (green), 1 ripe (yellow), and 1 overripe (with brown spots)."
    }
    
    return results

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
                    # Process the image locally
                    results = process_image(img)
                    
                    # Display results
                    col_total, col_unripe, col_ripe, col_overripe = st.columns(4)
                    col_total.metric("Total Bananas", results["total_count"])
                    col_unripe.metric("Unripe", results["unripe_count"])
                    col_ripe.metric("Ripe", results["ripe_count"])
                    col_overripe.metric("Overripe", results["overripe_count"])
                    
                    st.success("Analysis complete!")
                    st.subheader("Detailed Analysis")
                    st.write(results["detailed_analysis"])

if __name__ == "__main__":
    main()