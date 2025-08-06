import feedparser
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# List of RSS feed URLs
rss_feeds = {
    "nyt": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "guardian": "https://www.theguardian.com/world/rss",
    "clone": "https://clone.fyi/rss.xml"
}

def fetch_feeds():
    all_items = []

    for url in rss_feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            all_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", ""),
                "source": feed.feed.title
            })
    
    # Sort by published date (if available)
    all_items.sort(key=lambda x: x["published"], reverse=True)
    return all_items

@app.get("/feeds")
def get_feeds():
    items = fetch_feeds()
    return JSONResponse(content=items)

@app.post("/add_feed", status_code=status.HTTP_204_NO_CONTENT)
def add_feed(name, url):
    if "xml" not in url and "rss" not in url:
        return status.HTTP_400_BAD_REQUEST
    
    rss_feeds[name] = url

@app.delete("/remove_feed", status_code=status.HTTP_204_NO_CONTENT)
def remove_feed(name):
    try:
        del rss_feeds[name]
    except KeyError:
        return status.HTTP_400_BAD_REQUEST
    
class feeds(BaseModel):
    name: str

@app.get("/list_feeds", response_model=List[feeds])
def list_feeds():
    return [{"name": name} for name in rss_feeds.keys()]