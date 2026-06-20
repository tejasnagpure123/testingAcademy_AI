import { useState, useEffect, useCallback } from 'react';
import { getJobs, addJob, updateJob, deleteJob, importJobs } from '../lib/db';
import type { Job } from '../lib/db';

export const useJobs = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getJobs();
      setJobs(data);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleAddJob = async (job: Job) => {
    await addJob(job);
    await fetchJobs();
  };

  const handleUpdateJob = async (job: Job) => {
    await updateJob(job);
    setJobs((prev) => prev.map((j) => (j.id === job.id ? job : j)));
  };

  const handleDeleteJob = async (id: string) => {
    await deleteJob(id);
    setJobs((prev) => prev.filter((j) => j.id !== id));
  };

  const handleImportJobs = async (importedJobs: Job[]) => {
    await importJobs(importedJobs);
    await fetchJobs();
  };

  return {
    jobs,
    loading,
    refreshJobs: fetchJobs,
    addJob: handleAddJob,
    updateJob: handleUpdateJob,
    deleteJob: handleDeleteJob,
    importJobs: handleImportJobs,
  };
};
