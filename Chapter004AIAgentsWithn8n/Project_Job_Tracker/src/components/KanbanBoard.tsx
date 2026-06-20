import { useState } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type {
  DragStartEvent,
  DragOverEvent,
  DragEndEvent,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import type { Job, JobStatus } from '../lib/db';
import { KanbanColumn } from './KanbanColumn';
import { JobCard } from './JobCard';

interface KanbanBoardProps {
  jobs: Job[];
  onUpdateJob: (job: Job) => void;
  onEditJob: (job: Job) => void;
  onDeleteJob: (id: string) => void;
}

const COLUMNS: JobStatus[] = ['Wishlist', 'Applied', 'Follow-up', 'Interview', 'Offer', 'Rejected'];

export function KanbanBoard({ jobs, onUpdateJob, onEditJob, onDeleteJob }: KanbanBoardProps) {
  const [activeJob, setActiveJob] = useState<Job | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const { data } = active;
    
    if (data.current?.type === 'Job') {
      setActiveJob(data.current.job);
    }
  };

  const handleDragOver = (_event: DragOverEvent) => {
    // Only handling visual changes here if needed, 
    // but the actual update should happen on drag end to persist to DB.
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveJob(null);

    if (!over) return;

    const activeId = active.id;
    const overId = over.id;

    if (activeId === overId) return;

    const isActiveAJob = active.data.current?.type === 'Job';
    const isOverAColumn = over.data.current?.type === 'Column';
    const isOverAJob = over.data.current?.type === 'Job';

    if (!isActiveAJob) return;

    const draggedJob = active.data.current?.job as Job;
    let newStatus = draggedJob.status;

    if (isOverAColumn) {
      newStatus = over.data.current?.status as JobStatus;
    } else if (isOverAJob) {
      newStatus = over.data.current?.job.status as JobStatus;
    }

    if (draggedJob.status !== newStatus) {
      // Create updated job and trigger update
      const updatedJob = { ...draggedJob, status: newStatus };
      onUpdateJob(updatedJob);
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="flex h-full gap-4 p-4 md:p-8 overflow-x-auto kanban-scroll items-start bg-background/50">
        {COLUMNS.map((status) => (
          <KanbanColumn
            key={status}
            status={status}
            jobs={jobs.filter((j) => j.status === status).sort((a, b) => b.dateApplied - a.dateApplied)}
            onEditJob={onEditJob}
            onDeleteJob={onDeleteJob}
          />
        ))}
      </div>

      <DragOverlay>
        {activeJob ? (
          <div className="opacity-90 scale-105 shadow-xl rotate-2">
            <JobCard job={activeJob} onEdit={() => {}} onDelete={() => {}} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
