import { useState, useEffect, useMemo } from 'react';
import { Header } from './components/Header';
import { KanbanBoard } from './components/KanbanBoard';
import { JobModal } from './components/JobModal';
import { useJobs } from './hooks/useJobs';
import type { Job } from './lib/db';
import { exportToJson } from './lib/utils';

function App() {
  const { jobs, loading, addJob, updateJob, deleteJob, importJobs } = useJobs();
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.classList.contains('dark') || 
        window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });
  const [searchTerm, setSearchTerm] = useState('');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [jobToEdit, setJobToEdit] = useState<Job | null>(null);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

  const handleOpenAddModal = () => {
    setJobToEdit(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (job: Job) => {
    setJobToEdit(job);
    setIsModalOpen(true);
  };

  const handleSaveJob = async (job: Job) => {
    if (jobToEdit) {
      await updateJob(job);
    } else {
      await addJob(job);
    }
  };

  const handleExport = () => {
    exportToJson(jobs, `job-tracker-export-${new Date().toISOString().split('T')[0]}.json`);
  };

  const handleImport = async (file: File) => {
    try {
      const { importFromJson } = await import('./lib/utils');
      const importedData = await importFromJson(file);
      if (Array.isArray(importedData)) {
        await importJobs(importedData as Job[]);
        alert('Jobs imported successfully!');
      } else {
        alert('Invalid file format. Please upload a valid JSON array.');
      }
    } catch (error) {
      console.error(error);
      alert('Failed to import jobs.');
    }
  };

  const filteredJobs = useMemo(() => {
    if (!searchTerm) return jobs;
    const lowerSearch = searchTerm.toLowerCase();
    return jobs.filter(
      (job) =>
        job.company.toLowerCase().includes(lowerSearch) ||
        job.role.toLowerCase().includes(lowerSearch)
    );
  }, [jobs, searchTerm]);

  const existingResumes = useMemo(() => {
    const resumes = new Set<string>();
    jobs.forEach(j => {
      if (j.resume) resumes.add(j.resume);
    });
    return Array.from(resumes);
  }, [jobs]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      <Header
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onAddJobClick={handleOpenAddModal}
        onExport={handleExport}
        onImport={handleImport}
        isDarkMode={isDarkMode}
        toggleDarkMode={toggleDarkMode}
      />
      
      <main className="flex-1 overflow-hidden flex flex-col relative">
        <div className="absolute inset-0">
          <KanbanBoard
            jobs={filteredJobs}
            onUpdateJob={updateJob}
            onEditJob={handleOpenEditModal}
            onDeleteJob={deleteJob}
          />
        </div>
      </main>

      <JobModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveJob}
        jobToEdit={jobToEdit}
        existingResumes={existingResumes}
      />
    </div>
  );
}

export default App;
