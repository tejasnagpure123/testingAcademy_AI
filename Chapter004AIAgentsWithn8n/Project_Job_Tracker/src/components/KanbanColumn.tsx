import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import type { Job, JobStatus } from '../lib/db';
import { JobCard } from './JobCard';
import { cn } from '../lib/utils';

interface KanbanColumnProps {
  status: JobStatus;
  jobs: Job[];
  onEditJob: (job: Job) => void;
  onDeleteJob: (id: string) => void;
}

export function KanbanColumn({ status, jobs, onEditJob, onDeleteJob }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
    data: {
      type: 'Column',
      status,
    },
  });

  return (
    <div className="flex flex-col flex-1 min-w-[300px] max-w-[350px] shrink-0 bg-secondary/50 rounded-xl border border-border/50 h-full max-h-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border/50 bg-secondary/80">
        <h3 className="font-semibold text-secondary-foreground">{status}</h3>
        <span className="flex items-center justify-center bg-background text-muted-foreground text-xs font-medium w-6 h-6 rounded-full">
          {jobs.length}
        </span>
      </div>

      <div
        ref={setNodeRef}
        className={cn(
          "flex-1 p-3 overflow-y-auto kanban-scroll transition-colors",
          isOver ? "bg-accent/50" : "bg-transparent"
        )}
      >
        <div className="flex flex-col gap-3 min-h-[100px]">
          <SortableContext items={jobs.map(j => j.id)} strategy={verticalListSortingStrategy}>
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onEdit={onEditJob}
                onDelete={onDeleteJob}
              />
            ))}
          </SortableContext>
        </div>
      </div>
    </div>
  );
}
