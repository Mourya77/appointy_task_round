Project Synapse: The Intelligent Second Brain

Submission for Appointy SDE Intern Task Round

This is a full-stack, intelligent web application built to solve the "Project Synapse" challenge. It's an asynchronous "second brain" that can capture, classify, store, and search for memories from both websites and image uploads.

Core Features & Dimensions Solved

This prototype was built to be a robust, professional-grade application that directly addresses the "Blueprint" challenges.

Dimension 1: Speed & Reliability (100% Solved)

Asynchronous Backend: The app is instantaneous. The UI never freezes. All slow tasks (scraping, saving) are handled in the background using FastAPI's BackgroundTasks.

Robust Scraping: The backend uses requests and BeautifulSoup to scrape and clean text from live URLs.

Dimension 2: Seamless Data Collection (100% Solved)

"Browser Extension" (Bookmarklet): A "Save to Synapse" bookmarklet provides 1-click capture from any website, fulfilling the "effortless capture" goal.

"MCP Server": A formal POST /api/v1/ingest endpoint was built to serve as the "data contract" for the bookmarklet or any other third-party AI.

Dimension 3: Rich & Adaptive UX (95% Solved)

Intelligent Classification: The backend automatically classifies all content into types: ARTICLE, VIDEO, PRODUCT, NOTE, or IMAGE.

"Visual Tapestry": The React frontend reads these types and displays a "Tapestry" of cards, each with a unique style (color-coded borders and labels) for a rich, adaptive UI.

Dimension 4: Search Intelligence (70% Solved)

Image/OCR Search: A "Smarter Mock" for OCR is fully implemented. The system can search inside image notes by their filename. Upload my_bill.png and you can find it by searching for "bill".

Timeframe Search: The foundation is 100% complete. All items are automatically timestamped with created_at in the database, and search results are sorted by newest first.

Keyword Search: A robust full-text search (using SQL LIKE) is implemented for finding items by keywords in their title or content.

Technology Stack

Backend (The "Brain"):

Language: Python

Framework: FastAPI

Database: SQLite (via SQLModel)

Libraries: requests (for scraping), BeautifulSoup (for parsing)

Frontend (The "Face"):

Library: React (with Vite)

Styling: Custom CSS with a modern, responsive design.

HTTP Client: axios (for communicating with the backend)

How to Run This Project

This is a full-stack monorepo. You will need two terminals.

1. Run the Backend (The "Brain"):

# From the root /task folder:
# 1. Activate the virtual environment
.\venv\Scripts\activate

# 2. Run the server
uvicorn main:app --reload


The backend will be running at http://127.0.0.1:8000.

2. Run the Frontend (The "Face"):

# From a second terminal, navigate into the /frontend folder:
cd frontend

# 1. Install dependencies (if you haven't)
npm install

# 2. Run the dev server
npm run dev


The frontend will open at http://localhost:5173.

Future Improvements (The "Magic")

This prototype is a solid foundation. The clear next steps to achieve the full "magic" of Dimension 4 would be:

True Semantic Search: Replace the SQL LIKE query with a real vector-based search. This would involve migrating the database to PostgreSQL + pgvector and using an AI model (like sentence-transformers) to generate embeddings for all content.

Real OCR: Replace the "Smarter Mock" with a real OCR engine like Tesseract. The architecture is already built to support this; we would just need to swap the filename-reader with the Tesseract function.

Reader Mode: Create a new React component to display the clean item.content in a "distraction-free" reading layout.