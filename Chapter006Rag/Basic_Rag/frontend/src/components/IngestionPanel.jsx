import React, { useState } from 'react';
import axios from 'axios';
import { Database, FileText, Layers, Link, Loader2, CheckCircle2 } from 'lucide-react';

const IngestionPanel = ({ onIngestComplete, isIngested }) => {
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [error, setError] = useState(null);
  const [chunkCount, setChunkCount] = useState(0);

  const handleIngest = async () => {
    setLoading(true);
    setActiveStep(0); // Reading
    setError(null);
    
    try {
      // Simulate micro-steps for better UI feedback
      setTimeout(() => setActiveStep(1), 1000); // Chunking
      setTimeout(() => setActiveStep(2), 2000); // Embedding
      setTimeout(() => setActiveStep(3), 3500); // Storing

      const response = await axios.post('http://localhost:5000/api/ingest');
      
      if (response.data.success) {
        setChunkCount(response.data.chunks);
        setActiveStep(4); // Complete
        setTimeout(() => {
          setLoading(false);
          onIngestComplete();
        }, 1000);
      } else {
        throw new Error(response.data.message);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.message || err.message || "Failed to ingest PDF");
      setLoading(false);
      setActiveStep(-1);
    }
  };

  const steps = [
    { icon: <FileText size={18} />, label: "Reading PDF Document" },
    { icon: <Layers size={18} />, label: "Chunking Text Content" },
    { icon: <Link size={18} />, label: "Generating Ollama Embeddings" },
    { icon: <Database size={18} />, label: "Storing in ChromaDB" },
  ];

  return (
    <section className="panel">
      <div className="panel-header">
        <Database className="text-accent" />
        <h2>Data Ingestion</h2>
      </div>
      
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Click the button below to process the `Product Requirements Document_(PRD)_VWO.com.pdf` file. This will extract the text, split it into chunks, generate embeddings using Ollama, and save them in a local Chroma vector database.
      </p>

      <button 
        className="btn btn-primary" 
        onClick={handleIngest} 
        disabled={loading || isIngested}
      >
        {loading ? (
          <><Loader2 className="spin" size={18} /> Processing Pipeline...</>
        ) : isIngested ? (
          <><CheckCircle2 size={18} /> Successfully Ingested</>
        ) : (
          <><Database size={18} /> Start Ingestion Pipeline</>
        )}
      </button>

      {error && (
        <div style={{ color: 'var(--danger-color)', marginTop: '1rem', padding: '0.75rem', background: 'rgba(248, 81, 73, 0.1)', borderRadius: '8px' }}>
          {error}
        </div>
      )}

      {(loading || isIngested) && (
        <div className="step-container">
          {steps.map((step, idx) => {
            const isActive = activeStep === idx;
            const isCompleted = activeStep > idx || isIngested;
            
            return (
              <div 
                key={idx} 
                className={`step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
              >
                <div className="step-icon">
                  {isCompleted ? <CheckCircle2 size={20} /> : isActive ? <Loader2 size={20} className="spin" /> : step.icon}
                </div>
                <span>{step.label}</span>
                {isCompleted && idx === 1 && chunkCount > 0 && (
                  <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {chunkCount} chunks
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};

export default IngestionPanel;
