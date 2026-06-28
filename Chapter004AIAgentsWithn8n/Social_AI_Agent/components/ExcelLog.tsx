import React from 'react';
import { ContentRow } from '@/lib/types';
import { FileSpreadsheet, Download, Activity, CheckCircle, Clock, AlertTriangle, Layers } from 'lucide-react';

interface ExcelLogProps {
  rows: ContentRow[];
  fileModifiedTime?: string;
}

interface LogEvent {
  date: string;
  topic: string;
  agent: string;
  action: string;
  timestamp: string;
  status: 'Pending' | 'Writing' | 'Imaging' | 'Done' | 'Error';
}

export default function ExcelLog({ rows, fileModifiedTime }: ExcelLogProps) {
  // Generate logs from row state transitions
  const logs: LogEvent[] = [];

  rows.forEach((row) => {
    const fallbackTime = row.lastUpdated || new Date().toISOString();
    
    // Agent 1: Created Topic
    if (row.topic) {
      logs.push({
        date: row.date,
        topic: row.topic,
        agent: 'Agent 1 (Topic Gen)',
        action: `Created new content row with topic: "${row.topic}"`,
        timestamp: row.writtenBy === 'Agent 1' ? fallbackTime : '', // approximate if overwritten
        status: 'Pending',
      });
    }

    // Agent 2: Wrote Content
    if (row.linkedinPost || row.mediumArticle || row.status === 'Writing' || row.status === 'Imaging' || row.status === 'Done') {
      logs.push({
        date: row.date,
        topic: row.topic,
        agent: 'Agent 2 (Content Writer)',
        action: `Generated LinkedIn, Medium, Instagram, YouTube, and Dev.to drafts`,
        timestamp: row.writtenBy === 'Agent 2' ? fallbackTime : '',
        status: row.status === 'Writing' ? 'Writing' : 'Imaging',
      });
    }

    // Agent 3: Generated Images
    if (row.linkedinImage || row.mediumImage || row.status === 'Done') {
      logs.push({
        date: row.date,
        topic: row.topic,
        agent: 'Agent 3 (Image Gen)',
        action: `Generated assets: LinkedIn Image, Medium Cover Image, and Instagram Crop`,
        timestamp: row.writtenBy === 'Agent 3' ? fallbackTime : '',
        status: 'Done',
      });
    }

    // Pipeline Error Status
    if (row.status === 'Error') {
      logs.push({
        date: row.date,
        topic: row.topic,
        agent: 'Pipeline Orchestrator',
        action: `Execution interrupted due to an error. Status marked as Error.`,
        timestamp: fallbackTime,
        status: 'Error',
      });
    }
  });

  // Assign fallback times for logs lacking specific timestamps, and sort them newest first
  const resolvedLogs = logs.map((log) => {
    if (!log.timestamp) {
      // Estimate past actions happened a bit earlier than latest mutation time
      const offset = log.status === 'Pending' ? -60000 : log.status === 'Imaging' ? -30000 : 0;
      const baseTime = new Date(fileModifiedTime || Date.now());
      log.timestamp = new Date(baseTime.getTime() + offset).toISOString();
    }
    return log;
  }).sort((a, b) => b.timestamp.localeCompare(a.timestamp));

  const getAgentColor = (agent: string) => {
    if (agent.includes('Agent 1')) return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
    if (agent.includes('Agent 2')) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    if (agent.includes('Agent 3')) return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
    return 'text-red-400 bg-red-500/10 border-red-500/20';
  };

  const getStatusIcon = (status: ContentRow['status']) => {
    switch (status) {
      case 'Done':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'Writing':
      case 'Imaging':
        return <Clock className="w-4 h-4 text-amber-400 animate-pulse" />;
      case 'Error':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* SHEET INFO HEADER BAR */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
            <FileSpreadsheet className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-white font-semibold">content_calendar.xlsx</h3>
            <p className="text-xs text-zinc-500">
              Last Modified: {fileModifiedTime ? new Date(fileModifiedTime).toLocaleString() : 'Not created yet'}
            </p>
          </div>
        </div>
        
        <a
          href="/api/calendar?download=true"
          className="flex items-center space-x-2 px-5 py-2.5 bg-purple-600 text-white rounded-lg font-medium shadow-md shadow-purple-900/20 hover:bg-purple-500 active:bg-purple-700 transition-all duration-150 text-sm"
        >
          <Download className="w-4 h-4" />
          <span>Download Spreadsheet (.xlsx)</span>
        </a>
      </div>

      {/* OPERATIONS LOG */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
          <span className="text-white font-semibold flex items-center space-x-2">
            <Activity className="w-4 h-4 text-purple-400" />
            <span>Excel Mutations Log</span>
          </span>
          <span className="text-zinc-500 text-xs">{resolvedLogs.length} events logged</span>
        </div>

        {resolvedLogs.length === 0 ? (
          <div className="py-12 text-center">
            <Layers className="w-12 h-12 text-zinc-650 mx-auto mb-3" />
            <p className="text-zinc-500 text-sm">No spreadsheet operations recorded yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-zinc-800">
              <thead className="bg-zinc-950">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase">Timestamp</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase">Agent / Source</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase">Operation Description</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase">Topic Date</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-zinc-400 uppercase">Step</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800 bg-zinc-900/30">
                {resolvedLogs.map((log, index) => (
                  <tr key={index} className="hover:bg-zinc-800/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-zinc-450 font-mono">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold border ${getAgentColor(log.agent)}`}>
                        {log.agent}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-zinc-300 font-medium">
                      {log.action}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-zinc-450 font-mono">
                      {log.date}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-flex justify-center">{getStatusIcon(log.status)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
