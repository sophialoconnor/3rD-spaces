from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz
import urllib.parse
from fake_useragent import UserAgent
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Dublin Cultural Events Search Engine", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# User agent for web scraping
ua = UserAgent()

# Define Models
class WebsiteContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    url: str
    source_website: str
    event_date: Optional[datetime] = None
    venue: Optional[str] = None
    description: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    content_type: str = "article"  # article, event, venue_info
    tags: List[str] = []

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    content_type: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    title: str
    description: str
    url: str
    source_website: str
    relevance_score: float
    content_type: str
    venue: Optional[str] = None
    event_date: Optional[datetime] = None
    tags: List[str] = []

class ScrapeStatus(BaseModel):
    status: str
    message: str
    scraped_count: int
    last_scraped: Optional[datetime] = None

# Dublin websites to scrape
DUBLIN_WEBSITES = [
    "https://lovin.ie/",
    "https://www.alternativedublincity.com/",
    "https://charfoodguide.com/category/dublins-food-and-drink-culture-explored/",
    "https://www.totallydublin.ie/",
    "https://districtmagazine.ie/",
    "https://www.bordgaisenergytheatre.ie/",
    "https://www.3olympia.ie/",
    "https://www.theacademydublin.com/",
    "https://www.whelanslive.com/events/",
    "https://imma.ie/",
    "https://www.nationalgallery.ie/",
    "https://www.nch.ie/",
    "https://www.riam.ie/whats-on",
    "https://hughlane.ie/whats-on/",
    "https://rhagallery.ie/whats-on/",
    "https://www.gaietytheatre.ie/events/",
    "https://www.fringefest.com/festival/whats-on",
    "https://chesterbeatty.ie/exhibitions/",
    "https://universitytimes.ie/",
    "https://miscmagazine.ie/"
]

async def scrape_website(session: aiohttp.ClientSession, url: str) -> List[WebsiteContent]:
    """Scrape content from a single website"""
    try:
        headers = {'User-Agent': ua.random}
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status != 200:
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract content based on common patterns
            articles = []
            
            # Try to find article elements
            article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'(post|article|event|news|content)', re.I))
            
            if not article_elements:
                # Fallback to finding content with common patterns
                article_elements = soup.find_all('div', class_=re.compile(r'(card|item|entry|story)', re.I))
            
            for element in article_elements[:10]:  # Limit to 10 articles per site
                try:
                    # Extract title
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'(title|heading|name)', re.I))
                    if not title_elem:
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if len(title) < 10:  # Skip very short titles
                        continue
                    
                    # Extract description/content
                    content_elem = element.find(['p', 'div'], class_=re.compile(r'(excerpt|summary|description|content)', re.I))
                    if not content_elem:
                        content_elem = element.find('p')
                    
                    description = content_elem.get_text(strip=True) if content_elem else ""
                    
                    # Extract link
                    link_elem = element.find('a')
                    if link_elem and link_elem.get('href'):
                        article_url = urllib.parse.urljoin(url, link_elem.get('href'))
                    else:
                        article_url = url
                    
                    # Extract venue and event date if possible
                    venue = None
                    event_date = None
                    
                    # Look for venue information
                    venue_elem = element.find(text=re.compile(r'(venue|location|@)', re.I))
                    if venue_elem:
                        venue = venue_elem.strip()[:100]
                    
                    # Determine content type
                    content_type = "article"
                    if any(keyword in title.lower() for keyword in ['event', 'gig', 'concert', 'show', 'exhibition']):
                        content_type = "event"
                    
                    # Extract tags
                    tags = []
                    if 'music' in title.lower() or 'gig' in title.lower():
                        tags.append('music')
                    if 'art' in title.lower() or 'gallery' in title.lower():
                        tags.append('art')
                    if 'food' in title.lower() or 'restaurant' in title.lower():
                        tags.append('food')
                    if 'theatre' in title.lower() or 'play' in title.lower():
                        tags.append('theatre')
                    
                    article = WebsiteContent(
                        title=title,
                        content=description,
                        url=article_url,
                        source_website=url,
                        description=description[:300],
                        venue=venue,
                        event_date=event_date,
                        content_type=content_type,
                        tags=tags
                    )
                    articles.append(article)
                    
                except Exception as e:
                    logging.warning(f"Error processing article element: {e}")
                    continue
            
            return articles
            
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return []

