import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Activity, Beaker, FileJson, Loader2, PlayCircle } from 'lucide-react';
import './index.css';

function App() {
  const [file1, setFile1] = useState('D:\\Study\\TestingAcademy_AI_Notes\\JSON_LANG\\results1.json');
  const [file2, setFile2] = useState('D:\\Study\\TestingAcademy_AI_Notes\\JSON_LANG\\results2.json');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult('');

    try {
      const response = await fetch('/api/v1/run/dc6870e8-fd0c-4026-b101-af2c568e46ab?stream=false', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'sk-3VHe0nLT0utdvA3OpUouRLY3GIS6nN5Gk2LR9XqmQAQ'
        },
        body: JSON.stringify({
          output_type: 'chat',
          input_type: 'text',
          input_value: 'Analyze these two Playwright runs and tell me which build has the most failing/flaky test.',
          session_id: 'postman-session-1',
          tweaks: {
            'File-XXXXX': {
              path: [file1]
            },
            'File-YYYYY': {
              path: [file2]
            }
          }
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Extract the markdown response based on the provided curl response structure
      const markdownMessage = data?.outputs?.[0]?.outputs?.[0]?.results?.message?.text || 
                              data?.outputs?.[0]?.outputs?.[0]?.artifacts?.message ||
                              "No text returned from the API.";
      
      setResult(markdownMessage);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to analyze runs. Ensure the API is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Flaky Test Analyzer</h1>
        <p>Compare Playwright test runs with AI to identify flaky tests instantly.</p>
      </header>

      <main className="main-card">
        <div className="input-group">
          <label htmlFor="file1">
            <FileJson size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'text-bottom' }} />
            Build 1 Results (Absolute JSON Path)
          </label>
          <input
            id="file1"
            type="text"
            className="input-field"
            value={file1}
            onChange={(e) => setFile1(e.target.value)}
            placeholder="e.g. D:\path\to\results1.json"
          />
        </div>

        <div className="input-group">
          <label htmlFor="file2">
            <FileJson size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'text-bottom' }} />
            Build 2 Results (Absolute JSON Path)
          </label>
          <input
            id="file2"
            type="text"
            className="input-field"
            value={file2}
            onChange={(e) => setFile2(e.target.value)}
            placeholder="e.g. D:\path\to\results2.json"
          />
        </div>

        <button 
          className="analyze-btn" 
          onClick={handleAnalyze} 
          disabled={loading || !file1 || !file2}
        >
          {loading ? (
            <>
              <Loader2 className="spinner" size={20} />
              Analyzing Runs...
            </>
          ) : (
            <>
              <PlayCircle size={20} />
              Analyze Runs
            </>
          )}
        </button>

        {error && (
          <div style={{ color: '#E11D48', marginTop: '1.5rem', padding: '1rem', backgroundColor: '#FFE4E6', borderRadius: '8px', fontSize: '0.9rem' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {(result || loading) && (
          <div className="results-section">
            <h2>
              <Activity size={24} color="#4F46E5" />
              Analysis Results
            </h2>
            <div className="markdown-body">
              {loading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#64748B' }}>
                  <Beaker size={20} className="spinner" />
                  AI is processing the test runs...
                </div>
              ) : (
                <ReactMarkdown>{result}</ReactMarkdown>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
