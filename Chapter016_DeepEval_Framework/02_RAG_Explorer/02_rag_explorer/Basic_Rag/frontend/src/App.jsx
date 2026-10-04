import React, { useState } from 'react';
import IngestionPanel from './components/IngestionPanel';
import QueryPanel from './components/QueryPanel';

function App() {
  const [ingested, setIngested] = useState(false);

  return (
    <>
      <header>
        <h1>RAG Explorer</h1>
        <p className="subtitle">Retrieval-Augmented Generation using ChromaDB, Nomic, and Groq</p>
      </header>

      <main className="app-container">
        <IngestionPanel 
          onIngestComplete={() => setIngested(true)} 
          isIngested={ingested}
        />
        
        <QueryPanel 
          isIngested={ingested} 
        />
      </main>
    </>
  );
}

export default App;
