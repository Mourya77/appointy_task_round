import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = "http://127.0.0.1:8000";

// --- UPDATED: The Bookmarklet Code ---
const bookmarkletCode = `
  javascript:(
    function() {
      const url = window.location.href;
      fetch('${API_URL}/api/v1/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'url=' + encodeURIComponent(url)
      })
      .then(response => response.json())
      .then(data => {
        alert('Synapse capture started for: ' + url);
        console.log(data);
      })
      .catch(error => {
        console.error('Synapse capture failed:', error);
        alert('Synapse capture failed!');
      });
    }
  )();
`.replace(/\s+/g, ' '); // Minify it

function formatTimestamp(isoString) {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

// --- UPDATED: ItemCard ---
function ItemCard({ item }) {
  let cardStyle = "card";
  if (item.item_type === "VIDEO") cardStyle += " card-video";
  if (item.item_type === "PRODUCT") cardStyle += " card-product";
  if (item.item_type === "NOTE") cardStyle += " card-note";
  if (item.item_type === "IMAGE") cardStyle += " card-image";

  const isViewableUpload = item.item_type === "NOTE" || item.item_type === "IMAGE";
  const sourceUrl = isViewableUpload
    ? `${API_URL}${item.url}`
    : item.url;

  return (
    <div className={cardStyle}>
      <span className="card-type-label">{item.item_type}</span>
      <h3>{item.title}</h3>
      <p className="card-content">{item.content.substring(0, 150)}...</p>

      <p className="card-timestamp">
        Saved on: {formatTimestamp(item.created_at)}
      </p>

      <a href={sourceUrl} target="_blank" rel="noopener noreferrer">
        {isViewableUpload ? "View Upload" : "Visit Source"}
      </a>
    </div>
  );
}
// --- END OF UPDATED ItemCard ---

function App() {
  const [fileToUpload, setFileToUpload] = useState(null);
  const [items, setItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [captureUrl, setCaptureUrl] = useState("");
  const [message, setMessage] = useState("Search your brain...");
  const [copyButtonText, setCopyButtonText] = useState("Copy Code");

  useEffect(() => {
    runSearch(true);
  }, []);

  const runSearch = async (isRefresh = false) => {
    let query = searchQuery.trim();
    if (isRefresh) {
      query = "";
    }

    if (query === "" && !isRefresh) {
      setItems([]);
      setMessage("Search for something...");
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/search?q=${query}`);
      if (response.data.message) {
        setItems([]);
        setMessage(response.data.message);
      } else {
        setItems(response.data);
        if (!isRefresh) {
          setMessage(`Found ${response.data.length} memories.`);
        } else {
          setMessage(`Displaying ${response.data.length} total memories.`);
        }
      }
    } catch (error) {
      console.error("Search failed:", error);
      setMessage("Search failed.");
    }
  };

  const runCapture = async () => {
    if (captureUrl.trim() === "") return;
    try {
      const response = await axios.post(`${API_URL}/capture?url=${captureUrl}`);
      setMessage(response.data.message);
      setCaptureUrl("");
    } catch (error) {
      console.error("Capture failed:", error);
      setMessage("Capture failed. Is the URL correct?");
    }
  };

  const runImageCapture = async () => {
    if (!fileToUpload) return;

    const formData = new FormData();
    formData.append("file", fileToUpload);

    try {
      const response = await axios.post(`${API_URL}/capture-image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage(response.data.message);
      setFileToUpload(null);
      document.getElementById('file-input').value = null;
    } catch (error) {
      console.error("Image capture failed:", error);
      setMessage("Image capture failed.");
    }
  };

  const copyBookmarklet = () => {
    navigator.clipboard.writeText(bookmarkletCode)
      .then(() => {
        setCopyButtonText("Copied!");
        setTimeout(() => setCopyButtonText("Copy Code"), 2000);
      })
      .catch(err => {
        console.error('Failed to copy: ', err);
      });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Project Synapse 🧠</h1>
      </header>

      <div className="action-box bookmarklet-box">
        <h2>Capture from Anywhere (Bookmarklet)</h2>
        <p>
          **Manual Install:** 1. Right-click your bookmarks bar, select "Add Page...".
          2. For "Name", type <strong>Save to Synapse</strong>.
          3. For "URL", copy the text below and paste it there.
        </p>
        <textarea
          className="bookmarklet-code"
          value={bookmarkletCode}
          readOnly
        />
        <button
          onClick={copyBookmarklet}
          style={{ marginTop: "10px", backgroundColor: "#28a745" }}
        >
          {copyButtonText}
        </button>
      </div>

      <div className="action-box">
        <h2>Capture New Memory</h2>
        <input
          type="text"
          value={captureUrl}
          onChange={(e) => setCaptureUrl(e.target.value)}
          placeholder="Paste a URL to capture..."
        />
        <button onClick={runCapture}>Capture</button>
      </div>

      <div className="action-box">
        <h2>Capture Image Note (OCR)</h2>
        <input
          type="file"
          id="file-input"
          onChange={(e) => setFileToUpload(e.target.files[0])}
        />
        <button onClick={runImageCapture}>Upload Note</button>
      </div>

      <div className="action-box">
        <h2>Search Your Memories</h2>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search for articles, bills, or notes..."
        />
        <button onClick={() => runSearch(false)}>Search</button>
        <button onClick={() => runSearch(true)} style={{ marginLeft: "10px", backgroundColor: "#6c757d" }}>Refresh</button>
      </div>

      <div className="tapestry-container">
        <h2>{message}</h2>
        <div className="grid">
          {items.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;