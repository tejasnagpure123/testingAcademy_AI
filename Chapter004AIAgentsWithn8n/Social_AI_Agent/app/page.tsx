'use client';

import React, { useState, useEffect } from 'react';
import { ContentRow, PipelineStatus, ApiKeyStatus } from '@/lib/types';
import StatusCards from '@/components/StatusCards';
import ContentTabs from '@/components/ContentTabs';
import CalendarTable from '@/components/CalendarTable';
import ExcelLog from '@/components/ExcelLog';
import { 
  Play, 
  Layers, 
  Calendar, 
  FileSpreadsheet, 
  Cpu, 
  Database, 
  Key, 
  Clock, 
  AlertCircle,
  HelpCircle,
  RefreshCw
} from 'lucide-react';

export default function Dashboard() {
  // Navigation active tab
  const [activeTab, setActiveTab] = useState<'content' | 'calendar' | 'log'>('content');
  
  // Data State
  const [todayRow, setTodayRow] = useState<ContentRow | null>(null);
  const [calendarRows, setCalendarRows] = useState<ContentRow[]>([]);
  const [fileModifiedTime, setFileModifiedTime] = useState<string>('');
  
  // Status and Health State
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus>({
    status: 'idle',
    currentStep: 'idle'
  });
  const [keysHealth, setKeysHealth] = useState<ApiKeyStatus>({
    groq: false,
    gemini: false
  });
  
  // Loading & error UI states
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [uiError, setUiError] = useState<string | null>(null);

  // Fetch Pipeline Status & API Key Health
  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const json = await res.json();
      if (json.success) {
        setPipelineStatus(json.pipeline);
        setKeysHealth(json.keys);
      }
    } catch (e: any) {
      console.error('Failed to fetch status:', e);
    }
  };

  // Fetch Today's content row
  const fetchToday = async () => {
    try {
      const res = await fetch('/api/today');
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const json = await res.json();
      if (json.success) {
        setTodayRow(json.data);
      }
    } catch (e: any) {
      console.error('Failed to fetch today\'s row:', e);
    }
  };

  // Fetch Full Calendar
  const fetchCalendar = async () => {
    try {
      const res = await fetch('/api/calendar');
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const json = await res.json();
      if (json.success) {
        setCalendarRows(json.data);
        setFileModifiedTime(json.fileModifiedTime || '');
      }
    } catch (e: any) {
      console.error('Failed to fetch calendar:', e);
      setUiError('Could not load Excel calendar data. Make sure process has write rights in project root.');
    }
  };

  // Run Pipeline manually
  const handleRunPipeline = async () => {
    if (pipelineStatus.status === 'running') return;
    setIsTriggering(true);
    setUiError(null);
    try {
      const res = await fetch('/api/run', { method: 'POST' });
      const json = await res.json();
      if (res.status === 202 || json.success) {
        // Optimistic state updates
        setPipelineStatus(prev => ({
          ...prev,
          status: 'running',
          currentStep: 'topic_generation'
        }));
      } else {
        setUiError(json.message || 'Failed to trigger pipeline.');
      }
    } catch (e: any) {
      setUiError('Failed to run pipeline. Server error.');
      console.error(e);
    } finally {
      setIsTriggering(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchStatus();
    fetchToday();
    fetchCalendar();
  }, []);

  // Poll every 3 seconds for active state
  useEffect(() => {
    const timer = setInterval(() => {
      fetchStatus();
      fetchToday();
      
      // If pipeline was running and just finished (or error), refresh the table list
      if (pipelineStatus.status === 'running') {
        fetchCalendar();
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [pipelineStatus.status]);

  // Derived running step description
  const getStepDescription = (step: PipelineStatus['currentStep']) => {
    switch (step) {
      case 'topic_generation': return 'Generating Topic Title...';
      case 'content_writing': return 'Writing 5 Content Drafts...';
      case 'image_generation': return 'Creating Artwork & Graphics...';
      default: return 'Running Pipeline...';
    }
  };

  const isPipelineRunning = pipelineStatus.status === 'running';

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col md:flex-row antialiased">
      {/* SIDEBAR */}
      <aside className="w-full md:w-80 bg-zinc-900 border-r border-zinc-800 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo */}
          <div className="p-6 border-b border-zinc-800 flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-purple-600 to-indigo-600 rounded-lg shadow-md shadow-purple-900/40">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
                ContentForge
              </h1>
              <p className="text-zinc-500 text-xs font-medium">Local AI Agent Pipeline</p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="p-6 border-b border-zinc-800 space-y-4">
            <button
              onClick={handleRunPipeline}
              disabled={isPipelineRunning || isTriggering}
              className={`w-full py-3 px-4 rounded-lg font-semibold flex items-center justify-center space-x-2 shadow-lg transition-all duration-200 ${
                isPipelineRunning
                  ? 'bg-amber-600/25 border border-amber-500/20 text-amber-300 cursor-not-allowed shadow-none'
                  : isTriggering
                    ? 'bg-purple-700/50 text-purple-300 border border-purple-500/20 cursor-wait'
                    : 'bg-purple-600 text-white shadow-purple-900/30 hover:bg-purple-500 hover:shadow-purple-500/20 active:bg-purple-700 active:scale-[0.98]'
              }`}
            >
              {isPipelineRunning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className="text-sm">{getStepDescription(pipelineStatus.currentStep)}</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run Pipeline Now</span>
                </>
              )}
            </button>

            {uiError && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-xs flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{uiError}</span>
              </div>
            )}
          </div>

          {/* API Keys Status */}
          <div className="p-6 border-b border-zinc-800 space-y-4">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider flex items-center space-x-1.5">
              <Key className="w-3.5 h-3.5" />
              <span>API Gateway Health</span>
            </span>
            <div className="space-y-3">
              {/* GROQ indicator */}
              <div className="flex items-center justify-between bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/60">
                <div className="flex items-center space-x-2.5">
                  <Database className="w-4 h-4 text-zinc-500" />
                  <span className="text-sm text-zinc-300">GROQ API (LLMs)</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className={`w-2 h-2 rounded-full shadow ${keysHealth.groq ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-red-500 shadow-red-500/50'}`} />
                  <span className={`text-xs font-medium ${keysHealth.groq ? 'text-emerald-400' : 'text-red-400'}`}>
                    {keysHealth.groq ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
              </div>

              {/* GEMINI indicator */}
              <div className="flex items-center justify-between bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/60">
                <div className="flex items-center space-x-2.5">
                  <Database className="w-4 h-4 text-zinc-500" />
                  <span className="text-sm text-zinc-300">Gemini API (Imaging)</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className={`w-2 h-2 rounded-full shadow ${keysHealth.gemini ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-red-500 shadow-red-500/50'}`} />
                  <span className={`text-xs font-medium ${keysHealth.gemini ? 'text-emerald-400' : 'text-red-400'}`}>
                    {keysHealth.gemini ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Schedule & Metadata */}
        <div className="p-6 bg-zinc-950/40 border-t border-zinc-800/40 space-y-4">
          <div className="flex items-start space-x-3 text-xs text-zinc-400">
            <Clock className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold text-zinc-300">Daily Scheduler Active</p>
              <p className="text-zinc-500 mt-0.5">Triggers daily at 09:00 AM</p>
            </div>
          </div>

          <div className="flex items-start space-x-3 text-xs text-zinc-500">
            <HelpCircle className="w-4 h-4 text-zinc-650 mt-0.5 shrink-0" />
            <div>
              <p>Workplace is entirely local. Files mutates in project root directory.</p>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTAINER */}
      <main className="flex-grow flex flex-col p-6 md:p-8 space-y-8 overflow-y-auto max-h-screen">
        {/* STATS CARDS */}
        <StatusCards todayRow={todayRow} pipelineStatus={pipelineStatus} />

        {/* TABS CONTROLLER */}
        <div className="space-y-4 flex-grow flex flex-col">
          <div className="flex space-x-1 p-1 bg-zinc-900 border border-zinc-800 rounded-xl max-w-md">
            <button
              onClick={() => setActiveTab('content')}
              className={`flex-1 flex items-center justify-center space-x-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                activeTab === 'content'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Today's Content</span>
            </button>
            <button
              onClick={() => setActiveTab('calendar')}
              className={`flex-1 flex items-center justify-center space-x-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                activeTab === 'calendar'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Calendar className="w-4 h-4" />
              <span>Calendar</span>
            </button>
            <button
              onClick={() => setActiveTab('log')}
              className={`flex-1 flex items-center justify-center space-x-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                activeTab === 'log'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Excel Log</span>
            </button>
          </div>

          {/* TAB VISUALIZERS */}
          <div className="flex-grow flex flex-col">
            {activeTab === 'content' && <ContentTabs todayRow={todayRow} />}
            {activeTab === 'calendar' && <CalendarTable rows={calendarRows} onSelectRow={(row) => { setTodayRow(row); setActiveTab('content'); }} />}
            {activeTab === 'log' && <ExcelLog rows={calendarRows} fileModifiedTime={fileModifiedTime} />}
          </div>
        </div>
      </main>
    </div>
  );
}
