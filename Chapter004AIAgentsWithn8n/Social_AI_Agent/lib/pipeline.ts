import { ExcelManager } from './excelManager';
import { runAgent1TopicGenerator, runAgent2ContentWriter, runAgent3ImageGenerator, getTodayDateString } from './agents';
import { PipelineStatus } from './types';

// Global in-memory pipeline status
export let currentStatus: PipelineStatus = {
  status: 'idle',
  currentStep: 'idle',
};

const excelManager = new ExcelManager();

export async function runPipeline(): Promise<void> {
  if (currentStatus.status === 'running') {
    console.log('[Pipeline] Run requested, but pipeline is already running.');
    return;
  }

  console.log('[Pipeline] Starting content pipeline execution...');
  currentStatus = {
    status: 'running',
    currentStep: 'topic_generation',
    lastRunTime: new Date().toISOString(),
    error: undefined,
  };

  try {
    // 1. Initialize spreadsheet first
    await excelManager.initialize();

    // 2. Step 1: Topic Generation
    await runAgent1TopicGenerator(excelManager);

    // 3. Step 2: Content Writing
    currentStatus.currentStep = 'content_writing';
    await runAgent2ContentWriter(excelManager);

    // 4. Step 3: Image Generation
    currentStatus.currentStep = 'image_generation';
    await runAgent3ImageGenerator(excelManager);

    // 5. Success
    currentStatus.status = 'success';
    currentStatus.currentStep = 'done';
    console.log('[Pipeline] Content pipeline completed successfully!');
  } catch (error: any) {
    const errorMsg = error?.message || String(error);
    console.error(`[Pipeline] Content pipeline failed at step "${currentStatus.currentStep}":`, errorMsg);
    
    currentStatus.status = 'error';
    currentStatus.currentStep = 'error';
    currentStatus.error = errorMsg;

    // Graceful fallback: set status to 'Error' for today's row in excel
    try {
      const todayStr = getTodayDateString();
      const rows = await excelManager.readRows();
      const todayRow = rows.find(r => r.date === todayStr);
      if (todayRow) {
        todayRow.status = 'Error';
        todayRow.lastUpdated = new Date().toISOString();
        todayRow.writtenBy = 'Pipeline Orchestration';
        await excelManager.saveRow(todayRow);
        console.log('[Pipeline] Successfully marked today\'s Excel row as Error.');
      }
    } catch (saveError) {
      console.error('[Pipeline] Failed to mark Excel row as Error:', saveError);
    }
  }
}
