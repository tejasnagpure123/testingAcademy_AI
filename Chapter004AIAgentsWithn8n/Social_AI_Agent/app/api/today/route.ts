import { NextResponse } from 'next/server';
import { ExcelManager } from '@/lib/excelManager';
import { getTodayDateString } from '@/lib/agents';

export async function GET() {
  try {
    const excelManager = new ExcelManager();
    const rows = await excelManager.readRows();
    const todayStr = getTodayDateString();
    
    const todayRow = rows.find((r) => r.date === todayStr) || null;
    
    return NextResponse.json({ 
      success: true, 
      data: todayRow 
    });
  } catch (error: any) {
    console.error('[API /api/today] Failed to read today\'s content row:', error);
    return NextResponse.json(
      { success: false, error: error.message || String(error) },
      { status: 500 }
    );
  }
}
