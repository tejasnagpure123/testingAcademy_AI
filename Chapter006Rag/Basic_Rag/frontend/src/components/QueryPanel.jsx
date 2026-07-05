import React, { useState } from 'react';
import axios from 'axios';
import { Search, MessageSquare, Loader2, Send } from 'lucide-react';

const QueryPanel = ({ isIngested }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post('http://localhost:5000/api/query', { query });
      if (response.data.success) {
        setResult(response.data);
      } else {
        throw new Error(response.data.message);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.message || err.message || "Failed to fetch answer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel" style={{ opacity: isIngested ? 1 : 0.5, pointerEvents: isIngested ? 'auto' : 'none', transition: 'all 0.5s ease' }}>
      <div className="panel-header">
        <MessageSquare className="text-accent" />
        <h2>Query & Retrieval</h2>
      </div>
      
      <form onSubmit={handleQuery} className="query-form">
        <input 
          type="text" 
          className="input-field" 
          placeholder="Ask a question about the VWO PRD..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading || !isIngested}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !query.trim() || !isIngested} style={{ padding: '0.75rem 1rem' }}>
          {loading ? <Loader2 className="spin" size={20} /> : <Send size={20} />}
        </button>
      </form>

      {error && (
        <div style={{ color: 'var(--danger-color)', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(248, 81, 73, 0.1)', borderRadius: '8px' }}>
          {error}
        </div>
      )}

      <div className="results-area">
        {loading && !result && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
            <Loader2 className="spin" size={32} style={{ marginBottom: '1rem', color: 'var(--accent-color)' }} />
            <p>Searching ChromaDB and generating answer...</p>
          </div>
        )}

        {result && (
          <>
            <div>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Search size={16} color="var(--text-secondary)" /> 
                Retrieved Context (Top 4 Chunks)
              </h3>
              <div className="chunks-grid">
                {result.retrievedChunks.map((chunk, idx) => (
                  <div key={idx} className="chunk-card" title={chunk}>
                    <span style={{ color: 'var(--accent-color)', fontWeight: 'bold', marginRight: '5px' }}>#{idx + 1}</span>
                    {chunk}
                  </div>
                ))}
              </div>
            </div>

            <div className="answer-box">
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--accent-color)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <MessageSquare size={18} /> Groq Generated Answer
              </h3>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{result.answer}</p>
            </div>
          </>
        )}
      </div>
    </section>
  );
};

export default QueryPanel;
