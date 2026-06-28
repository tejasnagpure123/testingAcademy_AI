import React from 'react';
import { ContentRow, PipelineStatus } from '@/lib/types';
import { Calendar, CheckCircle2, Clock, FileText, AlertCircle, RefreshCw } from 'lucide-react';

interface StatusCardsProps {
  todayRow: ContentRow | null;
  pipelineStatus: PipelineStatus;
}

export default function StatusCards({ todayRow, pipelineStatus }: StatusCardsProps) {
  // Determine current active status
  const isRunning = pipelineStatus.status === 'running';
  const status = isRunning 
    ? (pipelineStatus.currentStep === 'topic_generation' ? 'Topic Gen' : pipelineStatus.currentStep === 'content_writing' ? 'Writing' : 'Imaging')
    : (todayRow?.status || 'No Run Today');

  const getStatusColor = (val: string) => {
    switch (val) {
      case 'Done':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'Writing':
      case 'Imaging':
      case 'Topic Gen':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse';
      case 'Pending':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'Error':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      default:
        return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30';
    }
  };

  const getStatusIcon = (val: string) => {
    switch (val) {
      case 'Done':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'Writing':
      case 'Imaging':
      case 'Topic Gen':
        return <RefreshCw className="w-5 h-5 text-amber-400 animate-spin" />;
      case 'Pending':
        return <Clock className="w-5 h-5 text-blue-400" />;
      case 'Error':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Clock className="w-5 h-5 text-zinc-400" />;
    }
  };

  const formattedTime = todayRow?.lastUpdated 
    ? new Date(todayRow.lastUpdated).toLocaleTimeString() 
    : pipelineStatus.lastRunTime 
      ? new Date(pipelineStatus.lastRunTime).toLocaleTimeString() 
      : 'Never';

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* CARD 1: TODAY'S TOPIC */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 transition-all duration-300 hover:border-zinc-700 hover:shadow-lg hover:shadow-black/20">
        <div className="flex items-center justify-between mb-4">
          <span className="text-zinc-400 text-sm font-medium">Today's Topic</span>
          <FileText className="w-5 h-5 text-purple-400" />
        </div>
        <h3 className="text-white text-lg font-semibold tracking-tight line-clamp-2 h-14">
          {todayRow?.topic || 'No topic generated yet for today'}
        </h3>
        <p className="text-xs text-zinc-500 mt-2">
          {todayRow?.date ? `Generated on ${todayRow.date}` : 'Trigger the pipeline to generate a topic'}
        </p>
      </div>

      {/* CARD 2: PIPELINE STATUS */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 transition-all duration-300 hover:border-zinc-700 hover:shadow-lg hover:shadow-black/20">
        <div className="flex items-center justify-between mb-4">
          <span className="text-zinc-400 text-sm font-medium">Pipeline Status</span>
          {getStatusIcon(status)}
        </div>
        <div className="flex flex-col justify-between h-20">
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${getStatusColor(status)}`}>
              {status.toUpperCase()}
            </span>
          </div>
          {isRunning && (
            <p className="text-xs text-amber-400/80 animate-pulse mt-2">
              Agent is active. Writing to content_calendar.xlsx...
            </p>
          )}
          {!isRunning && todayRow?.status === 'Error' && (
            <p className="text-xs text-red-400/80 mt-2 truncate max-w-full">
              Error: {pipelineStatus.error || 'Failed during execution.'}
            </p>
          )}
          {!isRunning && todayRow?.status === 'Done' && (
            <p className="text-xs text-emerald-400/80 mt-2">
              All contents generated and saved successfully.
            </p>
          )}
        </div>
      </div>

      {/* CARD 3: LAST UPDATE */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 transition-all duration-300 hover:border-zinc-700 hover:shadow-lg hover:shadow-black/20">
        <div className="flex items-center justify-between mb-4">
          <span className="text-zinc-400 text-sm font-medium">Last Action</span>
          <Calendar className="w-5 h-5 text-indigo-400" />
        </div>
        <h3 className="text-white text-3xl font-bold tracking-tight">
          {formattedTime}
        </h3>
        <p className="text-xs text-zinc-500 mt-2">
          {todayRow?.writtenBy ? `Mutated by ${todayRow.writtenBy}` : 'No actions taken yet today'}
        </p>
      </div>
    </div>
  );
}
