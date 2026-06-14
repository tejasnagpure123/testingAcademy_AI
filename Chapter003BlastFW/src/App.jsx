import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [config, setConfig] = useState({
    jiraUrl: '',
    jiraEmail: '',
    jiraToken: '',
    issueId: 'KAN-12',
    groqKey: ''
  });

  const [loading, setLoading] = useState(false);
  const [testPlan, setTestPlan] = useState('');
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: value }));
  };

  const generateTestPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'An error occurred during generation');
      }

      setTestPlan(data.testPlanMarkdown);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="header">
        <h1>AI Test Plan Generator</h1>
        <p>B.L.A.S.T Framework • Phase 4: Stylize</p>
      </div>

      <div className="glass-panel">
        <h2>Configuration</h2>
        <p style={{marginBottom: '1.5rem', color: '#a0aec0', fontSize: '0.9rem'}}>
          Leave fields blank to use values from `.env` on the backend.
        </p>
        <div className="form-grid">
          <div className="form-group">
            <label>Jira Base URL</label>
            <input 
              type="text" 
              name="jiraUrl" 
              placeholder="https://your-domain.atlassian.net" 
              value={config.jiraUrl}
              onChange={handleInputChange}
            />
          </div>
          <div className="form-group">
            <label>Jira Email</label>
            <input 
              type="text" 
              name="jiraEmail" 
              placeholder="email@example.com" 
              value={config.jiraEmail}
              onChange={handleInputChange}
            />
          </div>
          <div className="form-group">
            <label>Jira API Token</label>
            <input 
              type="password" 
              name="jiraToken" 
              placeholder="••••••••••••••••" 
              value={config.jiraToken}
              onChange={handleInputChange}
            />
          </div>
          <div className="form-group">
            <label>Groq API Key</label>
            <input 
              type="password" 
              name="groqKey" 
              placeholder="gsk_..." 
              value={config.groqKey}
              onChange={handleInputChange}
            />
          </div>
          <div className="form-group full-width">
            <label>Issue ID</label>
            <input 
              type="text" 
              name="issueId" 
              placeholder="KAN-12" 
              value={config.issueId}
              onChange={handleInputChange}
              style={{ fontWeight: 'bold' }}
            />
          </div>
        </div>

        <button 
          className="generate-btn" 
          onClick={generateTestPlan}
          disabled={loading}
        >
          {loading ? <div className="loading-spinner"></div> : 'Generate Test Plan'}
        </button>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>

      {testPlan && (
        <div className="glass-panel" style={{ marginTop: '2rem' }}>
          <div className="markdown-content">
            <ReactMarkdown>{testPlan}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