async def scrape_all_websites():
    """Scrape all Dublin websites"""
    all_content = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in DUBLIN_WEBSITES:
            tasks.append(scrape_website(session, url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_content.extend(result)
            else:
                logging.error(f"Scraping error: {result}")
    
    return all_content

def calculate_relevance_score(content: WebsiteContent, query: str) -> float:
    """Calculate relevance score for search results"""
    query_lower = query.lower()
    title_lower = content.title.lower()
    description_lower = content.description.lower()
    
    # Title match (highest weight)
    title_score = fuzz.partial_ratio(query_lower, title_lower) / 100 * 0.4
    
    # Description match
    desc_score = fuzz.partial_ratio(query_lower, description_lower) / 100 * 0.3
    
    # Tag match
    tag_score = 0
    for tag in content.tags:
        if query_lower in tag.lower():
            tag_score += 0.2
    
    # Venue match
    venue_score = 0
    if content.venue and query_lower in content.venue.lower():
        venue_score = 0.1
    
    return min(title_score + desc_score + tag_score + venue_score, 1.0)

@api_router.get("/")
async def root():
    return {"message": "Dublin Cultural Events Search Engine API"}

@api_router.post("/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger scraping of all Dublin websites"""
    background_tasks.add_task(perform_scrape)
    return {"message": "Scraping started in background"}

async def perform_scrape():
    """Perform the actual scraping and store in database"""
    try:
        logging.info("Starting web scraping...")
        content_list = await scrape_all_websites()
        
        # Store in database
        stored_count = 0
        for content in content_list:
            # Check if content already exists
            existing = await db.scraped_content.find_one({"url": content.url})
            if not existing:
                await db.scraped_content.insert_one(content.dict())
                stored_count += 1
        
        # Update scrape status
        await db.scrape_status.replace_one(
            {"_id": "main"},
            {
                "_id": "main",
                "status": "completed",
                "message": f"Successfully scraped {stored_count} new articles",
                "scraped_count": stored_count,
                "last_scraped": datetime.utcnow()
            },
            upsert=True
        )
        
        logging.info(f"Scraping completed. Stored {stored_count} new articles.")
        
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        await db.scrape_status.replace_one(
            {"_id": "main"},
            {
                "_id": "main",
                "status": "failed",
                "message": f"Scraping failed: {str(e)}",
                "scraped_count": 0,
                "last_scraped": datetime.utcnow()
            },
            upsert=True
        )

@api_router.get("/scrape/status", response_model=ScrapeStatus)
async def get_scrape_status():
    """Get current scraping status"""
    status = await db.scrape_status.find_one({"_id": "main"})
    if not status:
        return ScrapeStatus(
            status="never_run",
            message="Scraping has never been run",
            scraped_count=0
        )
    
    return ScrapeStatus(
        status=status.get("status", "unknown"),
        message=status.get("message", ""),
        scraped_count=status.get("scraped_count", 0),
        last_scraped=status.get("last_scraped")
    )

@api_router.post("/search", response_model=List[SearchResult])
async def search_content(search_query: SearchQuery):
    """Search through scraped content"""
    try:
        # Build query filter
        query_filter = {}
        if search_query.content_type:
            query_filter["content_type"] = search_query.content_type
        
        # Get all matching content
        cursor = db.scraped_content.find(query_filter)
        all_content = await cursor.to_list(length=None)
        
        if not all_content:
            return []
        
        # Convert MongoDB documents to proper format and calculate relevance scores
        scored_results = []
        for content_dict in all_content:
            # Remove MongoDB's _id field to avoid serialization issues
            if '_id' in content_dict:
                del content_dict['_id']
            
            # Convert datetime objects to ISO format strings
            if 'scraped_at' in content_dict and content_dict['scraped_at']:
                content_dict['scraped_at'] = content_dict['scraped_at'].isoformat()
            if 'event_date' in content_dict and content_dict['event_date']:
                content_dict['event_date'] = content_dict['event_date'].isoformat()
            
            content = WebsiteContent(**content_dict)
            score = calculate_relevance_score(content, search_query.query)
            
            if score > 0.1:  # Minimum relevance threshold
                result = SearchResult(
                    id=content.id,
                    title=content.title,
                    description=content.description,
                    url=content.url,
                    source_website=content.source_website,
                    relevance_score=score,
                    content_type=content.content_type,
                    venue=content.venue,
                    event_date=content.event_date,
                    tags=content.tags
                )
                scored_results.append(result)
        
        # Sort by relevance score
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top results
        return scored_results[:search_query.limit]
        
    except Exception as e:
        logging.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@api_router.get("/content/stats")
async def get_content_stats():
    """Get statistics about scraped content"""
    try:
        total_count = await db.scraped_content.count_documents({})
        
        # Count by content type
        type_counts = await db.scraped_content.aggregate([
            {"$group": {"_id": "$content_type", "count": {"$sum": 1}}}
        ]).to_list(length=None)
        
        # Count by source website
        source_counts = await db.scraped_content.aggregate([
            {"$group": {"_id": "$source_website", "count": {"$sum": 1}}}
        ]).to_list(length=None)
        
        return {
            "total_articles": total_count,
            "by_type": {item["_id"]: item["count"] for item in type_counts},
            "by_source": {item["_id"]: item["count"] for item in source_counts}
        }
        
    except Exception as e:
        logging.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

@api_router.get("/content/recent")
async def get_recent_content():
    """Get most recently scraped content"""
    try:
        recent_content = await db.scraped_content.find().sort("scraped_at", -1).limit(20).to_list(length=None)
        
        # Convert MongoDB documents to proper format
        formatted_content = []
        for content in recent_content:
            # Remove MongoDB's _id field to avoid serialization issues
            if '_id' in content:
                del content['_id']
            
            # Convert datetime objects to ISO format strings
            if 'scraped_at' in content and content['scraped_at']:
                content['scraped_at'] = content['scraped_at'].isoformat()
            if 'event_date' in content and content['event_date']:
                content['event_date'] = content['event_date'].isoformat()
            
            formatted_content.append(content)
        
        return formatted_content
    except Exception as e:
        logging.error(f"Recent content error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent content")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Initialize scraping on startup
@app.on_event("startup")
async def startup_event():
    """Initialize scraping on startup"""
    asyncio.create_task(perform_scrape())
    logger.info("Dublin Cultural Events Search Engine started")