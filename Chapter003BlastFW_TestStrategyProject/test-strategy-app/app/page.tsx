"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Loader2, FileText, ClipboardList, CheckCircle } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"strategy" | "cases">("strategy");
  const [jiraId, setJiraId] = useState("");
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!jiraId) {
      setError("Please enter a Jira ID (e.g. KAN-13)");
      return;
    }
    
    setLoading(true);
    setError("");
    setContent("");

    try {
      const endpoint = activeTab === "strategy" ? "/api/strategy" : "/api/cases";
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jiraId }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to generate");

      setContent(data.content);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
      <div className="max-w-5xl mx-auto px-4 py-12">
        {/* Header */}
        <header className="text-center space-y-4 mb-16">
          <div className="inline-flex items-center justify-center p-3 bg-indigo-500/10 rounded-2xl mb-4 border border-indigo-500/20 shadow-[0_0_40px_rgba(99,102,241,0.2)]">
            <CheckCircle className="w-8 h-8 text-indigo-400" />
          </div>
          <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 tracking-tight">
            AI QA Architect
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Generate enterprise-grade Test Strategies and Test Cases instantly from your Jira tickets.
          </p>
        </header>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-[350px_1fr] gap-8 items-start">
          
          {/* Sidebar / Controls */}
          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl sticky top-8">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              Configuration
            </h2>
            
            <div className="space-y-6">
              {/* Input */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-400 uppercase tracking-wider">Jira Ticket ID</label>
                <input
                  type="text"
                  placeholder="e.g., KAN-13"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-700"
                  value={jiraId}
                  onChange={(e) => setJiraId(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                />
              </div>

              {/* Tabs */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-400 uppercase tracking-wider">Output Type</label>
                <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800">
                  <button
                    onClick={() => setActiveTab("strategy")}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      activeTab === "strategy" 
                      ? "bg-slate-800 text-white shadow-sm" 
                      : "text-slate-500 hover:text-slate-300"
                    }`}
                  >
                    <FileText className="w-4 h-4" /> Strategy
                  </button>
                  <button
                    onClick={() => setActiveTab("cases")}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      activeTab === "cases" 
                      ? "bg-slate-800 text-white shadow-sm" 
                      : "text-slate-500 hover:text-slate-300"
                    }`}
                  >
                    <ClipboardList className="w-4 h-4" /> Test Cases
                  </button>
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="w-full bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Generate Now"}
              </button>

              {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Results Area */}
          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 min-h-[500px] shadow-2xl overflow-auto">
            {content ? (
              <div className="markdown-prose max-w-none">
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4 py-20">
                {activeTab === "strategy" ? (
                  <FileText className="w-16 h-16 opacity-20" />
                ) : (
                  <ClipboardList className="w-16 h-16 opacity-20" />
                )}
                <p className="text-lg">
                  {loading ? "Generating intelligent QA assets..." : "Your generated content will appear here"}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
