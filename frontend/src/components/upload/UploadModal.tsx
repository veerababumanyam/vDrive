import { useState, useCallback, useRef } from 'react';
import { createTusUpload, getUploadStatus } from '../../services/upload-api';

import { batchAddAssets } from '../../services/gallery-api';
import { AppCard } from '../ui/AppCard';
import { cn } from '../../lib/utils';
import { useHaptic } from '../../hooks';
import * as tus from 'tus-js-client';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  galleryId: string;
  workspaceId: string; // Needed for upload service
  onUploadComplete: () => void;
}

interface FileUploadState {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  uploadId?: string;
  tusUpload?: tus.Upload;
}

export function UploadModal({
  isOpen,
  onClose,
  galleryId,
  workspaceId,
  onUploadComplete,
}: UploadModalProps) {
  const [uploads, setUploads] = useState<FileUploadState[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const haptic = useHaptic();

  // Helper to update specific upload state
  const updateUpload = useCallback((fileName: string, update: Partial<FileUploadState>) => {
    setUploads((prev) =>
      prev.map((u) => (u.file.name === fileName ? { ...u, ...update } : u))
    );
  }, []);

  // Poll for processing status
  const pollStatus = useCallback(async (uploadId: string, fileName: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await getUploadStatus(uploadId);
        
        if (status.asset_id) {
          // Asset created successfully
          clearInterval(pollInterval);
          
          // Link to gallery
          try {
            await batchAddAssets(
                [status.asset_id], 
                galleryId, 
                workspaceId
            );
            
            updateUpload(fileName, { status: 'completed', progress: 100 });
            haptic.success();
            onUploadComplete(); // Trigger refresh
          } catch (err) {
            updateUpload(fileName, { 
                status: 'error', 
                error: 'Failed to add to gallery' 
            });
          }
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          updateUpload(fileName, { status: 'error', error: 'Processing failed' });
        }
      } catch (err) {
        // Ignore minor polling errors
      }
    }, 2000); // Poll every 2s

    // Cleanup after 30s timeout
    setTimeout(() => {
        clearInterval(pollInterval);
        // Don't mark as error necessarily, maybe just taking loong
    }, 30000);
  }, [galleryId, workspaceId, updateUpload, haptic, onUploadComplete]);

  // Start upload for a file
  const startUpload = useCallback((file: File) => {
    const tusUpload = createTusUpload(
      file,
      workspaceId,
      (progress) => {
        updateUpload(file.name, { progress: progress.percentage });
      },
      (uploadId) => {
        updateUpload(file.name, { status: 'processing', uploadId });
        pollStatus(uploadId, file.name);
      },
      (error) => {
        updateUpload(file.name, { status: 'error', error: error.message });
      }
    );

    updateUpload(file.name, { status: 'uploading', tusUpload });
    tusUpload.start();
  }, [workspaceId, updateUpload, pollStatus]);

  // Add files to queue and start upload
  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;

    const newUploads: FileUploadState[] = Array.from(files).map((file) => ({
      file,
      progress: 0,
      status: 'pending',
    }));

    setUploads((prev) => [...prev, ...newUploads]);

    // Start uploads immediately
    newUploads.forEach((u) => {
        // Hack to ensure state is set before starting? 
        // Actually startUpload needs the state to exist for updateUpload to work?
        // No, updateUpload maps over previous state.
        // But we need to make sure this newUpload is IN the state.
        
        // Let's use a timeout or useEffect or just rely on the fact that setState is batched
        // Better: separate start logic
        setTimeout(() => startUpload(u.file), 100);
    });
  }, [startUpload]);

  // Drag and drop handlers
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <AppCard
        variant="premiumGlass"
        padding="lg"
        className="w-full max-w-xl animate-scale-up max-h-[80vh] flex flex-col"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-neutral-800 dark:text-white">
            Upload Photos
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-full text-neutral-500 hover:text-neutral-700 dark:hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
          </button>
        </div>

        {/* Drop Zone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={cn(
            'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
            isDragOver
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10'
              : 'border-neutral-300 dark:border-neutral-700 hover:border-primary-400 hover:bg-neutral-50 dark:hover:bg-white/5'
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,video/*"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          <div className="w-12 h-12 mx-auto mb-3 text-neutral-400">
            <svg viewBox="0 0 24 24" fill="currentColor">
               <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
            </svg>
          </div>
          <p className="text-neutral-600 dark:text-neutral-300 font-medium">
            Click to upload or drag and drop
          </p>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            JPG, PNG, WebP, MP4 (max 10GB)
          </p>
        </div>

        {/* Upload List */}
        {uploads.length > 0 && (
          <div className="mt-6 flex-1 overflow-y-auto space-y-3 min-h-0">
            {uploads.map((u, i) => (
              <div
                key={i}
                className="flex items-center gap-3 p-3 rounded-lg bg-neutral-50 dark:bg-white/5 border border-neutral-200 dark:border-white/10"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium truncate">{u.file.name}</span>
                    <span className={cn(
                        "text-xs",
                        u.status === 'error' ? 'text-red-500' : 
                        u.status === 'completed' ? 'text-emerald-500' : 'text-neutral-500'
                    )}>
                      {u.status === 'error' ? u.error : 
                       u.status === 'completed' ? 'Done' : 
                       u.status === 'processing' ? 'Processing...' : 
                       `${Math.round(u.progress)}%`}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-neutral-200 dark:bg-white/10 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full transition-all duration-300",
                        u.status === 'error' ? 'bg-red-500' :
                        u.status === 'completed' ? 'bg-emerald-500' :
                        u.status === 'processing' ? 'bg-amber-500' : 'bg-primary-500'
                      )}
                      style={{ width: `${u.progress}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </AppCard>
    </div>
  );
}
