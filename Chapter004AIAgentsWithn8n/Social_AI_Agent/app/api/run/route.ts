import { NextResponse } from 'next/server';
import { runPipeline, currentStatus } from '@/lib/pipeline';

export async function POST() {
  if (currentStatus.status === 'running') {
    return NextResponse.json(
      { success: false, message: 'Pipeline is already running.' },
      { status: 409 }
    );
  }

  // Trigger pipeline asynchronously in the background
  runPipeline().catch((err) => {
    console.error('[API /api/run] Async pipeline run failed:', err);
  });

  return NextResponse.json(
    { success: true, message: 'Pipeline triggered in background.' },
    { status: 202 }
  );
}
