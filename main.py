from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Depends, HTTPException, Query

# -----------------------------------------------------------------
# STAGE 1: DEFINE YOUR "COGNITIVE SCHEMA" (Database)
# -----------------------------------------------------------------

class Item(SQLModel, table=True):
    """Represents a single 'memory' in the database."""
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    title: str
    content: str  # The full scraped text
    item_type: str  # 'ARTICLE', 'VIDEO', 'PRODUCT', etc.

# -----------------------------------------------------------------
# STAGE 2: SETUP THE "BRAIN" (Database Connection)
# -----------------------------------------------------------------

sqlite_file_name = "synapse.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=True is great for debugging, it prints the SQL commands
engine = create_engine(sqlite_url, echo=True) 

def create_db_and_tables():
    """Creates the database file and all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provides a database session for API endpoints."""
    with Session(engine) as session:
        yield session

# -----------------------------------------------------------------
# STAGE 3: "INTELLIGENT CAPTURE" PIPELINE
# -----------------------------------------------------------------

def analyze_and_extract(url: str):
    """
    Fetches a URL, scrapes its content, and classifies it.
    This is the core "understanding" part of the brain.
    """
    try:
        # 1. Capture: Fetch the content
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status() # Raise an error on bad responses (4xx, 5xx)
        
        # 2. Understand: Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 3. Extract Title
        title = soup.find('title').get_text() if soup.find('title') else "No Title Found"
        
        # 4. Extract Content
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
            
        content = soup.get_text(separator=' ', strip=True)
        if not content:
            content = "No readable content found."

        # 5. Classify
        item_type = "ARTICLE" # Default
        if "youtube.com" in url or "vimeo.com" in url:
            item_type = "VIDEO"
        elif "amazon.com" in url or "ebay.com" in url or "flipkart.com" in url:
            item_type = "PRODUCT"
        
        return title, content, item_type

    except requests.exceptions.RequestException as e:
        print(f"Error extracting {url}: {e}")
        return "Error", f"Could not fetch or extract content: {e}", "ERROR"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "Error", f"An unexpected error occurred: {e}", "ERROR"

# -----------------------------------------------------------------
# STAGE 4: THE "MEMORY" API (ENDPOINTS)
# -----------------------------------------------------------------

app = FastAPI(
    title="Project Synapse",
    description="The intelligent backend for your second brain.",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup_event():
    # This creates the DB and tables when the app starts
    create_db_and_tables()

# --- API ENDPOINT 1: "CAPTURE" ---
@app.post("/capture", response_model=Item, summary="Capture a new memory")
def capture_url(
    url: str = Query(..., description="The URL to capture", example="https://www.wired.com/"),
    session: Session = Depends(get_session)
):
    """
    Captures, analyzes, scrapes, and stores a new item from a URL.
    """
    # 1. Check if we already have it
    existing = session.exec(select(Item).where(Item.url == url)).first()
    if existing:
        return existing

    # 2. Call your "Understand" pipeline
    title, content, item_type = analyze_and_extract(url)
    
    if item_type == "ERROR":
        raise HTTPException(status_code=400, detail=content)

    # 3. Store in the "Brain"
    db_item = Item(url=url, title=title, content=content, item_type=item_type)
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    
    return db_item

# --- API ENDPOINT 2: "SEARCH" ---
@app.get("/search", summary="Search your memories")
def search_memory(
    q: str = Query(..., description="Your natural language search query", example="AI"),
    session: Session = Depends(get_session)
):
    """
    Searches the brain for a query 'q'.
    This is a full-text search on the 'content' and 'title'.
    """
    query = f"%{q}%" # The % is a wildcard
    
    items = session.exec(
        select(Item).where(
            (Item.content.ilike(query)) | (Item.title.ilike(query))
        )
    ).all()
    
    if not items:
        return {"message": "No memories found matching that query."}
    
    return items