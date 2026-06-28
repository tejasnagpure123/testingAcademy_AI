import cron, { ScheduledTask } from 'node-cron';
import { runPipeline } from './pipeline';

declare global {
  var schedulerInitialized: boolean | undefined;
  var cronJob: ScheduledTask | undefined;
}

export function initScheduler(): void {
  // Prevent duplicate initialization in Next.js development hot-reloading
  if (global.schedulerInitialized) {
    console.log('[Scheduler] Already initialized. Skipping duplicate setup.');
    return;
  }

  global.schedulerInitialized = true;
  console.log('[Scheduler] Initializing ContentForge daily 9:00 AM schedule...');

  // '0 9 * * *' triggers every day at 9:00 AM local time
  global.cronJob = cron.schedule('0 9 * * *', async () => {
    console.log('[Scheduler] Cron triggered at 9:00 AM. Running pipeline...');
    try {
      await runPipeline();
    } catch (err) {
      console.error('[Scheduler] Cron pipeline execution failed:', err);
    }
  });

  console.log('[Scheduler] Cron job registered successfully. Next run computed dynamically.');
}

// Dynamically compute the next 9:00 AM run time relative to the current local time
export function getNextScheduledTime(): string {
  const now = new Date();
  const nextRun = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 9, 0, 0, 0);
  if (now >= nextRun) {
    nextRun.setDate(nextRun.getDate() + 1);
  }
  return nextRun.toISOString();
}
