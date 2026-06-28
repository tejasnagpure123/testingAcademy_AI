import { NextResponse } from 'next/server';
import { ExcelManager } from '@/lib/excelManager';
import fs from 'fs';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const download = searchParams.get('download');
    
    const excelManager = new ExcelManager();
    
    // Download route
    if (download === 'true') {
      const filePath = excelManager.getFilePath();
      if (!fs.existsSync(filePath)) {
        // If file doesn't exist yet, initialize it
        await excelManager.initialize();
      }
      
      const fileBuffer = await fs.promises.readFile(filePath);
      return new Response(fileBuffer, {
        headers: {
          'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'Content-Disposition': 'attachment; filename="content_calendar.xlsx"',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Normal API route returning JSON data
    const rows = await excelManager.readRows();
    
    // Retrieve file modification time for Excel Log
    let fileModifiedTime = '';
    try {
      const filePath = excelManager.getFilePath();
      if (fs.existsSync(filePath)) {
        fileModifiedTime = fs.statSync(filePath).mtime.toISOString();
      }
    } catch (e) {
      console.warn('[API /api/calendar] Failed to read modified time:', e);
    }

    return NextResponse.json({ 
      success: true, 
      data: rows,
      fileModifiedTime 
    });
  } catch (error: any) {
    console.error('[API /api/calendar] Failed to retrieve calendar data:', error);
    return NextResponse.json(
      { success: false, error: error.message || String(error) },
      { status: 500 }
    );
  }
}
