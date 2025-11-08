from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, Annotated  # <-- Make sure Annotated is imported
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
from datetime import datetime
from pydantic import BaseModel

# -----------------------------------------------------------------
# STAGE 1: DEFINE YOUR "COGNITIVE SCHEMA" (Database)
# -----------------------------------------------------------------

class Item(SQLModel, table=True):
    """Represents a single 'memory' in the database."""
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    title: str
    content: str
    item_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

# (This class is good for other integrations, but not our bookmarklet)
class MCPIngestRequest(BaseModel):
    url: str

# -----------------------------------------------------------------
# STAGE 2: SETUP THE "BRAIN" (Database Connection)
# -----------------------------------------------------------------

sqlite_file_name = "synapse.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
UPLOADS_DIR = "uploads"

# echo=False to make logs cleaner
engine = create_engine(sqlite_url, echo=False) 

def create_db_and_tables():
    """Creates the database file and all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provides a database session for API endpoints."""
    with Session(engine) as session:
        yield session

# -----------------------------------------------------------------
# STAGE 3: "INTELLIGENT CAPTURE" PIPELINE (for URLs)
# -----------------------------------------------------------------

def analyze_and_extract(url: str):
    """
    Fetches a URL, scrapes its content, and classifies it.
    This is the core "understanding" part of the brain.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('title').get_text() if soup.find('title') else "No Title Found"
        
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
            
        content = soup.get_text(separator=' ', strip=True)
        if not content:
            content = "No readable content found."

        item_type = "ARTICLE"
        if "youtube.com" in url or "vimeo.com" in url:
            item_type = "VIDEO"
        elif "amazon.com" in url or "ebay.com" in url or "flipkart.com" in url:
            item_type = "PRODUCT"
        
        return title, content, item_type

    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return "Error", f"Could not fetch or extract content: {e}", "ERROR"

# --- NEW: BACKGROUND TASK FUNCTIONS ---

def process_and_save_url(url: str):
    """
    This is the new background task for scraping.
    It creates its OWN database session.
    """
    print(f"Background task started: processing {url}")
    with Session(engine) as session:
        existing = session.exec(select(Item).where(Item.url == url)).first()
        if existing:
            print(f"Background task: Item {url} already exists.")
            return

        title, content, item_type = analyze_and_extract(url)
        
        if item_type != "ERROR":
            db_item = Item(url=url, title=title, content=content, item_type=item_type)
            session.add(db_item)
            session.commit()
            print(f"Background task finished: Saved {title}")
        else:
            print(f"Background task failed: Could not process {url}")

def process_and_save_image(filename: str, file_contents: bytes):
    """
    This is the new background task for saving images.
    It creates its OWN database session.
    """
    print(f"Background task started: processing {filename}")
    with Session(engine) as session:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        with open(file_path, "wb") as f:
            f.write(file_contents)
            
        base_name = os.path.splitext(filename)[0]
        clean_name = base_name.replace("_", " ").replace("-", " ")
        extracted_text = f"(Simulated OCR text from image: {filename}) Keywords: {clean_name}"
        
        db_item = Item(
            url=f"/uploads/{filename}",
            title=f"Note: {filename}",
            content=extracted_text,
            item_type="NOTE"
        )
        
        session.add(db_item)
        session.commit()
        print(f"Background task finished: Saved {filename}")


# -----------------------------------------------------------------
# STAGE 4: THE "MEMORY" API (ENDPOINTS)
# -----------------------------------------------------------------

app = FastAPI(
    title="Project Synapse",
    description="The intelligent backend for your second brain.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.on_event("startup")
def on_startup_event():
    create_db_and_tables()

# --- API ENDPOINT 1: "CAPTURE" (For our UI) ---
@app.post("/capture", summary="Capture a new memory (for UI)")
def capture_url(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="The URL to capture", example="https.www.wired.com/")
):
    background_tasks.add_task(process_and_save_url, url)
    return {"message": f"Capture in progress for: {url}"}

# --- API ENDPOINT 3: "CAPTURE IMAGE" (For our UI) ---
@app.post("/capture-image", summary="Capture a new image/note (for UI)")
async def capture_image(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    file_contents = await file.read()
    background_tasks.add_task(process_and_save_image, file.filename, file_contents)
    return {"message": f"Upload in progress for: {file.filename}"}

# --- API ENDPOINT 2: "SEARCH" (For our UI) ---
@app.get("/search", summary="Search your memories")
def search_memory(
    q: str = Query(..., description="Your natural language search query", example="AI"),
    session: Session = Depends(get_session)
):
    query = f"%{q}%"
    
    items = session.exec(
        select(Item).where(
            (Item.content.ilike(query)) | (Item.title.ilike(query))
        ).order_by(Item.created_at.desc())
    ).all()
    
    if not items:
        return {"message": "No memories found matching that query."}
    
    return items

# --- UPDATED: ENDPOINT 4: "MCP SERVER" ---
@app.post("/api/v1/ingest", summary="MCP Server: Ingest a new memory")
def mcp_ingest_url(
    background_tasks: BackgroundTasks,
    url: Annotated[str, Form()] # <-- This now correctly accepts 'x-www-form-urlencoded'
):
    """
    This is our official 'data contract' endpoint for external AI,
    bookmarklets, or other 3rd party integrations.
    """
    background_tasks.add_task(process_and_save_url, url)
    return {"status": "received", "message": f"Capture in progress for: {url}"}