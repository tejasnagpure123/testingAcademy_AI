import { openDB } from 'idb';
import type { DBSchema, IDBPDatabase } from 'idb';

export type JobStatus = 'Wishlist' | 'Applied' | 'Follow-up' | 'Interview' | 'Offer' | 'Rejected';

export interface Job {
  id: string;
  company: string;
  role: string;
  url?: string;
  resume?: string;
  dateApplied: number; // Unix timestamp
  salary?: string;
  notes?: string;
  status: JobStatus;
  createdAt: number; // Unix timestamp
}

interface JobTrackerDB extends DBSchema {
  jobs: {
    key: string;
    value: Job;
    indexes: { 'by-date': number };
  };
}

const DB_NAME = 'JobTrackerDB';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase<JobTrackerDB>> | null = null;

export const initDB = () => {
  if (!dbPromise) {
    dbPromise = openDB<JobTrackerDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('jobs')) {
          const store = db.createObjectStore('jobs', { keyPath: 'id' });
          store.createIndex('by-date', 'dateApplied');
        }
      },
    });
  }
  return dbPromise;
};

export const getJobs = async (): Promise<Job[]> => {
  const db = await initDB();
  return db.getAll('jobs');
};

export const addJob = async (job: Job): Promise<void> => {
  const db = await initDB();
  await db.put('jobs', job);
};

export const updateJob = async (job: Job): Promise<void> => {
  const db = await initDB();
  await db.put('jobs', job);
};

export const deleteJob = async (id: string): Promise<void> => {
  const db = await initDB();
  await db.delete('jobs', id);
};

export const importJobs = async (jobs: Job[]): Promise<void> => {
  const db = await initDB();
  const tx = db.transaction('jobs', 'readwrite');
  await Promise.all([
    tx.store.clear(),
    ...jobs.map(job => tx.store.put(job)),
    tx.done
  ]);
};
