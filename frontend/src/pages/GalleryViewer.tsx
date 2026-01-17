/**
 * GalleryViewer Page
 *
 * Public gallery viewing experience with:
 * - Sub-gallery navigation (tabs or continuous scroll)
 * - LQIP progressive loading
 * - Lightbox for full photo viewing
 * - Real-time favorites/selections via WebSocket
 * - PIN protection for private photos
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../lib/utils';
import { useHaptic } from '../hooks';
import {
  GalleryGrid,
  Lightbox,
  PinEntryModal,
} from '../components/gallery';
import { AppCard } from '../components/ui/AppCard';
import { AppButton } from '../components/ui/AppButton';
import {
  getPublicGalleryMetadata,
  getPublicGalleryPhotos,
  verifyPhotoPin,
  addToFavorites,
  removeFromFavorites,
  addToSelections,
  removeFromSelections,
  createReconnectingWebSocket,
} from '../services/gallery-api';
import type {
  GalleryResponse,
  GalleryAsset,
  SubGallery,
  WebSocketMessage,
} from '../types/gallery';

/**
 * Camera icon for empty state
 */
function CameraIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 15.2c1.94 0 3.5-1.56 3.5-3.5S13.94 8.2 12 8.2s-3.5 1.56-3.5 3.5 1.56 3.5 3.5 3.5zM9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z" />
    </svg>
  );
}

/**
 * Heart icon for favorites
 */
function HeartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  );
}

/**
 * Check circle icon for selections
 */
function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
    </svg>
  );
}

/**
 * X icon for closing
 */
function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

/**
 * Share icon
 */
function ShareIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z" />
    </svg>
  );
}

/**
 * Loading skeleton for gallery header
 */
function HeaderSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 w-48 bg-neutral-200 dark:bg-white/10 rounded-lg mb-2" />
      <div className="h-4 w-32 bg-neutral-200 dark:bg-white/10 rounded-lg" />
    </div>
  );
}

/**
 * Sub-gallery tab navigation
 */
function SubGalleryTabs({
  subGalleries,
  activeId,
  onSelect,
}: {
  subGalleries: SubGallery[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
}) {
  return (
    <div className="flex overflow-x-auto gap-2 pb-2 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
      {/* All Photos tab */}
      <button
        onClick={() => onSelect(null)}
        className={cn(
          'flex-shrink-0 px-4 py-2 rounded-full',
          'text-sm font-medium',
          'transition-all duration-200',
          activeId === null
            ? 'bg-primary-500 text-white'
            : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:bg-white/10 dark:text-neutral-300 dark:hover:bg-white/15'
        )}
      >
        All Photos
      </button>

      {subGalleries
        .filter((sg) => sg.visible)
        .map((sg) => (
          <button
            key={sg.sub_gallery_id}
            onClick={() => onSelect(sg.sub_gallery_id)}
            className={cn(
              'flex-shrink-0 px-4 py-2 rounded-full',
              'text-sm font-medium',
              'transition-all duration-200',
              activeId === sg.sub_gallery_id
                ? 'bg-primary-500 text-white'
                : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:bg-white/10 dark:text-neutral-300 dark:hover:bg-white/15'
            )}
          >
            {sg.name}
            <span className="ml-1.5 opacity-60">({sg.photo_count})</span>
          </button>
        ))}
    </div>
  );
}

/**
 * Gallery stats bar with favorites and selections
 */
function GalleryStats({
  gallery,
  favoritesCount,
  selectionsCount,
}: {
  gallery: GalleryResponse;
  favoritesCount: number;
  selectionsCount: number;
}) {
  return (
    <div className="flex items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400">
      <span className="flex items-center gap-1">
        <CameraIcon className="w-4 h-4" />
        {gallery.photo_count} photos
      </span>
      {favoritesCount > 0 && (
        <span className="flex items-center gap-1.5 text-rose-500">
          <HeartIcon className="w-4 h-4" />
          {favoritesCount}
        </span>
      )}
      {selectionsCount > 0 && (
        <span className="flex items-center gap-1.5 text-emerald-500">
          <CheckCircleIcon className="w-4 h-4" />
          {selectionsCount}
        </span>
      )}
    </div>
  );
}

/**
 * Check icon for copied state
 */
function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

/**
 * Selection bar at bottom of screen when photos are selected
 */
function SelectionBar({
  count,
  onClear,
  onShare,
  isCopied,
}: {
  count: number;
  onClear: () => void;
  onShare: () => void;
  isCopied: boolean;
}) {
  const haptic = useHaptic();

  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={cn(
        'fixed bottom-0 inset-x-0 z-30',
        'bg-white/95 dark:bg-neutral-900/95',
        'backdrop-blur-xl',
        'border-t border-neutral-200 dark:border-white/10',
        'shadow-[0_-4px_20px_rgba(0,0,0,0.1)]',
        'px-4 py-3 sm:px-6'
      )}
      style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 12px)' }}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Selection count */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              haptic.light();
              onClear();
            }}
            className={cn(
              'p-2 rounded-full',
              'text-neutral-500 hover:text-neutral-700 dark:hover:text-white',
              'hover:bg-neutral-100 dark:hover:bg-white/10',
              'transition-colors'
            )}
            aria-label="Clear selection"
          >
            <XIcon className="w-5 h-5" />
          </button>
          <span className="font-medium text-neutral-800 dark:text-white">
            {count} selected
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <AppButton
            variant={isCopied ? 'ghost' : 'outline'}
            size="sm"
            onClick={() => {
              haptic.medium();
              onShare();
            }}
            className={cn(
              'gap-2 transition-all',
              isCopied && 'bg-emerald-500/20 border-emerald-500/50 text-emerald-600 dark:text-emerald-400'
            )}
          >
            {isCopied ? (
              <>
                <CheckIcon className="w-4 h-4" />
                <span className="hidden sm:inline">Copied!</span>
                <span className="sm:hidden">Copied</span>
              </>
            ) : (
              <>
                <ShareIcon className="w-4 h-4" />
                <span className="hidden sm:inline">Share Selection</span>
                <span className="sm:hidden">Share</span>
              </>
            )}
          </AppButton>
        </div>
      </div>
    </motion.div>
  );
}

