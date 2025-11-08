import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // We'll add some simple styles

// This is our backend's API URL
const API_URL = "http://127.0.0.1:8000";

// This is the "Visual Tapestry" Card
function ItemCard({ item }) {
  // Render a different style based on the item_type
  let cardStyle = "card";
  if (item.item_type === "VIDEO") cardStyle += " card-video";
  if (item.item_type === "PRODUCT") cardStyle += " card-product";

  return (
    <div className={cardStyle}>
      <span className="card-type-label">{item.item_type}</span>
      <h3>{item.title}</h3>
      <p>{item.content.substring(0, 150)}...</p>
      <a href={item.url} target="_blank" rel="noopener noreferrer">
        Visit Source
      </a>
    </div>
  );
}

function App() {
  const [items, setItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [captureUrl, setCaptureUrl] = useState("");
  const [message, setMessage] = useState("Search your brain...");

  // Function to run a search
  const runSearch = async () => {
    if (searchQuery.trim() === "") {
      setItems([]);
      setMessage("Search for something...");
      return;
    }
    try {
      const response = await axios.get(`${API_URL}/search?q=${searchQuery}`);
      if (response.data.message) {
        setItems([]);
        setMessage(response.data.message);
      } else {
        setItems(response.data);
        setMessage(`Found ${response.data.length} memories.`);
      }
    } catch (error) {
      console.error("Search failed:", error);
      setMessage("Search failed.");
    }
  };

  // Function to capture a new URL
  const runCapture = async () => {
    if (captureUrl.trim() === "") return;
    try {
      setMessage(`Capturing ${captureUrl}...`);
      const response = await axios.post(`${API_URL}/capture?url=${captureUrl}`);
      setMessage(`Captured: ${response.data.title}`);
      setCaptureUrl(""); // Clear the input
    } catch (error) {
      console.error("Capture failed:", error);
      setMessage("Capture failed. Is the URL correct?");
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Project Synapse 🧠</h1>
      </header>

      {/* --- CAPTURE SECTION --- */}
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

      {/* --- SEARCH SECTION --- */}
      <div className="action-box">
        <h2>Search Your Memories</h2>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search for 'AI'..."
        />
        <button onClick={runSearch}>Search</button>
      </div>

      {/* --- RESULTS "TAPESTRY" --- */}
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