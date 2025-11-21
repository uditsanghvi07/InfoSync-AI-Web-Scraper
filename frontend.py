import streamlit as st
import requests
from typing import Literal
import time
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="InfoSync - Intelligent News Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    body {
        background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%);
    }
    
    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        text-align: center;
    }
    
    .header-title {
        font-size: 2.5em;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 1.1em;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 10px;
    }
    
    /* Card Styling */
    .info-card {
        background: linear-gradient(135deg, #1e293b 0%, #2d3748 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 30px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* Input Styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        color: white;
    }
    
    /* Success/Error Messages */
    .success-box {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.5);
        color: #a7f3d0;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .error-box {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.5);
        color: #fca5a5;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Stats Grid */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #2d3748 100%);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .metric-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        font-size: 0.9em;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Constants
BACKEND_URL = "http://localhost:8000"
SOURCE_TYPES = ["both", "news", "reddit"]

# Initialize session state
if 'topics' not in st.session_state:
    st.session_state.topics = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_audio' not in st.session_state:
    st.session_state.current_audio = None

# Header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">📊 InfoSync</h1>
    <p class="header-subtitle">Intelligent News & Social Media Analytics Platform</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    source_type = st.selectbox(
        "📡 Data Sources",
        options=SOURCE_TYPES,
        format_func=lambda x: {
            "both": "🌐 News + Reddit",
            "news": "📰 News Only",
            "reddit": "🔗 Reddit Only"
        }.get(x, x),
        help="Select where to pull data from"
    )
    
    st.markdown("---")
    st.markdown("### 📚 Features")
    st.markdown("""
    - 🔍 Multi-source content aggregation
    - 🤖 AI-powered summarization
    - 🎙️ Text-to-speech conversion
    - 📊 Topic analysis
    - 💾 Search history
    - ⚡ Real-time processing
    """)
    
    st.markdown("---")
    st.markdown("### 📈 Analytics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Topics Processed", len(st.session_state.history))
    with col2:
        st.metric("Total Queries", len(st.session_state.topics))

# Main content area
tab1, tab2, tab3 = st.tabs(["🎯 Generate", "📋 History", "ℹ️ About"])

# Tab 1: Generate
with tab1:
    st.markdown("### 📝 Create News Analysis")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        new_topic = st.text_input(
            "Enter a topic to analyze",
            placeholder="e.g., Artificial Intelligence, Climate Change, Technology...",
            help="Enter any topic you want to analyze from news and Reddit"
        )
    with col2:
        st.write("")
        st.write("")
        add_disabled = len(st.session_state.topics) >= 3 or not new_topic.strip()
        if st.button("➕ Add", disabled=add_disabled, use_container_width=True):
            if new_topic.strip() not in st.session_state.topics:
                st.session_state.topics.append(new_topic.strip())
                st.success(f"✅ Added: {new_topic}")
                st.rerun()
            else:
                st.warning("⚠️ Topic already added!")
    
    # Selected Topics Display
    if st.session_state.topics:
        st.markdown("### ✅ Selected Topics")
        for i, topic in enumerate(st.session_state.topics):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{i+1}. {topic}**")
            with col2:
                st.write("")
            with col3:
                if st.button("❌", key=f"remove_{i}", use_container_width=True):
                    st.session_state.topics.pop(i)
                    st.rerun()
    
    st.markdown("---")
    
    # Generation Controls
    st.markdown("### 🚀 Generate Summary")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.info("💡 Tip: Add 1-3 topics for best results")
    with col2:
        st.write("")
    with col3:
        generate_disabled = len(st.session_state.topics) == 0
        generate_button = st.button(
            "🎙️ Generate Audio",
            disabled=generate_disabled,
            use_container_width=True,
            key="generate_btn"
        )
    
    if generate_button:
        if not st.session_state.topics:
            st.error("❌ Please add at least one topic")
        else:
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            try:
                with st.spinner("🔄 Processing... This may take a minute"):
                    # Show progress
                    progress_bar = progress_placeholder.progress(0)
                    
                    status_placeholder.info("📡 Fetching data from sources...")
                    progress_bar.progress(25)
                    
                    time.sleep(0.5)
                    
                    status_placeholder.info("🤖 Generating summary with AI...")
                    progress_bar.progress(50)
                    
                    # Make API call
                    response = requests.post(
                        f"{BACKEND_URL}/generate-news-audio",
                        json={
                            "topics": st.session_state.topics,
                            "source_type": source_type
                        },
                        timeout=120
                    )
                    
                    progress_bar.progress(75)
                    status_placeholder.info("🎵 Converting to audio...")
                    
                    if response.status_code == 200:
                        progress_bar.progress(100)
                        progress_placeholder.empty()
                        status_placeholder.empty()
                        
                        st.session_state.current_audio = response.content
                        
                        # Add to history
                        st.session_state.history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "topics": st.session_state.topics.copy(),
                            "source_type": source_type
                        })
                        
                        st.success("✅ Audio generated successfully!")
                        
                        # Display audio player
                        st.markdown("### 🎧 Audio Summary")
                        st.audio(st.session_state.current_audio, format="audio/mpeg")
                        
                        # Download button
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            st.download_button(
                                "⬇️ Download MP3",
                                data=st.session_state.current_audio,
                                file_name=f"infosync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3",
                                mime="audio/mpeg",
                                use_container_width=True
                            )
                        with col2:
                            if st.button("🔄 Regenerate", use_container_width=True):
                                st.rerun()
                        
                        # Clear topics after successful generation
                        if st.button("➕ Analyze New Topics", use_container_width=True):
                            st.session_state.topics = []
                            st.session_state.current_audio = None
                            st.rerun()
                    else:
                        progress_placeholder.empty()
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
            except requests.exceptions.Timeout:
                progress_placeholder.empty()
                st.error("❌ Request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                progress_placeholder.empty()
                st.error("❌ Cannot connect to backend. Make sure the server is running on localhost:8000")
            except Exception as e:
                progress_placeholder.empty()
                st.error(f"❌ Error: {str(e)}")

# Tab 2: History
with tab2:
    st.markdown("### 📜 Search History")
    
    if st.session_state.history:
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.container():
                st.markdown(f"""
                <div class="info-card">
                    <strong>⏰ {item['timestamp']}</strong><br>
                    📌 Topics: {', '.join(item['topics'])}<br>
                    📡 Source: {item['source_type'].upper()}
                </div>
                """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.info("📭 No history yet. Generate your first summary to see it here!")

# Tab 3: About
with tab3:
    st.markdown("### 📊 About InfoSync")
    
    st.markdown("""
    **InfoSync** is an intelligent news and social media analytics platform that helps you stay informed 
    with AI-powered summaries from multiple sources.
    
    #### 🌟 Key Features
    - **Multi-Source Aggregation**: Combine news and Reddit discussions
    - **AI Summarization**: Uses advanced language models for intelligent summaries
    - **Text-to-Speech**: Convert summaries to high-quality audio
    - **Real-time Processing**: Get results instantly
    - **Search History**: Track your analysis queries
    
    #### 🔧 Technology Stack
    - **Frontend**: Streamlit
    - **Backend**: FastAPI
    - **AI Model**: Ollama (Llama 3.2)
    - **Data Sources**: Google News, Reddit
    - **Text-to-Speech**: Google Text-to-Speech (gTTS)
    
    #### 📖 How to Use
    1. Select data sources (News, Reddit, or Both)
    2. Enter topics you want to analyze
    3. Click "Generate Audio" to create a summary
    4. Listen and download the audio file
    5. Check your history to track previous analyses
    
    #### ⚠️ Requirements
    - Backend server running on localhost:8000
    - Ollama installed and running (llama3.2 model)
    - Internet connection for data fetching
    
    #### 📝 Note
    This project is perfect for your portfolio! It demonstrates:
    - Full-stack development (frontend + backend)
    - API integration
    - Async programming
    - AI/ML implementation
    - Data processing
    - Professional UI design
    """)
    
    st.markdown("---")
    st.markdown("""
    **Made with ❤️ | Open Source | Production Ready**
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255, 255, 255, 0.5); font-size: 0.9em;">
    InfoSync v1.0 | Intelligent News Analytics Platform | © 2024
</div>
""", unsafe_allow_html=True)