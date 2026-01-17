/**
 * GalleryDetail Page
 *
 * Staff gallery management with:
 * - Gallery info editing
 * - Photo grid with batch selection
 * - Sub-gallery management
 * - Share link creation
 * - Preview mode
 * - Real-time WebSocket updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useHaptic, useBreakpoint } from '../hooks';
import {
  GalleryGrid,
  Lightbox,
  PinEntryModal,
  ShareModal,
} from '../components/gallery';
import { UploadModal } from '../components/upload/UploadModal';
import { AppButton } from '../components/ui/AppButton';
import { AppCard } from '../components/ui/AppCard';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import {
  getGallery,
  getGalleryPhotos,
  publishGallery,
  archiveGallery,
  updateGallery,
  verifyPhotoPin,
  createReconnectingWebSocket,
  batchUpdateVisibility,
} from '../services/gallery-api';
import type {
  GalleryResponse,
  GalleryAsset,
  WebSocketMessage,
} from '../types/gallery';

// Icons
function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
    </svg>
  );
}

function ShareIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z" />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
    </svg>
  );
}

function ImageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
    </svg>
  );
}

// Status badge component
const statusColors = {
  draft: 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300',
  published: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300',
  archived: 'bg-neutral-100 text-neutral-600 dark:bg-white/10 dark:text-neutral-400',
};

const statusLabels = {
  draft: 'Draft',
  published: 'Published',
  archived: 'Archived',
};

// Loading skeleton
function GallerySkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="h-8 w-48 bg-neutral-200 dark:bg-white/10 rounded-lg" />
      <div className="h-4 w-32 bg-neutral-200 dark:bg-white/10 rounded-lg" />
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="aspect-square rounded-xl bg-neutral-200 dark:bg-white/10" />
        ))}
      </div>
    </div>
  );
}

// Batch action bar
function BatchActionBar({
  selectedCount,
  onClear,
  onHide,
  onShow,
  onDelete,
  onSetCover,
  isSettingCover,
}: {
  selectedCount: number;
  onClear: () => void;
  onHide: () => void;
  onShow: () => void;
  onDelete: () => void;
  onSetCover?: () => void;
  isSettingCover?: boolean;
}) {
  if (selectedCount === 0) return null;

  return (
    <div
      className={cn(
        'fixed bottom-4 left-1/2 -translate-x-1/2 z-30',
        'flex items-center gap-3',
        'px-4 py-3 rounded-2xl',
        'bg-neutral-900/95 dark:bg-white/95 backdrop-blur-xl',
        'shadow-xl',
        'animate-slide-up'
      )}
    >
      <span className="text-sm font-medium text-white dark:text-neutral-900">
        {selectedCount} selected
      </span>
      <div className="h-4 w-px bg-white/20 dark:bg-neutral-900/20" />

      {/* Set as Cover - only show when exactly 1 photo selected */}
      {selectedCount === 1 && onSetCover && (
        <button
          onClick={onSetCover}
          disabled={isSettingCover}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg",
            "bg-primary-500 text-white hover:bg-primary-600 transition-colors",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          <ImageIcon className="w-4 h-4" />
          {isSettingCover ? 'Setting...' : 'Set as Cover'}
        </button>
      )}

      <button
        onClick={onShow}
        className="px-3 py-1.5 text-sm rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 transition-colors"
      >
        Show
      </button>
      <button
        onClick={onHide}
        className="px-3 py-1.5 text-sm rounded-lg bg-amber-500 text-white hover:bg-amber-600 transition-colors"
      >
        Hide
      </button>
      <button
        onClick={onDelete}
        className="px-3 py-1.5 text-sm rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors"
      >
        Delete
      </button>
      <button
        onClick={onClear}
        className="p-1.5 rounded-lg text-white/70 dark:text-neutral-900/70 hover:text-white dark:hover:text-neutral-900 transition-colors"
      >
        <CloseIcon className="w-4 h-4" />
      </button>
    </div>
  );
}

