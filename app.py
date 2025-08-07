import feedparser
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import db
import sqlalchemy
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_feeds():
    all_items = []

    feeds = list_feeds()

    for f in feeds:
        url = f["url"]
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

class ArticleOut(BaseModel):
    timestamp: datetime
    title: str
    link: str

@app.get("/feeds")
def get_feeds():
    with db.engine.begin() as connection:
        res = connection.execute(
                    sqlalchemy.text(
                        """
                        SELECT timestamp, title, link
                        FROM articles
                        ORDER BY timestamp DESC
                        LIMIT 100
                        """
                    )
                )
        
        rows = res.mappings().all() 
        
        return [ArticleOut(**row) for row in rows] 

@app.get("/update_feeds")
def update_feeds():
    items = fetch_feeds()

    # Get feed name → id mapping
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT id, name FROM feeds"))
        feed_map = {row["name"]: row["id"] for row in result.mappings()}

    #add deduping

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("""INSERT INTO articles (timestamp, title, link, feed_source)
                    VALUES (:timestamp, :title, :url, :source)"""),
            [{
                "timestamp": item.get("published", ""),
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "source": feed_map[item.get("source", "")]
            } for item in items]
        )

    return JSONResponse(content=items)

@app.post("/add_feed", status_code=status.HTTP_204_NO_CONTENT)
def add_feed(name, url):
    
    try:
        feed = feedparser.parse(url)
    except:
        return status.HTTP_400_BAD_REQUEST
    
    source = feed.feed.title
    
    with db.engine.begin() as connection:
        connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO feeds (name, user_name, url)
                        VALUES (:name, :uname, :url)
                        """
                    ), [{"name": source, "uname": name, "url": url}]
                )


@app.delete("/remove_feed", status_code=status.HTTP_204_NO_CONTENT)
def remove_feed(name):
    with db.engine.begin() as connection:
        connection.execute(
                    sqlalchemy.text(
                        """
                        DELETE FROM feeds
                        WHERE user_name = :name
                        """
                    ), [{"name": name}]
                )
    
class feeds(BaseModel):
    user_name: str
    url: str

@app.get("/list_feeds", response_model=List[feeds])
def list_feeds():
    with db.engine.begin() as connection:
        res = connection.execute(sqlalchemy.text("""SELECT user_name, url
                                                    FROM feeds"""))
        
        rows = res.mappings().all()
        
        return rows