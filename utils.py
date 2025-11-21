from urllib.parse import quote_plus
from dotenv import load_dotenv
import requests
import os
from fastapi import HTTPException
from bs4 import BeautifulSoup
import ollama
from datetime import datetime
from pathlib import Path
from gtts import gTTS

load_dotenv()

class MCPOverloadedError(Exception):
    """Custom exception for MCP service overloads"""
    pass


def generate_valid_news_url(keyword: str) -> str:
    """
    Generate a Google News search URL for a keyword with optional sorting by latest
    
    Args:
        keyword: Search term to use in the news search
        
    Returns:
        str: Constructed Google News search URL
    """
    q = quote_plus(keyword)
    return f"https://news.google.com/search?q={q}&tbs=sbd:1"


def generate_news_urls_to_scrape(list_of_keywords):
    valid_urls_dict = {}
    for keyword in list_of_keywords:
        valid_urls_dict[keyword] = generate_valid_news_url(keyword)
    
    return valid_urls_dict


def scrape_with_brightdata(url: str) -> str:
    """Scrape a URL using BrightData"""
    headers = {
        "Authorization": f"Bearer {os.getenv('BRIGHTDATA_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "zone": os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE'),
        "url": url,
        "format": "raw"
    }
    
    try:
        response = requests.post("https://api.brightdata.com/request", json=payload, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"BrightData error: {str(e)}")


def clean_html_to_text(html_content: str) -> str:
    """Clean HTML content to plain text"""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n")
    return text.strip()


def extract_headlines(cleaned_text: str) -> str:
    """
    Extract and concatenate headlines from cleaned news text content.
    
    Args:
        cleaned_text: Raw text from news page after HTML cleaning
        
    Returns:
        str: Combined headlines separated by newlines
    """
    headlines = []
    current_block = []
    
    # Split text into lines and remove empty lines
    lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
    
    # Process lines to find headline blocks
    for line in lines:
        if line == "More":
            if current_block:
                # First line of block is headline
                headlines.append(current_block[0])
                current_block = []
        else:
            current_block.append(line)
    
    # Add any remaining block at end of text
    if current_block:
        headlines.append(current_block[0])
    
    return "\n".join(headlines)


def summarize_with_ollama(headlines) -> str:
    """Summarize content using Ollama"""
    prompt = f"""You are my personal news editor. Summarize these headlines into a TV news script for me, focus on important headlines and remember that this text will be converted to audio:
    So no extra stuff other than text which the podcaster/newscaster should read, no special symbols or extra information in between and of course no preamble please.
    {headlines}
    News Script:"""

    try:
        # Direct API call instead of client
        import requests
        import json
        
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")


def generate_broadcast_news_free(news_data, reddit_data, topics):
    """Generate broadcast news using Ollama (FREE alternative to Anthropic)"""
    system_prompt = """You are a professional news anchor writing a broadcast script. Create a natural, engaging news report.

RULES:
- Write clear, conversational paragraphs as if speaking on air
- Remove all Reddit usernames and platform references
- Clean up any awkward formatting or special characters
- Make transitions smooth between topics
- Keep sentences short and punchy (good for speech)
- NO asterisks, hyphens, or formatting symbols
- NO introductions or preambles
- Just pure, readable news script

Each topic should sound natural when read aloud."""

    try:
        import requests
        
        topic_blocks = []
        for topic in topics:
            news_content = news_data.get("news_analysis", {}).get(topic, "") if news_data else ''
            reddit_content = reddit_data.get("reddit_analysis", {}).get(topic, "") if reddit_data else ''
            
            content_parts = []
            if news_content and news_content.strip():
                content_parts.append(f"News: {news_content}")
            if reddit_content and reddit_content.strip():
                content_parts.append(f"Discussion: {reddit_content}")
            
            if content_parts:
                topic_blocks.append(f"Topic: {topic}\n" + "\n".join(content_parts))

        if not topic_blocks:
            return "No content available to generate news script."

        user_prompt = "Create a news broadcast script from this content:\n\n" + "\n\n".join(topic_blocks)

        # Use Ollama via direct API call
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": "llama3.2",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 2000
                }
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()['response'].strip()
        
        # Clean up any remaining artifacts
        result = result.replace("**", "").replace("##", "").replace("--", " ")
        return result

    except Exception as e:
        raise e


def tts_to_audio(text: str, language: str = 'en') -> str:
    """
    Convert text to speech using gTTS (Google Text-to-Speech) - FREE
    
    Args:
        text: Input text to convert
        language: Language code (default: 'en')
    
    Returns:
        str: Path to saved audio file
    """
    try:
        # Ensure output directory exists
        audio_dir = Path("audio")
        audio_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = audio_dir / f"tts_{timestamp}.mp3"
        
        # Create TTS object and save
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(filename))
        
        return str(filename)
    except Exception as e:
        print(f"gTTS Error: {str(e)}")
        return None


def summarize_with_anthropic_news_script(api_key: str, headlines: str) -> str:
    """
    Summarize multiple news headlines into a TTS-friendly broadcast news script using Ollama (FREE)
    """
    system_prompt = """
You are my personal news editor and scriptwriter for a news podcast. Your job is to turn raw headlines into a clean, professional, and TTS-friendly news script.

The final output will be read aloud by a news anchor or text-to-speech engine. So:
- Do not include any special characters, emojis, formatting symbols, or markdown.
- Do not add any preamble or framing like "Here's your summary" or "Let me explain".
- Write in full, clear, spoken-language paragraphs.
- Keep the tone formal, professional, and broadcast-style — just like a real TV news script.
- Focus on the most important headlines and turn them into short, informative news segments that sound natural when spoken.
- Start right away with the actual script, using transitions between topics if needed.

Remember: Your only output should be a clean script that is ready to be read out loud.
"""

    try:
        import requests
        
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": "llama3.2",
                "prompt": f"{system_prompt}\n\nHeadlines to summarize:\n{headlines}",
                "stream": False
            },
            timeout=300
        )
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")