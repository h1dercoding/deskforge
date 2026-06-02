'use client';

import React, { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { ALLOWED_CSV_TYPES, MAX_FILE_SIZE } from '@/lib/constants';
import { toast } from '@/hooks/useToast';

interface CsvUploadProps {
  onUpload: (file: File) => void;
  isLoading?: boolean;
}

export function CsvUpload({ onUpload, isLoading }: CsvUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const validateFile = (file: File): boolean => {
    if (!ALLOWED_CSV_TYPES.includes(file.type) && !file.name.match(/\.(csv|xlsx|xls)$/i)) {
      toast({ title: 'Invalid file type', description: 'Please upload a CSV or Excel file.', variant: 'destructive' });
      return false;
    }
    if (file.size > MAX_FILE_SIZE) {
      toast({ title: 'File too large', description: 'Maximum file size is 25MB.', variant: 'destructive' });
      return false;
    }
    return true;
  };

  const handleFile = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    },
    []
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  return (
    <div className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-muted-foreground/50',
          isLoading && 'opacity-50 pointer-events-none'
        )}
        onClick={() => document.getElementById('csv-upload')?.click()}
      >
        <input
          id="csv-upload"
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleInputChange}
          className="hidden"
        />
        {selectedFile ? (
          <div className="flex items-center justify-center gap-3">
            <FileSpreadsheet className="h-8 w-8 text-primary" />
            <div className="text-left">
              <p className="font-medium">{selectedFile.name}</p>
              <p className="text-sm text-muted-foreground">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <>
            <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
            <p className="text-sm font-medium mb-1">
              Drop your CSV or Excel file here, or click to browse
            </p>
            <p className="text-xs text-muted-foreground">
              Supports .csv, .xlsx, .xls files up to 25MB
            </p>
          </>
        )}
      </div>

      {selectedFile && (
        <Button onClick={handleSubmit} disabled={isLoading} className="w-full">
          {isLoading ? 'Uploading...' : 'Upload & Process'}
        </Button>
      )}
    </div>
  );
}
