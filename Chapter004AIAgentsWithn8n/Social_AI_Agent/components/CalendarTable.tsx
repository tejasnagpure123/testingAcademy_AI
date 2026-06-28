import React from 'react';
import { ContentRow } from '@/lib/types';
import { CalendarRange, Check, AlertCircle, FileText, Video, Code, ImageIcon } from 'lucide-react';

interface CalendarTableProps {
  rows: ContentRow[];
  onSelectRow?: (row: ContentRow) => void;
}

export default function CalendarTable({ rows, onSelectRow }: CalendarTableProps) {
  // Sort rows newest first (based on date YYYY-MM-DD descending)
  const sortedRows = [...rows].sort((a, b) => b.date.localeCompare(a.date));

  const getStatusBadge = (status: ContentRow['status']) => {
    switch (status) {
      case 'Done':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Check className="w-3 h-3 mr-1" />
            Done
          </span>
        );
      case 'Writing':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
            Writing
          </span>
        );
      case 'Imaging':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-600/10 text-amber-500 border border-amber-600/20 animate-pulse">
            Imaging
          </span>
        );
      case 'Pending':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
            Pending
          </span>
        );
      case 'Error':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
            <AlertCircle className="w-3 h-3 mr-1" />
            Error
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">
            Unknown
          </span>
        );
    }
  };

  if (sortedRows.length === 0) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center">
        <CalendarRange className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <h3 className="text-white text-lg font-semibold mb-1">Calendar Empty</h3>
        <p className="text-zinc-500 text-sm max-w-sm mx-auto">
          No records found in content_calendar.xlsx. Run the pipeline to append your first row.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-800">
          <thead className="bg-zinc-950">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">Date</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">Topic</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">LinkedIn</th>
              <th className="px-6 py-4 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">Medium</th>
              <th className="px-6 py-4 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">IG</th>
              <th className="px-6 py-4 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">YT</th>
              <th className="px-6 py-4 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">Dev.to</th>
              <th className="px-6 py-4 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">Images</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800 bg-zinc-900/40">
            {sortedRows.map((row, index) => {
              const hasLinkedin = !!row.linkedinPost;
              const hasMedium = !!row.mediumArticle;
              const hasIg = !!row.igScript;
              const hasYt = !!row.ytScript;
              const hasDevto = !!row.devtoArticle;
              const imagesCount = [row.linkedinImage, row.mediumImage, row.igImage].filter(Boolean).length;

              return (
                <tr 
                  key={index} 
                  onClick={() => onSelectRow?.(row)}
                  className={`transition-colors duration-150 ${
                    onSelectRow ? 'cursor-pointer hover:bg-zinc-800/40' : ''
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-zinc-300 font-mono">
                    {row.date}
                  </td>
                  <td className="px-6 py-4 text-sm text-white font-medium max-w-xs truncate">
                    {row.topic}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {getStatusBadge(row.status)}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <FileText className={`w-4 h-4 mx-auto ${hasLinkedin ? 'text-purple-400' : 'text-zinc-700'}`} />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <FileText className={`w-4 h-4 mx-auto ${hasMedium ? 'text-indigo-400' : 'text-zinc-700'}`} />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Video className={`w-4 h-4 mx-auto ${hasIg ? 'text-pink-400' : 'text-zinc-700'}`} />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Video className={`w-4 h-4 mx-auto ${hasYt ? 'text-red-500' : 'text-zinc-700'}`} />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Code className={`w-4 h-4 mx-auto ${hasDevto ? 'text-emerald-400' : 'text-zinc-700'}`} />
                  </td>
                  <td className="px-6 py-4 text-center whitespace-nowrap">
                    {imagesCount > 0 ? (
                      <span className="inline-flex items-center text-xs text-indigo-400 font-medium">
                        <ImageIcon className="w-3.5 h-3.5 mr-1" />
                        {imagesCount}
                      </span>
                    ) : (
                      <span className="text-zinc-750 text-xs">-</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