export function GalleryDetailPage() {
  const { galleryId } = useParams<{ galleryId: string }>();
  const navigate = useNavigate();
  const haptic = useHaptic();
  const { isMobile } = useBreakpoint();

  // Gallery state
  const [gallery, setGallery] = useState<GalleryResponse | null>(null);
  const [photos, setPhotos] = useState<GalleryAsset[]>([]);
  const [isLoadingGallery, setIsLoadingGallery] = useState(true);
  const [isLoadingPhotos, setIsLoadingPhotos] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [cursor, setCursor] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isSelectionMode, setIsSelectionMode] = useState(false);

  // Lightbox state
  const [lightboxAssetId, setLightboxAssetId] = useState<string | null>(null);

  // PIN state
  const [pinModalAsset, setPinModalAsset] = useState<GalleryAsset | null>(null);
  const [pinError, setPinError] = useState<string | null>(null);
  const [isPinLoading, setIsPinLoading] = useState(false);
  const [remainingAttempts, setRemainingAttempts] = useState<number | undefined>();
  const [lockedUntil, setLockedUntil] = useState<Date | null>(null);

  // Share modal state
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  // Upload modal state
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Action states
  const [isPublishing, setIsPublishing] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
  const [isSettingCover, setIsSettingCover] = useState(false);

  // Confirmation dialog state
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // WebSocket state
  const [wsConnected, setWsConnected] = useState(false);

  // Fetch gallery metadata
  useEffect(() => {
    if (!galleryId) return;

    const fetchGallery = async () => {
      try {
        setIsLoadingGallery(true);
        const data = await getGallery(galleryId);
        setGallery(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load gallery');
      } finally {
        setIsLoadingGallery(false);
      }
    };

    fetchGallery();
  }, [galleryId]);

  // Fetch photos
  const fetchPhotos = useCallback(
    async (reset = false) => {
      if (!galleryId) return;

      try {
        if (reset) {
          setIsLoadingPhotos(true);
          setCursor(undefined);
        }

        const data = await getGalleryPhotos(galleryId, {
          cursor: reset ? undefined : cursor,
          limit: 50,
          include_private: true,
        });

        setPhotos((prev) => (reset ? data.photos : [...prev, ...data.photos]));
        setCursor(data.cursor);
        setHasMore(data.has_more);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load photos');
      } finally {
        setIsLoadingPhotos(false);
      }
    },
    [galleryId, cursor]
  );

  // Track if we've done initial fetch for current gallery
  const lastGalleryIdRef = useRef<string | null>(null);

  // Initial photo fetch
  useEffect(() => {
    if (lastGalleryIdRef.current !== galleryId) {
      lastGalleryIdRef.current = galleryId ?? null;
      fetchPhotos(true);
    }
  }, [galleryId, fetchPhotos]);

  // WebSocket connection
  useEffect(() => {
    if (!galleryId) return;

    const { disconnect } = createReconnectingWebSocket(galleryId, {
      onOpen: () => setWsConnected(true),
      onMessage: (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          // Handle real-time updates
          if (message.type === 'favorite_added' || message.type === 'favorite_removed') {
            if (message.asset_id) {
              setPhotos((prev) =>
                prev.map((p) =>
                  p.gallery_asset_id === message.asset_id
                    ? {
                        ...p,
                        favorites_count:
                          message.type === 'favorite_added'
                            ? p.favorites_count + 1
                            : Math.max(0, p.favorites_count - 1),
                      }
                    : p
                )
              );
            }
          }
        } catch {
          // Ignore parse errors
        }
      },
      onClose: () => setWsConnected(false),
    });

    return () => disconnect();
  }, [galleryId]);

  // Handle photo click
  const handlePhotoClick = useCallback(
    (asset: GalleryAsset) => {
      if (isSelectionMode) {
        // Toggle selection
        setSelectedIds((prev) =>
          prev.includes(asset.gallery_asset_id)
            ? prev.filter((id) => id !== asset.gallery_asset_id)
            : [...prev, asset.gallery_asset_id]
        );
        haptic.light();
      } else if (asset.is_private) {
        setPinModalAsset(asset);
      } else {
        setLightboxAssetId(asset.gallery_asset_id);
      }
    },
    [isSelectionMode, haptic]
  );

  // Handle selection toggle
  const handleSelectionToggle = useCallback(
    (asset: GalleryAsset) => {
      setSelectedIds((prev) =>
        prev.includes(asset.gallery_asset_id)
          ? prev.filter((id) => id !== asset.gallery_asset_id)
          : [...prev, asset.gallery_asset_id]
      );
      haptic.light();
    },
    [haptic]
  );

  // Handle PIN verification
  const handlePinSubmit = useCallback(
    async (pin: string) => {
      if (!pinModalAsset) return;

      setIsPinLoading(true);
      setPinError(null);

      try {
        const result = await verifyPhotoPin({
          asset_id: pinModalAsset.gallery_asset_id,
          pin,
        });

        if (result.success) {
          setPhotos((prev) =>
            prev.map((p) =>
              p.gallery_asset_id === pinModalAsset.gallery_asset_id
                ? { ...p, is_private: false }
                : p
            )
          );
          setLightboxAssetId(pinModalAsset.gallery_asset_id);
          setPinModalAsset(null);
        } else {
          setPinError('Incorrect PIN');
          setRemainingAttempts(result.remaining_attempts);
          if (result.locked_until) {
            setLockedUntil(new Date(result.locked_until));
          }
        }
      } catch (err) {
        setPinError(err instanceof Error ? err.message : 'Failed to verify PIN');
      } finally {
        setIsPinLoading(false);
      }
    },
    [pinModalAsset]
  );

  // Handle lightbox navigation
  const handleLightboxNavigate = useCallback((assetId: string) => {
    setLightboxAssetId(assetId);
  }, []);

  // Handle publish
  const handlePublish = useCallback(async () => {
    if (!galleryId || !gallery) return;

    setIsPublishing(true);
    try {
      const updated = await publishGallery(galleryId);
      setGallery({ ...gallery, ...updated });
      haptic.success();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish');
      haptic.error();
    } finally {
      setIsPublishing(false);
    }
  }, [galleryId, gallery, haptic]);

  // Handle archive
  const handleArchive = useCallback(async () => {
    if (!galleryId || !gallery) return;

    setIsArchiving(true);
    try {
      const updated = await archiveGallery(galleryId);
      setGallery({ ...gallery, ...updated });
      haptic.success();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to archive');
      haptic.error();
    } finally {
      setIsArchiving(false);
    }
  }, [galleryId, gallery, haptic]);

  // Handle set as cover
  const handleSetAsCover = useCallback(async () => {
    if (!galleryId || !gallery || selectedIds.length !== 1) return;

    const assetId = selectedIds[0];
    setIsSettingCover(true);

    try {
      const updated = await updateGallery(galleryId, { cover_asset_id: assetId });
      setGallery({ ...gallery, ...updated });
      setSelectedIds([]);
      setIsSelectionMode(false);
      haptic.success();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set cover');
      haptic.error();
    } finally {
      setIsSettingCover(false);
    }
  }, [galleryId, gallery, selectedIds, haptic]);

  // Batch actions
  const handleBatchHide = useCallback(async () => {
    if (!galleryId || selectedIds.length === 0) return;

    try {
      await batchUpdateVisibility(galleryId, { asset_ids: selectedIds, visible: false });
      setPhotos((prev) =>
        prev.map((p) =>
          selectedIds.includes(p.gallery_asset_id) ? { ...p, visible: false } : p
        )
      );
      setSelectedIds([]);
      haptic.success();
    } catch {
      haptic.error();
    }
  }, [galleryId, selectedIds, haptic]);

  const handleBatchShow = useCallback(async () => {
    if (!galleryId || selectedIds.length === 0) return;

    try {
      await batchUpdateVisibility(galleryId, { asset_ids: selectedIds, visible: true });
      setPhotos((prev) =>
        prev.map((p) =>
          selectedIds.includes(p.gallery_asset_id) ? { ...p, visible: true } : p
        )
      );
      setSelectedIds([]);
      haptic.success();
    } catch {
      haptic.error();
    }
  }, [galleryId, selectedIds, haptic]);

  // Open delete confirmation dialog
  const handleBatchDeleteClick = useCallback(() => {
    if (selectedIds.length === 0) return;
    setDeleteConfirmOpen(true);
  }, [selectedIds.length]);

  // Confirm and execute batch delete
  const handleBatchDeleteConfirm = useCallback(async () => {
    if (!galleryId || selectedIds.length === 0) return;

    setIsDeleting(true);
    try {
      // TODO: Implement actual batch delete API call
      // await batchDeleteAssets(galleryId, { asset_ids: selectedIds });

      // For now, remove from local state (simulate deletion)
      setPhotos((prev) =>
        prev.filter((p) => !selectedIds.includes(p.gallery_asset_id))
      );
      setSelectedIds([]);
      setIsSelectionMode(false);
      setDeleteConfirmOpen(false);
      haptic.success();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete photos');
      haptic.error();
    } finally {
      setIsDeleting(false);
    }
  }, [galleryId, selectedIds, haptic]);

  // Preview mode
  const handlePreview = useCallback(() => {
    if (galleryId) {
      window.open(`/g/${galleryId}`, '_blank');
    }
  }, [galleryId]);

  // Error state
  if (error && !gallery) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-neutral-50 dark:bg-neutral-900">
        <AppCard variant="glass" padding="lg" className="max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center">
            <span className="text-3xl">⚠️</span>
          </div>
          <h2 className="text-xl font-semibold text-neutral-800 dark:text-white mb-2">
            Gallery Not Found
          </h2>
          <p className="text-neutral-600 dark:text-neutral-300 mb-4">{error}</p>
          <AppButton variant="outline" onClick={() => navigate('/galleries')}>
            Back to Galleries
          </AppButton>
        </AppCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Header */}
      <header
        className={cn(
          'sticky top-0 z-20',
          'bg-white/80 dark:bg-neutral-900/80',
          'backdrop-blur-xl',
          'border-b border-neutral-200 dark:border-white/10',
          'px-4 py-4 sm:px-6'
        )}
      >
        <div className="max-w-7xl mx-auto">
          {isLoadingGallery ? (
            <div className="animate-pulse">
              <div className="h-6 w-32 bg-neutral-200 dark:bg-white/10 rounded-lg mb-2" />
              <div className="h-4 w-20 bg-neutral-200 dark:bg-white/10 rounded-lg" />
            </div>
          ) : gallery ? (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => navigate('/galleries')}
                  className={cn(
                    'p-2 rounded-full',
                    'text-neutral-600 hover:text-neutral-900',
                    'dark:text-neutral-400 dark:hover:text-white',
                    'hover:bg-neutral-100 dark:hover:bg-white/10',
                    'transition-colors'
                  )}
                  aria-label="Back to galleries"
                >
                  <ArrowLeftIcon className="w-5 h-5" />
                </button>
                <div>
                  <h1 className="text-xl sm:text-2xl font-bold text-neutral-800 dark:text-white">
                    {gallery.title}
                  </h1>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium', statusColors[gallery.status])}>
                      {statusLabels[gallery.status]}
                    </span>
                    <span className="text-sm text-neutral-500 dark:text-neutral-400">
                      {gallery.photo_count} photos
                    </span>
                    {wsConnected && (
                      <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        Live
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <AppButton
                  variant="ghost"
                  size="sm"
                  leftIcon={<EyeIcon className="w-4 h-4" />}
                  onClick={handlePreview}
                >
                  {isMobile ? '' : 'Preview'}
                </AppButton>

                <AppButton
                   variant="ghost"
                   size="sm"
                   leftIcon={<UploadIcon className="w-4 h-4" />}
                   onClick={() => setIsUploadModalOpen(true)}
                >
                   {isMobile ? '' : 'Upload'}
                </AppButton>

                <AppButton
                  variant="ghost"
                  size="sm"
                  leftIcon={<ShareIcon className="w-4 h-4" />}
                  onClick={() => setIsShareModalOpen(true)}
                >
                  {isMobile ? '' : 'Share'}
                </AppButton>

                <AppButton
                  variant="ghost"
                  size="sm"
                  leftIcon={<CheckIcon className="w-4 h-4" />}
                  onClick={() => {
                    setIsSelectionMode(!isSelectionMode);
                    if (isSelectionMode) setSelectedIds([]);
                    haptic.light();
                  }}
                  className={isSelectionMode ? 'bg-primary-100 dark:bg-primary-500/20' : ''}
                >
                  {isMobile ? '' : 'Select'}
                </AppButton>

                {gallery.status === 'draft' && (
                  <AppButton
                    variant="primary"
                    size="sm"
                    isLoading={isPublishing}
                    onClick={handlePublish}
                    glowOnHover
                  >
                    Publish
                  </AppButton>
                )}

                {gallery.status === 'published' && (
                  <AppButton
                    variant="outline"
                    size="sm"
                    isLoading={isArchiving}
                    onClick={handleArchive}
                  >
                    Archive
                  </AppButton>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </header>

      {/* Error toast for non-fatal errors */}
      {error && gallery && (
        <div
          className={cn(
            'fixed top-20 left-1/2 -translate-x-1/2 z-30',
            'max-w-md w-full mx-4',
            'animate-slide-down'
          )}
        >
          <div
            className={cn(
              'flex items-center gap-3',
              'px-4 py-3 rounded-xl',
              'bg-red-500/95 dark:bg-red-600/95 backdrop-blur-xl',
              'shadow-lg'
            )}
          >
            <svg className="w-5 h-5 text-white flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
            <p className="text-sm text-white flex-1">{error}</p>
            <button
              onClick={() => setError(null)}
              className="p-1 rounded-full text-white/80 hover:text-white hover:bg-white/20 transition-colors"
              aria-label="Dismiss error"
            >
              <CloseIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        {isLoadingGallery ? (
          <GallerySkeleton />
        ) : (
          <GalleryGrid
            assets={photos}
            isLoading={isLoadingPhotos}
            hasMore={hasMore}
            onLoadMore={() => fetchPhotos(false)}
            onPhotoClick={handlePhotoClick}
            onSelectionToggle={handleSelectionToggle}
            selectable={isSelectionMode}
            selectedIds={selectedIds}
            thumbnailProps={{
              showFavoriteCount: true,
              showSelectionCount: true,
            }}
          />
        )}
      </main>

      {/* Batch action bar */}
      <BatchActionBar
        selectedCount={selectedIds.length}
        onClear={() => setSelectedIds([])}
        onHide={handleBatchHide}
        onShow={handleBatchShow}
        onDelete={handleBatchDeleteClick}
        onSetCover={handleSetAsCover}
        isSettingCover={isSettingCover}
      />

      {/* Lightbox */}
      <Lightbox
        assets={photos}
        currentAssetId={lightboxAssetId || ''}
        isOpen={!!lightboxAssetId}
        onClose={() => setLightboxAssetId(null)}
        onNavigate={handleLightboxNavigate}
      />

      {/* PIN Modal */}
      <PinEntryModal
        isOpen={!!pinModalAsset}
        onClose={() => {
          setPinModalAsset(null);
          setPinError(null);
        }}
        onSubmit={handlePinSubmit}
        isLoading={isPinLoading}
        error={pinError}
        remainingAttempts={remainingAttempts}
        lockedUntil={lockedUntil}
        photoTitle={pinModalAsset?.title}
      />

      {/* Share modal */}
      {gallery && (
        <ShareModal
          isOpen={isShareModalOpen}
          onClose={() => setIsShareModalOpen(false)}
          galleryId={galleryId || ''}
          galleryTitle={gallery.title}
        />
      )}

      {/* Upload Modal */}
      {gallery && (
        <UploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          galleryId={galleryId || ''}
          workspaceId={gallery.workspace_id}
          onUploadComplete={() => fetchPhotos(true)}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        onConfirm={handleBatchDeleteConfirm}
        title="Delete Photos"
        message={`Are you sure you want to delete ${selectedIds.length} photo${selectedIds.length !== 1 ? 's' : ''}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}

export default GalleryDetailPage;
