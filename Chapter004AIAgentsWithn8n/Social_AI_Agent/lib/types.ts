export interface ContentRow {
  date: string; // YYYY-MM-DD
  topic: string;
  linkedinPost?: string;
  mediumArticle?: string;
  igScript?: string;
  ytScript?: string;
  devtoArticle?: string;
  status: 'Pending' | 'Writing' | 'Imaging' | 'Done' | 'Error';
  linkedinImage?: string;
  mediumImage?: string;
  igImage?: string;
  lastUpdated?: string; // Excel log metadata
  writtenBy?: string;  // Excel log metadata
}

export type PipelineStep = 'idle' | 'topic_generation' | 'content_writing' | 'image_generation' | 'done' | 'error';
export type PipelineRunStatus = 'idle' | 'running' | 'success' | 'error';

export interface PipelineStatus {
  status: PipelineRunStatus;
  currentStep: PipelineStep;
  lastRunTime?: string;
  error?: string;
}

export interface ApiKeyStatus {
  groq: boolean;
  gemini: boolean;
}

export interface ExcelLogEntry {
  row: number;
  date: string;
  topic: string;
  what: string; // Detail of what was updated (e.g. LinkedIn post, Medium article, images, etc.)
  when: string; // Timestamp
  how: string;  // Which agent did the update
}