export function GalleryViewerPage() {
  const { galleryId } = useParams<{ galleryId: string }>();
  // searchParams reserved for future filter functionality
  // const [searchParams] = useSearchParams();

  // State
  const [gallery, setGallery] = useState<GalleryResponse | null>(null);
  const [photos, setPhotos] = useState<GalleryAsset[]>([]);
  const [isLoadingGallery, setIsLoadingGallery] = useState(true);
  const [isLoadingPhotos, setIsLoadingPhotos] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [cursor, setCursor] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);

  // Navigation state
  const [activeSubGalleryId, setActiveSubGalleryId] = useState<string | null>(null);

  // Lightbox state
  const [lightboxAssetId, setLightboxAssetId] = useState<string | null>(null);

  // Favorites state (tracked locally for optimistic UI)
  const [favoritedIds, setFavoritedIds] = useState<Set<string>>(new Set());

  // Selections state (photos client wants to order/share)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // PIN entry state
  const [pinModalAsset, setPinModalAsset] = useState<GalleryAsset | null>(null);
  const [pinError, setPinError] = useState<string | null>(null);
  const [isPinLoading, setIsPinLoading] = useState(false);
  const [remainingAttempts, setRemainingAttempts] = useState<number | undefined>();
  const [lockedUntil, setLockedUntil] = useState<Date | null>(null);

  // WebSocket state
  const [wsConnected, setWsConnected] = useState(false);

  // Share feedback state
  const [selectionsCopied, setSelectionsCopied] = useState(false);

  // Haptic feedback
  const haptic = useHaptic();

  // Fetch gallery metadata
  useEffect(() => {
    if (!galleryId) return;

    const fetchGallery = async () => {
      try {
        setIsLoadingGallery(true);
        const data = await getPublicGalleryMetadata(galleryId);
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
  const fetchPhotos = useCallback(async (reset = false) => {
    if (!galleryId) return;

    try {
      if (reset) {
        setIsLoadingPhotos(true);
        setCursor(undefined);
      }

      const data = await getPublicGalleryPhotos(galleryId, {
        cursor: reset ? undefined : cursor,
        limit: 50,
        sub_gallery_id: activeSubGalleryId || undefined,
      });

      setPhotos((prev) => (reset ? data.photos : [...prev, ...data.photos]));
      setCursor(data.cursor);
      setHasMore(data.has_more);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load photos');
    } finally {
      setIsLoadingPhotos(false);
    }
  }, [galleryId, cursor, activeSubGalleryId]);

  // Track if we've done initial fetch for current gallery/sub-gallery combination
  const lastFetchKeyRef = useRef<string | null>(null);

  // Initial photo fetch and sub-gallery change
  useEffect(() => {
    const fetchKey = `${galleryId}-${activeSubGalleryId}`;
    if (lastFetchKeyRef.current !== fetchKey) {
      lastFetchKeyRef.current = fetchKey;
      fetchPhotos(true);
    }
  }, [galleryId, activeSubGalleryId, fetchPhotos]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!galleryId) return;

    const { disconnect } = createReconnectingWebSocket(galleryId, {
      onOpen: () => setWsConnected(true),
      onMessage: (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'favorite_added':
            case 'favorite_removed':
              // Update photo favorite count
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
              break;

            case 'selection_added':
              // Update photo selection count from other viewers
              if (message.asset_id) {
                setPhotos((prev) =>
                  prev.map((p) =>
                    p.gallery_asset_id === message.asset_id
                      ? { ...p, selections_count: (p.selections_count || 0) + 1 }
                      : p
                  )
                );
              }
              break;

            case 'selection_removed':
              if (message.asset_id) {
                setPhotos((prev) =>
                  prev.map((p) =>
                    p.gallery_asset_id === message.asset_id
                      ? { ...p, selections_count: Math.max(0, (p.selections_count || 0) - 1) }
                      : p
                  )
                );
              }
              break;
          }
        } catch {
          // Ignore parse errors
        }
      },
      onClose: () => setWsConnected(false),
    });

    return () => disconnect();
  }, [galleryId]);

  // Handle photo click -> open lightbox
  const handlePhotoClick = useCallback((asset: GalleryAsset) => {
    if (asset.is_private) {
      // Need to unlock first
      setPinModalAsset(asset);
    } else {
      setLightboxAssetId(asset.gallery_asset_id);
    }
  }, []);

  // Handle favorite toggle
  const handleFavoriteToggle = useCallback(
    async (asset: GalleryAsset) => {
      if (!galleryId) return;

      const isFavorited = favoritedIds.has(asset.gallery_asset_id);

      // Optimistic update
      setFavoritedIds((prev) => {
        const next = new Set(prev);
        if (isFavorited) {
          next.delete(asset.gallery_asset_id);
        } else {
          next.add(asset.gallery_asset_id);
        }
        return next;
      });

      try {
        if (isFavorited) {
          await removeFromFavorites(galleryId, asset.gallery_asset_id);
        } else {
          await addToFavorites(galleryId, asset.gallery_asset_id);
        }
      } catch {
        // Revert on error
        setFavoritedIds((prev) => {
          const next = new Set(prev);
          if (isFavorited) {
            next.add(asset.gallery_asset_id);
          } else {
            next.delete(asset.gallery_asset_id);
          }
          return next;
        });
      }
    },
    [galleryId, favoritedIds]
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
          // Update the photo to show as unlocked
          setPhotos((prev) =>
            prev.map((p) =>
              p.gallery_asset_id === pinModalAsset.gallery_asset_id
                ? { ...p, is_private: false }
                : p
            )
          );

          // Open lightbox
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

  // Handle selection toggle
  const handleSelectionToggle = useCallback(
    async (asset: GalleryAsset) => {
      if (!galleryId) return;

      const isSelected = selectedIds.has(asset.gallery_asset_id);
      const haptic = {
        light: () => navigator.vibrate?.(10),
        medium: () => navigator.vibrate?.(20),
      };

      // Optimistic update with haptic feedback
      setSelectedIds((prev) => {
        const next = new Set(prev);
        if (isSelected) {
          next.delete(asset.gallery_asset_id);
          haptic.light();
        } else {
          next.add(asset.gallery_asset_id);
          haptic.medium();
        }
        return next;
      });

      try {
        if (isSelected) {
          await removeFromSelections(galleryId, asset.gallery_asset_id);
        } else {
          await addToSelections(galleryId, asset.gallery_asset_id);
        }
      } catch {
        // Revert on error
        setSelectedIds((prev) => {
          const next = new Set(prev);
          if (isSelected) {
            next.add(asset.gallery_asset_id);
          } else {
            next.delete(asset.gallery_asset_id);
          }
          return next;
        });
      }
    },
    [galleryId, selectedIds]
  );

  // Clear all selections
  const handleClearSelections = useCallback(() => {
    setSelectedIds(new Set());
    // Note: Could also call API to clear server-side selections
  }, []);

  // Share selected photos - copies selection summary for client to share with photographer
  const handleShareSelections = useCallback(async () => {
    if (selectedIds.size === 0) return;

    const selectedPhotos = photos.filter((p) =>
      selectedIds.has(p.gallery_asset_id)
    );

    // Build shareable text with selection summary
    const selectionText = [
      `My Selections from "${gallery?.title || 'Gallery'}"`,
      `${selectedPhotos.length} photo${selectedPhotos.length !== 1 ? 's' : ''} selected`,
      '',
      'Selected photos:',
      ...selectedPhotos.map((p, i) => `${i + 1}. ${p.title || `Photo ${p.gallery_asset_id.slice(0, 8)}`}`),
    ].join('\n');

    try {
      await navigator.clipboard.writeText(selectionText);
      setSelectionsCopied(true);
      haptic.success();
      setTimeout(() => setSelectionsCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = selectionText;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        setSelectionsCopied(true);
        haptic.success();
        setTimeout(() => setSelectionsCopied(false), 2000);
      } catch {
        haptic.error();
      }
      document.body.removeChild(textArea);
    }
  }, [photos, selectedIds, gallery?.title, haptic]);

  // Sub-gallery list (visible only)
  const visibleSubGalleries = useMemo(
    () => gallery?.sub_galleries?.filter((sg) => sg.visible) || [],
    [gallery?.sub_galleries]
  );

  // Error state
  if (error && !gallery) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <AppCard variant="glass" padding="lg" className="max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center">
            <span className="text-3xl">⚠️</span>
          </div>
          <h2 className="text-xl font-semibold text-neutral-800 dark:text-white mb-2">
            Gallery Not Available
          </h2>
          <p className="text-neutral-600 dark:text-neutral-300">{error}</p>
        </AppCard>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'min-h-screen',
        'bg-neutral-50 dark:bg-neutral-900'
      )}
    >
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
            <HeaderSkeleton />
          ) : gallery ? (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-neutral-800 dark:text-white">
                  {gallery.title}
                </h1>
                {gallery.client_name && (
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                    {gallery.client_name}
                  </p>
                )}
              </div>
              <GalleryStats
                gallery={gallery}
                favoritesCount={favoritedIds.size}
                selectionsCount={selectedIds.size}
              />
            </div>
          ) : null}

          {/* Sub-gallery tabs */}
          {visibleSubGalleries.length > 0 && gallery?.layout_style === 'tab' && (
            <div className="mt-4">
              <SubGalleryTabs
                subGalleries={visibleSubGalleries}
                activeId={activeSubGalleryId}
                onSelect={setActiveSubGalleryId}
              />
            </div>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        {/* Connection indicator */}
        {wsConnected && (
          <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 mb-4">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Live updates enabled
          </div>
        )}

        {/* Photo grid */}
        <GalleryGrid
          assets={photos}
          isLoading={isLoadingPhotos}
          hasMore={hasMore}
          onLoadMore={() => fetchPhotos(false)}
          onPhotoClick={handlePhotoClick}
          onFavoriteToggle={handleFavoriteToggle}
          onSelectionToggle={handleSelectionToggle}
          onUnlockClick={(asset) => setPinModalAsset(asset)}
          favoritedIds={Array.from(favoritedIds)}
          selectedIds={Array.from(selectedIds)}
          selectable={selectedIds.size > 0}
          thumbnailProps={{
            showFavoriteCount: true,
            showSelectionCount: true,
          }}
        />
      </main>

      {/* Lightbox */}
      <Lightbox
        assets={photos}
        currentAssetId={lightboxAssetId || ''}
        isOpen={!!lightboxAssetId}
        onClose={() => setLightboxAssetId(null)}
        onNavigate={handleLightboxNavigate}
        onFavoriteToggle={handleFavoriteToggle}
        isFavorited={lightboxAssetId ? favoritedIds.has(lightboxAssetId) : false}
      />

      {/* PIN Entry Modal */}
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

      {/* Selection bar (animated) */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <SelectionBar
            count={selectedIds.size}
            onClear={handleClearSelections}
            onShare={handleShareSelections}
            isCopied={selectionsCopied}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default GalleryViewerPage;
