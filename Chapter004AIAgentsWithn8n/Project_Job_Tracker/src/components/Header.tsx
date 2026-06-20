import React, { useRef } from 'react';
import { Search, Plus, Moon, Sun, Download, Upload } from 'lucide-react';

interface HeaderProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onAddJobClick: () => void;
  onExport: () => void;
  onImport: (file: File) => void;
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

export function Header({
  searchTerm,
  onSearchChange,
  onAddJobClick,
  onExport,
  onImport,
  isDarkMode,
  toggleDarkMode,
}: HeaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImportChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImport(file);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <header className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 md:px-8 border-b border-border bg-card text-card-foreground">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold">
          JT
        </div>
        <h1 className="text-xl font-semibold tracking-tight">Job Tracker</h1>
      </div>

      <div className="flex-1 w-full max-w-md relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by company or role..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full h-10 pl-9 pr-4 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onExport}
          className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          title="Export Data"
        >
          <Download className="w-5 h-5" />
        </button>
        
        <input
          type="file"
          accept=".json"
          ref={fileInputRef}
          onChange={handleImportChange}
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          title="Import Data"
        >
          <Upload className="w-5 h-5" />
        </button>

        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          title="Toggle Theme"
        >
          {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        <button
          onClick={onAddJobClick}
          className="ml-2 h-10 px-4 py-2 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-primary text-primary-foreground hover:bg-primary/90 shadow"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Job
        </button>
      </div>
    </header>
  );
}
