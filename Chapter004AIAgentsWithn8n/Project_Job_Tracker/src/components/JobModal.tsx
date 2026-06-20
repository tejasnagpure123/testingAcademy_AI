import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import type { Job, JobStatus } from '../lib/db';
import { v4 as uuidv4 } from 'uuid';

interface JobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (job: Job) => void;
  jobToEdit?: Job | null;
  existingResumes: string[];
}

const defaultJob: Partial<Job> = {
  company: '',
  role: '',
  url: '',
  resume: '',
  salary: '',
  notes: '',
  status: 'Wishlist',
};

const STATUS_OPTIONS: JobStatus[] = ['Wishlist', 'Applied', 'Follow-up', 'Interview', 'Offer', 'Rejected'];

export function JobModal({ isOpen, onClose, onSave, jobToEdit, existingResumes }: JobModalProps) {
  const [formData, setFormData] = useState<Partial<Job>>(defaultJob);

  useEffect(() => {
    if (isOpen) {
      if (jobToEdit) {
        setFormData(jobToEdit);
      } else {
        setFormData(defaultJob);
      }
    }
  }, [isOpen, jobToEdit]);

  if (!isOpen) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.company || !formData.role) return;

    const jobToSave: Job = {
      id: formData.id || uuidv4(),
      company: formData.company,
      role: formData.role,
      url: formData.url,
      resume: formData.resume,
      salary: formData.salary,
      notes: formData.notes,
      status: formData.status as JobStatus || 'Wishlist',
      dateApplied: formData.dateApplied || Date.now(),
      createdAt: formData.createdAt || Date.now(),
    };

    onSave(jobToSave);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-card text-card-foreground w-full max-w-lg rounded-xl shadow-lg flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold">{jobToEdit ? 'Edit Job' : 'Add New Job'}</h2>
          <button onClick={onClose} className="p-1 rounded-md hover:bg-muted text-muted-foreground transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <form id="job-form" onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 sm:col-span-1 space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Company <span className="text-destructive">*</span></label>
                <input
                  type="text"
                  name="company"
                  required
                  value={formData.company || ''}
                  onChange={handleChange}
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="e.g. Google"
                />
              </div>
              <div className="col-span-2 sm:col-span-1 space-y-2">
                <label className="text-sm font-medium leading-none">Role <span className="text-destructive">*</span></label>
                <input
                  type="text"
                  name="role"
                  required
                  value={formData.role || ''}
                  onChange={handleChange}
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="e.g. Frontend Engineer"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium leading-none">Job URL</label>
              <input
                type="url"
                name="url"
                value={formData.url || ''}
                onChange={handleChange}
                className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="https://linkedin.com/jobs/..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 sm:col-span-1 space-y-2">
                <label className="text-sm font-medium leading-none">Status</label>
                <select
                  name="status"
                  value={formData.status || 'Wishlist'}
                  onChange={handleChange}
                  className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {STATUS_OPTIONS.map(status => (
                    <option key={status} value={status} className="bg-background text-foreground">{status}</option>
                  ))}
                </select>
              </div>
              <div className="col-span-2 sm:col-span-1 space-y-2">
                <label className="text-sm font-medium leading-none">Salary Range</label>
                <input
                  type="text"
                  name="salary"
                  value={formData.salary || ''}
                  onChange={handleChange}
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="e.g. $120k - $150k"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium leading-none">Resume Used</label>
              <input
                type="text"
                name="resume"
                list="resumes-list"
                value={formData.resume || ''}
                onChange={handleChange}
                className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Select or type resume version..."
              />
              <datalist id="resumes-list">
                {existingResumes.map(r => (
                  <option key={r} value={r} />
                ))}
              </datalist>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium leading-none">Notes</label>
              <textarea
                name="notes"
                value={formData.notes || ''}
                onChange={handleChange}
                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Recruiter info, referral details, etc."
              />
            </div>
          </form>
        </div>
        
        <div className="p-4 border-t border-border flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="h-10 px-4 py-2 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors hover:bg-muted hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="job-form"
            className="h-10 px-4 py-2 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-primary text-primary-foreground hover:bg-primary/90 shadow"
          >
            Save Job
          </button>
        </div>
      </div>
    </div>
  );
}
