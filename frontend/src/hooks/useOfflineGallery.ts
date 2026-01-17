/**
 * useOfflineGallery Hook
 * Manages offline gallery state: download, list cached galleries, clear cache
 * Integrates with offlineService for IndexedDB storage operations
 */

import { useState, useCallback, useEffect } from 'react';
import {
  offlineService,
  type DownloadProgress,
  type DownloadOptions,
  type OfflineGalleryInfo,
} from '../services/offlineService';

// ============================================
// Types
// ============================================

export interface StorageStats {
  usage_mb: number;
  quota_mb: number;
  available_mb: number;
  percentage_used: number;
  gallery_count: number;
  total_gallery_size_mb: number;
}

export interface UseOfflineGalleryOptions {
  workspaceId?: string;
  onDownloadComplete?: (galleryId: string) => void;
  onDownloadError?: (galleryId: string, error: string) => void;
  onDeleteComplete?: (galleryId: string) => void;
}

export interface UseOfflineGalleryReturn {
  // Download state
  isDownloading: boolean;
  downloadProgress: DownloadProgress | null;

  // Gallery list state
  downloadedGalleries: OfflineGalleryInfo[];
  isLoadingGalleries: boolean;

  // Storage stats
  storageStats: StorageStats | null;
  isLoadingStats: boolean;

  // Actions
  downloadGallery: (galleryId: string, options?: DownloadOptions) => Promise<boolean>;
  deleteGallery: (galleryId: string) => Promise<boolean>;
  refreshGalleryList: () => Promise<void>;
  refreshStorageStats: () => Promise<void>;
  clearAllOfflineData: () => Promise<boolean>;
  isGalleryAvailableOffline: (galleryId: string) => Promise<boolean>;

  // Errors
  error: string | null;
  clearError: () => void;
}

// ============================================
// Hook
// ============================================

export function useOfflineGallery(
  options: UseOfflineGalleryOptions = {}
): UseOfflineGalleryReturn {
  const { workspaceId, onDownloadComplete, onDownloadError, onDeleteComplete } = options;

  // Download state
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);

  // Gallery list state
  const [downloadedGalleries, setDownloadedGalleries] = useState<OfflineGalleryInfo[]>([]);
  const [isLoadingGalleries, setIsLoadingGalleries] = useState(false);

  // Storage stats state
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Refresh gallery list
  const refreshGalleryList = useCallback(async () => {
    if (!workspaceId) {
      return;
    }

    setIsLoadingGalleries(true);
    setError(null);

    try {
      const galleries = await offlineService.getDownloadedGalleries(workspaceId);
      setDownloadedGalleries(galleries);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load galleries';
      setError(errorMessage);
    } finally {
      setIsLoadingGalleries(false);
    }
  }, [workspaceId]);

  // Refresh storage stats
  const refreshStorageStats = useCallback(async () => {
    setIsLoadingStats(true);
    setError(null);

    try {
      const stats = await offlineService.getStorageStats();
      setStorageStats(stats);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load storage stats';
      setError(errorMessage);
    } finally {
      setIsLoadingStats(false);
    }
  }, []);

  // Download a gallery for offline access
  const downloadGallery = useCallback(
    async (galleryId: string, downloadOptions: DownloadOptions = {}): Promise<boolean> => {
      setIsDownloading(true);
      setError(null);
      setDownloadProgress(null);

      try {
        await offlineService.downloadGallery(galleryId, {
          ...downloadOptions,
          onProgress: (progress) => {
            setDownloadProgress(progress);
            downloadOptions.onProgress?.(progress);
          },
        });

        // Refresh gallery list and storage stats after successful download
        await Promise.all([refreshGalleryList(), refreshStorageStats()]);

        onDownloadComplete?.(galleryId);
        return true;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Download failed';
        setError(errorMessage);
        onDownloadError?.(galleryId, errorMessage);
        return false;
      } finally {
        setIsDownloading(false);
        setDownloadProgress(null);
      }
    },
    [refreshGalleryList, refreshStorageStats, onDownloadComplete, onDownloadError]
  );

  // Delete a gallery from offline storage
  const deleteGallery = useCallback(
    async (galleryId: string): Promise<boolean> => {
      setError(null);

      try {
        await offlineService.deleteOfflineGallery(galleryId);

        // Refresh gallery list and storage stats after deletion
        await Promise.all([refreshGalleryList(), refreshStorageStats()]);

        onDeleteComplete?.(galleryId);
        return true;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete gallery';
        setError(errorMessage);
        return false;
      }
    },
    [refreshGalleryList, refreshStorageStats, onDeleteComplete]
  );

  // Clear all offline data
  const clearAllOfflineData = useCallback(async (): Promise<boolean> => {
    setError(null);

    try {
      await offlineService.clearAllOfflineData();

      // Refresh gallery list and storage stats after clearing
      await Promise.all([refreshGalleryList(), refreshStorageStats()]);

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to clear offline data';
      setError(errorMessage);
      return false;
    }
  }, [refreshGalleryList, refreshStorageStats]);

  // Check if a gallery is available offline
  const isGalleryAvailableOffline = useCallback(
    async (galleryId: string): Promise<boolean> => {
      try {
        return await offlineService.isGalleryAvailableOffline(galleryId);
      } catch (err) {
        return false;
      }
    },
    []
  );

  // Load initial data when workspaceId changes
  useEffect(() => {
    if (workspaceId) {
      refreshGalleryList();
    }
  }, [workspaceId, refreshGalleryList]);

  // Load storage stats on mount
  useEffect(() => {
    refreshStorageStats();
  }, [refreshStorageStats]);

  return {
    // Download state
    isDownloading,
    downloadProgress,

    // Gallery list state
    downloadedGalleries,
    isLoadingGalleries,

    // Storage stats
    storageStats,
    isLoadingStats,

    // Actions
    downloadGallery,
    deleteGallery,
    refreshGalleryList,
    refreshStorageStats,
    clearAllOfflineData,
    isGalleryAvailableOffline,

    // Errors
    error,
    clearError,
  };
}

export default useOfflineGallery;
