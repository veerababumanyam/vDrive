/**
 * OfflineManager Component
 * Manages offline gallery downloads, storage, and cache
 *
 * Phase 4: Offline UI Components
 * Subtask 4-1: Create OfflineManager component for gallery selection
 */

import { useState, useCallback, useEffect } from 'react';
import { useOfflineGallery } from '../hooks/useOfflineGallery';
import { offlineService, type GalleryMetadata } from '../services/offlineService';
import { AppButton } from './ui/AppButton';
import { AppCard } from './ui/AppCard';
import { cn } from '../lib/utils';

// ============================================
// Icons
// ============================================

function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

function ImageIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  );
}

function DatabaseIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface OfflineManagerProps {
  /** Current workspace ID */
  workspaceId: string;
  /** Additional class names */
  className?: string;
}

// ============================================
// Component
// ============================================

export function OfflineManager({ workspaceId, className }: OfflineManagerProps) {
  const [availableGalleries, setAvailableGalleries] = useState<GalleryMetadata[]>([]);
  const [isLoadingAvailable, setIsLoadingAvailable] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const {
    isDownloading,
    downloadProgress,
    downloadedGalleries,
    isLoadingGalleries,
    storageStats,
    isLoadingStats,
    downloadGallery,
    deleteGallery,
    clearAllOfflineData,
    error: offlineError,
    clearError,
  } = useOfflineGallery({
    workspaceId,
    onDownloadComplete: (galleryId) => {
      console.log(`Gallery ${galleryId} downloaded successfully`);
    },
    onDownloadError: (galleryId, error) => {
      console.error(`Failed to download gallery ${galleryId}:`, error);
    },
    onDeleteComplete: (galleryId) => {
      console.log(`Gallery ${galleryId} deleted from offline storage`);
    },
  });

  // Fetch available galleries from API
  const fetchAvailableGalleries = useCallback(async () => {
    setIsLoadingAvailable(true);
    setFetchError(null);

    try {
      const galleries = await offlineService.fetchAvailableGalleries(workspaceId);
      setAvailableGalleries(galleries);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load galleries';
      setFetchError(errorMessage);
    } finally {
      setIsLoadingAvailable(false);
    }
  }, [workspaceId]);

  // Load available galleries on mount
  useEffect(() => {
    fetchAvailableGalleries();
  }, [fetchAvailableGalleries]);

  // Handle download button click
  const handleDownload = useCallback(
    async (galleryId: string) => {
      await downloadGallery(galleryId, {
        includeFullResolution: false, // Only download previews by default
        includePreview: true,
        includeThumbnail: true,
      });
    },
    [downloadGallery]
  );

  // Handle delete button click
  const handleDelete = useCallback(
    async (galleryId: string) => {
      if (confirm('Are you sure you want to remove this gallery from offline storage?')) {
        await deleteGallery(galleryId);
      }
    },
    [deleteGallery]
  );

  // Handle clear all button click
  const handleClearAll = useCallback(async () => {
    if (
      confirm(
        'Are you sure you want to clear all offline data? This will remove all downloaded galleries.'
      )
    ) {
      await clearAllOfflineData();
    }
  }, [clearAllOfflineData]);

  // Check if a gallery is already downloaded
  const isGalleryDownloaded = useCallback(
    (galleryId: string): boolean => {
      return downloadedGalleries.some((g) => g.gallery.gallery_id === galleryId);
    },
    [downloadedGalleries]
  );

  // Get downloaded gallery info
  const getDownloadedInfo = useCallback(
    (galleryId: string) => {
      return downloadedGalleries.find((g) => g.gallery.gallery_id === galleryId);
    },
    [downloadedGalleries]
  );

  const error = offlineError || fetchError;

  return (
    <div className={cn('max-w-6xl mx-auto space-y-6', className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white">
            Offline Galleries
          </h1>
          <p className="mt-1 text-sm sm:text-base text-neutral-600 dark:text-white/70">
            Download galleries to view them without an internet connection
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <AppCard variant="glass" padding="md">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-5 h-5 rounded-full bg-error-500/20 flex items-center justify-center">
              <span className="text-error-500 text-sm">!</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-error-600 dark:text-error-400">{error}</p>
            </div>
            <button
              onClick={clearError}
              className="flex-shrink-0 text-neutral-400 hover:text-neutral-600 dark:hover:text-white/70"
            >
              <span className="sr-only">Dismiss</span>
              <span className="text-lg">&times;</span>
            </button>
          </div>
        </AppCard>
      )}

      {/* Storage Stats */}
      <AppCard variant="glass" padding="lg">
        <div className="flex items-center gap-3 mb-4">
          <DatabaseIcon className="w-6 h-6 text-primary-500" />
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
            Storage Usage
          </h2>
        </div>

        {isLoadingStats ? (
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-neutral-200 dark:bg-white/10 rounded w-full" />
            <div className="h-4 bg-neutral-200 dark:bg-white/10 rounded w-3/4" />
          </div>
        ) : storageStats ? (
          <div className="space-y-4">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-neutral-600 dark:text-white/70">
                  {storageStats.usage_mb.toFixed(1)} MB of {storageStats.quota_mb.toFixed(0)} MB
                  used
                </span>
                <span className="text-neutral-600 dark:text-white/70">
                  {storageStats.percentage_used.toFixed(1)}%
                </span>
              </div>
              <div className="h-2 bg-neutral-200 dark:bg-white/10 rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full transition-all duration-300 rounded-full',
                    storageStats.percentage_used > 90
                      ? 'bg-error-500'
                      : storageStats.percentage_used > 70
                        ? 'bg-warning-500'
                        : 'bg-primary-500'
                  )}
                  style={{ width: `${Math.min(storageStats.percentage_used, 100)}%` }}
                />
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <p className="text-xs text-neutral-500 dark:text-white/50">Downloaded Galleries</p>
                <p className="text-xl font-semibold text-neutral-900 dark:text-white">
                  {storageStats.gallery_count}
                </p>
              </div>
              <div>
                <p className="text-xs text-neutral-500 dark:text-white/50">Total Size</p>
                <p className="text-xl font-semibold text-neutral-900 dark:text-white">
                  {storageStats.total_gallery_size_mb.toFixed(1)} MB
                </p>
              </div>
            </div>

            {/* Clear All Button */}
            {storageStats.gallery_count > 0 && (
              <div className="pt-2">
                <AppButton
                  variant="outline"
                  size="sm"
                  leftIcon={<TrashIcon className="w-4 h-4" />}
                  onClick={handleClearAll}
                  fullWidth
                >
                  Clear All Offline Data
                </AppButton>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-neutral-500 dark:text-white/50">
            Unable to load storage statistics
          </p>
        )}
      </AppCard>

      {/* Download Progress */}
      {isDownloading && downloadProgress && (
        <AppCard variant="neon" padding="lg">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-neutral-900 dark:text-white">
                Downloading: {downloadProgress.gallery_name}
              </h3>
              <span className="text-sm text-neutral-600 dark:text-white/70">
                {downloadProgress.percentage.toFixed(0)}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-neutral-200 dark:bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 transition-all duration-300 rounded-full"
                style={{ width: `${downloadProgress.percentage}%` }}
              />
            </div>

            <div className="flex justify-between text-xs text-neutral-500 dark:text-white/50">
              <span>
                {downloadProgress.downloaded_photos} / {downloadProgress.total_photos} photos
              </span>
              <span>
                {(downloadProgress.downloaded_bytes / 1024 / 1024).toFixed(1)} /{' '}
                {(downloadProgress.total_bytes / 1024 / 1024).toFixed(1)} MB
              </span>
            </div>
          </div>
        </AppCard>
      )}

      {/* Downloaded Galleries */}
      {downloadedGalleries.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
            Available Offline
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {downloadedGalleries.map(({ gallery, photo_count, size_mb, last_synced }) => (
              <AppCard
                key={gallery.gallery_id}
                variant="glass"
                padding="md"
                hoverable
                className="group"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary-500/10 dark:bg-primary-500/20 flex items-center justify-center">
                    <CheckCircleIcon className="w-5 h-5 text-primary-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-neutral-900 dark:text-white truncate">
                      {gallery.name}
                    </h3>
                    <p className="text-sm text-neutral-500 dark:text-white/50 mt-1">
                      {photo_count} photos • {size_mb.toFixed(1)} MB
                    </p>
                    <p className="text-xs text-neutral-400 dark:text-white/40 mt-1">
                      Synced {new Date(last_synced).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="mt-4">
                  <AppButton
                    variant="outline"
                    size="sm"
                    leftIcon={<TrashIcon className="w-4 h-4" />}
                    onClick={() => handleDelete(gallery.gallery_id)}
                    fullWidth
                  >
                    Remove
                  </AppButton>
                </div>
              </AppCard>
            ))}
          </div>
        </div>
      )}

      {/* Available Galleries */}
      <div>
        <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
          Available to Download
        </h2>

        {isLoadingAvailable || isLoadingGalleries ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <AppCard key={i} variant="glass" padding="md">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-neutral-200 dark:bg-white/10 rounded w-3/4" />
                  <div className="h-3 bg-neutral-200 dark:bg-white/10 rounded w-1/2" />
                  <div className="h-10 bg-neutral-200 dark:bg-white/10 rounded" />
                </div>
              </AppCard>
            ))}
          </div>
        ) : availableGalleries.length === 0 ? (
          <AppCard variant="glass" padding="lg">
            <div className="text-center py-8">
              <ImageIcon className="w-12 h-12 mx-auto text-neutral-400 dark:text-white/30 mb-3" />
              <h3 className="text-lg font-medium text-neutral-900 dark:text-white mb-1">
                No galleries found
              </h3>
              <p className="text-sm text-neutral-500 dark:text-white/50">
                Create a gallery to get started with offline access
              </p>
            </div>
          </AppCard>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {availableGalleries.map((gallery) => {
              const isDownloaded = isGalleryDownloaded(gallery.id);
              const downloadedInfo = getDownloadedInfo(gallery.id);

              return (
                <AppCard
                  key={gallery.id}
                  variant="glass"
                  padding="md"
                  hoverable
                  className="group"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-neutral-200 dark:bg-white/10 flex items-center justify-center">
                      <ImageIcon className="w-5 h-5 text-neutral-500 dark:text-white/50" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-neutral-900 dark:text-white truncate">
                        {gallery.name}
                      </h3>
                      <p className="text-sm text-neutral-500 dark:text-white/50 mt-1">
                        {gallery.photo_count} photos
                      </p>
                      {gallery.description && (
                        <p className="text-xs text-neutral-400 dark:text-white/40 mt-1 line-clamp-2">
                          {gallery.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-4">
                    {isDownloaded ? (
                      <div className="flex items-center gap-2 text-sm text-primary-600 dark:text-primary-400">
                        <CheckCircleIcon className="w-4 h-4" />
                        <span>Available offline</span>
                      </div>
                    ) : (
                      <AppButton
                        variant="primary"
                        size="sm"
                        leftIcon={<DownloadIcon className="w-4 h-4" />}
                        onClick={() => handleDownload(gallery.id)}
                        disabled={isDownloading}
                        fullWidth
                      >
                        {isDownloading && downloadProgress?.gallery_id === gallery.id
                          ? 'Downloading...'
                          : 'Download'}
                      </AppButton>
                    )}
                  </div>
                </AppCard>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default OfflineManager;
