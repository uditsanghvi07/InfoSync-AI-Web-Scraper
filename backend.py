from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import os
from pathlib import Path
from dotenv import load_dotenv
from models import NewsRequest
from utils import generate_broadcast_news_free, tts_to_audio
from news_scraper import NewsScraper
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
load_dotenv()

@app.post("/generate-news-audio")
async def generate_news_audio(request: NewsRequest):
    try:
        results = {}
        
        # Scrape news if requested
        if request.source_type in ["news", "both"]:
            try:
                logger.info(f"Scraping news for topics: {request.topics}")
                news_scraper = NewsScraper()
                results["news"] = await news_scraper.scrape_news(request.topics)
            except Exception as e:
                logger.error(f"News scraping error: {str(e)}")
                results["news"] = {"news_analysis": {topic: "" for topic in request.topics}}
        
        # Scrape Reddit if requested
        if request.source_type in ["reddit", "both"]:
            try:
                logger.info(f"Scraping Reddit for topics: {request.topics}")
                from reddit_scraper import scrape_reddit_topics
                results["reddit"] = await scrape_reddit_topics(request.topics)
            except Exception as e:
                logger.error(f"Reddit scraping error: {str(e)}")
                results["reddit"] = {"reddit_analysis": {topic: "" for topic in request.topics}}
        
        # Use available data or defaults
        news_data = results.get("news", {"news_analysis": {}})
        reddit_data = results.get("reddit", {"reddit_analysis": {}})
        
        logger.info("Generating broadcast news...")
        news_summary = generate_broadcast_news_free(
            news_data=news_data,
            reddit_data=reddit_data,
            topics=request.topics
        )
        
        if not news_summary or news_summary.strip() == "":
            raise HTTPException(status_code=500, detail="Failed to generate news summary")
        
        logger.info("Converting text to audio...")
        audio_path = tts_to_audio(text=news_summary)
        
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            logger.info(f"Audio generated successfully: {audio_path}")
            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "attachment; filename=news-summary.mp3"}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio file")
    
    except HTTPException as http_e:
        logger.error(f"HTTP Error: {http_e.detail}")
        raise http_e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )