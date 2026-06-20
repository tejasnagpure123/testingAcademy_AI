import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Job } from '../lib/db';
import { formatDistanceToNow } from 'date-fns';
import { Building2, ExternalLink, FileText, Pencil, Trash2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface JobCardProps {
  job: Job;
  onEdit: (job: Job) => void;
  onDelete: (id: string) => void;
}

const statusColors: Record<Job['status'], string> = {
  'Wishlist': 'border-l-slate-400 dark:border-l-slate-500',
  'Applied': 'border-l-blue-400 dark:border-l-blue-500',
  'Follow-up': 'border-l-purple-400 dark:border-l-purple-500',
  'Interview': 'border-l-yellow-400 dark:border-l-yellow-500',
  'Offer': 'border-l-green-400 dark:border-l-green-500',
  'Rejected': 'border-l-red-400 dark:border-l-red-500',
};

export function JobCard({ job, onEdit, onDelete }: JobCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: job.id, data: { type: 'Job', job } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(job);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this job?')) {
      onDelete(job.id);
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        "group relative flex flex-col gap-2 rounded-lg border bg-card p-3 shadow-sm transition-all hover:shadow-md cursor-grab active:cursor-grabbing border-l-4",
        statusColors[job.status],
        isDragging && "opacity-50 ring-2 ring-primary ring-offset-2 scale-105 z-10"
      )}
    >
      <div className="flex justify-between items-start gap-2">
        <div className="font-semibold text-card-foreground line-clamp-1 flex-1">
          {job.role}
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={handleEdit} className="p-1 rounded text-muted-foreground hover:bg-muted hover:text-foreground">
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button onClick={handleDelete} className="p-1 rounded text-muted-foreground hover:bg-muted hover:text-destructive">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Building2 className="w-4 h-4 shrink-0" />
        <span className="line-clamp-1">{job.company}</span>
        {job.url && (
          <a 
            href={job.url} 
            target="_blank" 
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="ml-auto text-primary hover:text-primary/80 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2 mt-2">
        {job.resume && (
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-secondary text-secondary-foreground text-xs font-medium">
            <FileText className="w-3 h-3" />
            {job.resume}
          </div>
        )}
        <div className="text-xs text-muted-foreground ml-auto">
          {formatDistanceToNow(job.dateApplied, { addSuffix: true })}
        </div>
      </div>
    </div>
  );
}
