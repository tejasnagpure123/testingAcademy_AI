import ExcelJS from 'exceljs';
import fs from 'fs';
import path from 'path';
import { ContentRow } from './types';

class Mutex {
  private queue: Promise<void> = Promise.resolve();

  async runExclusive<T>(callback: () => Promise<T>): Promise<T> {
    let release: () => void;
    const next = new Promise<void>((resolve) => {
      release = resolve;
    });
    const current = this.queue;
    this.queue = current.then(() => next);
    await current;
    try {
      return await callback();
    } finally {
      release!();
    }
  }
}

export class ExcelManager {
  private filePath: string;
  private mutex = new Mutex();

  constructor(filePath?: string) {
    this.filePath = filePath || path.join(process.cwd(), 'content_calendar.xlsx');
  }

  // Ensure file and worksheet exist with correct headers
  async initialize(): Promise<void> {
    return this.mutex.runExclusive(async () => {
      if (!fs.existsSync(this.filePath)) {
        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet('Content Calendar');
        
        // Define columns
        worksheet.columns = [
          { header: 'Date', key: 'date', width: 15 },
          { header: 'Topic', key: 'topic', width: 30 },
          { header: 'LinkedIn POST', key: 'linkedinPost', width: 40 },
          { header: 'Medium Article', key: 'mediumArticle', width: 40 },
          { header: 'IG Script', key: 'igScript', width: 40 },
          { header: 'YT Script', key: 'ytScript', width: 40 },
          { header: 'Dev.to Article', key: 'devtoArticle', width: 40 },
          { header: 'Status', key: 'status', width: 15 },
          { header: 'LinkedIn Image', key: 'linkedinImage', width: 25 },
          { header: 'Medium Image', key: 'mediumImage', width: 25 },
          { header: 'IG Image', key: 'igImage', width: 25 },
          { header: 'Last Updated', key: 'lastUpdated', width: 25 },
          { header: 'Written By', key: 'writtenBy', width: 15 }
        ];

        // Format header row
        worksheet.getRow(1).font = { bold: true };
        worksheet.getRow(1).fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: 'FFEAEAEA' }
        };

        await workbook.xlsx.writeFile(this.filePath);
      }
    });
  }

  // Read all rows
  async readRows(): Promise<ContentRow[]> {
    return this.mutex.runExclusive(async () => {
      await this.ensureInitializedInternal();
      
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.readFile(this.filePath);
      const worksheet = workbook.getWorksheet('Content Calendar');
      if (!worksheet) return [];

      const rows: ContentRow[] = [];
      worksheet.eachRow((row, rowNumber) => {
        if (rowNumber === 1) return; // Skip headers
        
        const getVal = (col: number): string => {
          const val = row.getCell(col).value;
          if (val === null || val === undefined) return '';
          if (typeof val === 'object' && 'text' in val) return (val as any).text || '';
          return String(val);
        };

        rows.push({
          date: getVal(1),
          topic: getVal(2),
          linkedinPost: getVal(3),
          mediumArticle: getVal(4),
          igScript: getVal(5),
          ytScript: getVal(6),
          devtoArticle: getVal(7),
          status: (getVal(8) || 'Pending') as ContentRow['status'],
          linkedinImage: getVal(9),
          mediumImage: getVal(10),
          igImage: getVal(11),
          lastUpdated: getVal(12),
          writtenBy: getVal(13),
        });
      });

      return rows;
    });
  }

  // Save/update a specific row by date
  async saveRow(rowToSave: ContentRow): Promise<void> {
    return this.mutex.runExclusive(async () => {
      await this.ensureInitializedInternal();
      
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.readFile(this.filePath);
      let worksheet = workbook.getWorksheet('Content Calendar');
      if (!worksheet) {
        worksheet = workbook.addWorksheet('Content Calendar');
      }

      // Search for existing row with matching date
      let targetRowNumber = -1;
      worksheet.eachRow((row, rowNumber) => {
        if (rowNumber === 1) return;
        const cellVal = row.getCell(1).value;
        if (cellVal && String(cellVal) === rowToSave.date) {
          targetRowNumber = rowNumber;
        }
      });

      const lastUpdatedStr = new Date().toISOString();
      const rowData = [
        rowToSave.date,
        rowToSave.topic,
        rowToSave.linkedinPost || '',
        rowToSave.mediumArticle || '',
        rowToSave.igScript || '',
        rowToSave.ytScript || '',
        rowToSave.devtoArticle || '',
        rowToSave.status,
        rowToSave.linkedinImage || '',
        rowToSave.mediumImage || '',
        rowToSave.igImage || '',
        rowToSave.lastUpdated || lastUpdatedStr,
        rowToSave.writtenBy || ''
      ];

      if (targetRowNumber !== -1) {
        const row = worksheet.getRow(targetRowNumber);
        for (let i = 0; i < rowData.length; i++) {
          row.getCell(i + 1).value = rowData[i];
        }
        row.commit();
      } else {
        worksheet.addRow(rowData);
      }

      await workbook.xlsx.writeFile(this.filePath);
    });
  }

  // Internal helper that runs WITHOUT acquiring mutex (since it's called inside mutex calls)
  private async ensureInitializedInternal(): Promise<void> {
    if (!fs.existsSync(this.filePath)) {
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Content Calendar');
      worksheet.columns = [
        { header: 'Date', key: 'date', width: 15 },
        { header: 'Topic', key: 'topic', width: 30 },
        { header: 'LinkedIn POST', key: 'linkedinPost', width: 40 },
        { header: 'Medium Article', key: 'mediumArticle', width: 40 },
        { header: 'IG Script', key: 'igScript', width: 40 },
        { header: 'YT Script', key: 'ytScript', width: 40 },
        { header: 'Dev.to Article', key: 'devtoArticle', width: 40 },
        { header: 'Status', key: 'status', width: 15 },
        { header: 'LinkedIn Image', key: 'linkedinImage', width: 25 },
        { header: 'Medium Image', key: 'mediumImage', width: 25 },
        { header: 'IG Image', key: 'igImage', width: 25 },
        { header: 'Last Updated', key: 'lastUpdated', width: 25 },
        { header: 'Written By', key: 'writtenBy', width: 15 }
      ];
      worksheet.getRow(1).font = { bold: true };
      worksheet.getRow(1).fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFEAEAEA' }
      };
      await workbook.xlsx.writeFile(this.filePath);
    }
  }

  // Get Excel file path for download
  getFilePath(): string {
    return this.filePath;
  }
}
