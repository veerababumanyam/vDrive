/**
 * Lightbox Component
 *
 * Full-screen photo viewer with smooth navigation, keyboard controls,
 * and touch gestures. Prefetches adjacent photos for instant navigation.
 *
 * Features:
 * - Full-screen immersive view
 * - Keyboard navigation (arrows, escape)
 * - Touch swipe gestures
 * - Prefetch N-1 and N+1 for instant navigation
 * - Zoom and pan support
 * - Photo info panel
 * - Favorite/Selection actions
 */

import {
  forwardRef,
  useState,
  useEffect,
  useCallback,
  useRef,
  type HTMLAttributes,
} from 'react';
import { cn } from '../../lib/utils';
import { useHaptic } from '../../hooks';
import type { GalleryAsset } from '../../types/gallery';

export interface LightboxProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onSelect'> {
  /** Array of all assets (for navigation) */
  assets: GalleryAsset[];
  /** Currently selected asset ID */
  currentAssetId: string;
  /** Is lightbox open */
  isOpen: boolean;
  /** Close handler */
  onClose: () => void;
  /** Navigate to asset */
  onNavigate?: (assetId: string) => void;
  /** Favorite toggle handler */
  onFavoriteToggle?: (asset: GalleryAsset) => void;
  /** Selection toggle handler */
  onSelect?: (asset: GalleryAsset) => void;
  /** Download handler */
  onDownload?: (asset: GalleryAsset) => void;
  /** Is current asset favorited */
  isFavorited?: boolean;
  /** Is current asset selected */
  isSelected?: boolean;
  /** Show info panel */
  showInfo?: boolean;
}

/**
 * Close icon
 */
function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

/**
 * Arrow left icon
 */
function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
    </svg>
  );
}

/**
 * Arrow right icon
 */
function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
    </svg>
  );
}

/**
 * Heart icon
 */
function HeartIcon({
  filled,
  className,
}: {
  filled?: boolean;
  className?: string;
}) {
  if (filled) {
    return (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
      </svg>
    );
  }
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  );
}

/**
 * Check icon
 */
function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

/**
 * Download icon
 */
function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M5 20h14v-2H5v2zM19 9h-4V3H9v6H5l7 7 7-7z" />
    </svg>
  );
}

/**
 * Info icon
 */
function InfoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
    </svg>
  );
}

/**
 * Format file size
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export const Lightbox = forwardRef<HTMLDivElement, LightboxProps>(
  (
    {
      assets = [],
      currentAssetId,
      isOpen,
      onClose,
      onNavigate,
      onFavoriteToggle,
      onSelect,
      onDownload,
      isFavorited = false,
      isSelected = false,
      showInfo = false,
      className,
      ...props
    },
    ref
  ) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const [showInfoPanel, setShowInfoPanel] = useState(showInfo);
    const [touchStart, setTouchStart] = useState<{ x: number; y: number } | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const [initialPinchDistance, setInitialPinchDistance] = useState<number | null>(null);
    const haptic = useHaptic();
    const imageRef = useRef<HTMLImageElement>(null);

    // Find current index with null safety
    const currentIndex = assets.findIndex(
      (a) => a.gallery_asset_id === currentAssetId
    );
    const currentAsset = currentIndex >= 0 ? assets[currentIndex] : null;
    const hasPrev = currentIndex > 0;
    const hasNext = currentIndex >= 0 && currentIndex < assets.length - 1;

    // Navigation handlers
    const goToPrev = useCallback(() => {
      if (hasPrev) {
        setIsLoaded(false);
        onNavigate?.(assets[currentIndex - 1].gallery_asset_id);
        haptic.light();
      }
    }, [hasPrev, currentIndex, assets, onNavigate, haptic]);

    const goToNext = useCallback(() => {
      if (hasNext) {
        setIsLoaded(false);
        onNavigate?.(assets[currentIndex + 1].gallery_asset_id);
        haptic.light();
      }
    }, [hasNext, currentIndex, assets, onNavigate, haptic]);

    // Keyboard navigation
    useEffect(() => {
      if (!isOpen) return;

      const handleKeyDown = (e: KeyboardEvent) => {
        switch (e.key) {
          case 'ArrowLeft':
            e.preventDefault();
            goToPrev();
            break;
          case 'ArrowRight':
            e.preventDefault();
            goToNext();
            break;
          case 'Escape':
            e.preventDefault();
            onClose();
            break;
        }
      };

      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, goToPrev, goToNext, onClose]);

    // Calculate distance between two touch points (for pinch)
    const getTouchDistance = (touches: React.TouchList) => {
      if (touches.length < 2) return 0;
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;
      return Math.sqrt(dx * dx + dy * dy);
    };

    // Touch gesture handlers
    const handleTouchStart = (e: React.TouchEvent) => {
      if (e.touches.length === 2) {
        // Pinch start
        setInitialPinchDistance(getTouchDistance(e.touches));
      } else if (e.touches.length === 1) {
        // Single touch start
        setTouchStart({ x: e.touches[0].clientX, y: e.touches[0].clientY });
        setIsDragging(true);
      }
    };

    const handleTouchMove = (e: React.TouchEvent) => {
      if (e.touches.length === 2 && initialPinchDistance) {
        // Pinch zoom - don't allow below 1x (standard zoom range)
        const currentDistance = getTouchDistance(e.touches);
        const scale = currentDistance / initialPinchDistance;
        setZoom(Math.min(Math.max(scale, 1), 3)); // Clamp between 1x and 3x
      } else if (e.touches.length === 1 && isDragging && touchStart && zoom === 1) {
        // Drag for swipe-down-to-close or navigation
        const currentY = e.touches[0].clientY;
        const diffY = currentY - touchStart.y;
        setDragOffset({ x: 0, y: diffY });
      }
    };

    const handleTouchEnd = (e: React.TouchEvent) => {
      if (initialPinchDistance) {
        // Reset pinch
        setInitialPinchDistance(null);
        // Snap back to 1x if close to 1x, or cap at 3x if over-zoomed
        if (zoom < 1.1) {
          setZoom(1);
        } else if (zoom > 2.8) {
          setZoom(3);
        }
      }

      if (touchStart && isDragging) {
        const touchEnd = e.changedTouches[0];
        const diffX = touchStart.x - touchEnd.clientX;
        const diffY = touchEnd.clientY - touchStart.y;
        // Increased thresholds to prevent accidental navigation
        const horizontalThreshold = 100; // was 50
        const verticalThreshold = 150;   // was 100

        // Swipe down to close (only when not zoomed)
        if (zoom === 1 && diffY > verticalThreshold && Math.abs(diffX) < horizontalThreshold) {
          haptic.light();
          onClose();
        }
        // Horizontal swipe for navigation (only when not zoomed)
        else if (zoom === 1 && Math.abs(diffX) > horizontalThreshold) {
          if (diffX > 0) {
            goToNext();
          } else {
            goToPrev();
          }
        }
      }

      // Reset state
      setTouchStart(null);
      setIsDragging(false);
      setDragOffset({ x: 0, y: 0 });
    };

    // Double-tap to zoom
    const lastTapRef = useRef<number>(0);
    const handleDoubleTap = useCallback((e: React.TouchEvent) => {
      const now = Date.now();
      const DOUBLE_TAP_DELAY = 300;

      if (now - lastTapRef.current < DOUBLE_TAP_DELAY) {
        // Double tap detected
        e.preventDefault();
        if (zoom === 1) {
          setZoom(2);
          haptic.medium();
        } else {
          setZoom(1);
          haptic.light();
        }
      }
      lastTapRef.current = now;
    }, [zoom, haptic]);

    // Reset zoom when navigating
    useEffect(() => {
      setZoom(1);
      setDragOffset({ x: 0, y: 0 });
    }, [currentAssetId]);

    // Prefetch adjacent images
    useEffect(() => {
      if (!isOpen || !currentAsset) return;

      const prefetchUrls: string[] = [];

      // Prefetch N-1
      if (hasPrev && assets[currentIndex - 1].preview_url) {
        prefetchUrls.push(assets[currentIndex - 1].preview_url!);
      }

      // Prefetch N+1
      if (hasNext && assets[currentIndex + 1].preview_url) {
        prefetchUrls.push(assets[currentIndex + 1].preview_url!);
      }

      prefetchUrls.forEach((url) => {
        const img = new Image();
        img.src = url;
      });
    }, [isOpen, currentAsset, hasPrev, hasNext, currentIndex, assets]);

    // Prevent body scroll when open
    useEffect(() => {
      if (isOpen) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
      return () => {
        document.body.style.overflow = '';
      };
    }, [isOpen]);

    if (!isOpen || !currentAsset) return null;

    return (
      <div
        ref={ref}
        className={cn(
          'fixed inset-0 z-50',
          'overlay-frosted bg-black/90',
          'flex flex-col',
          'animate-fade-in',
          'touch-none', // Prevent default touch behaviors
          className
        )}
        style={{
          // Swipe-down-to-close visual feedback
          opacity: dragOffset.y > 0 ? 1 - Math.min(dragOffset.y / 300, 0.5) : 1,
        }}
        onTouchStart={(e) => {
          handleTouchStart(e);
          handleDoubleTap(e);
        }}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        {...props}
      >
        {/* Header - with safe area support for notched devices */}
        <header
          className={cn(
            'absolute top-0 left-0 right-0 z-10',
            'flex items-center justify-between',
            'px-4 pb-3 sm:px-6 sm:pb-4',
            'bg-gradient-to-b from-black/80 to-transparent'
          )}
          style={{
            paddingTop: 'max(env(safe-area-inset-top, 12px), 12px)',
            paddingLeft: 'max(env(safe-area-inset-left, 16px), 16px)',
            paddingRight: 'max(env(safe-area-inset-right, 16px), 16px)',
          }}
        >
          {/* Counter */}
          <span className="text-sm text-white/80 font-medium">
            {currentIndex + 1} / {assets.length}
          </span>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* Info toggle */}
            <button
              onClick={() => setShowInfoPanel(!showInfoPanel)}
              className={cn(
                'p-2 rounded-full',
                'text-white/80 hover:text-white hover:bg-white/10',
                'transition-colors',
                showInfoPanel && 'bg-white/20'
              )}
              aria-label="Toggle info"
            >
              <InfoIcon className="w-5 h-5" />
            </button>

            {/* Favorite */}
            {onFavoriteToggle && (
              <button
                onClick={() => {
                  onFavoriteToggle(currentAsset);
                  haptic.medium();
                }}
                className={cn(
                  'p-2 rounded-full',
                  'transition-colors',
                  isFavorited
                    ? 'text-red-500 hover:text-red-400'
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                )}
                aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
              >
                <HeartIcon filled={isFavorited} className="w-5 h-5" />
              </button>
            )}

            {/* Select */}
            {onSelect && (
              <button
                onClick={() => {
                  onSelect(currentAsset);
                  haptic.medium();
                }}
                className={cn(
                  'p-2 rounded-full',
                  'transition-colors',
                  isSelected
                    ? 'text-primary-500 bg-primary-500/20'
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                )}
                aria-label={isSelected ? 'Deselect' : 'Select'}
              >
                <CheckIcon className="w-5 h-5" />
              </button>
            )}

            {/* Download */}
            {onDownload && currentAsset.download_url && (
              <button
                onClick={() => onDownload(currentAsset)}
                className={cn(
                  'p-2 rounded-full',
                  'text-white/80 hover:text-white hover:bg-white/10',
                  'transition-colors'
                )}
                aria-label="Download"
              >
                <DownloadIcon className="w-5 h-5" />
              </button>
            )}

            {/* Close */}
            <button
              onClick={onClose}
              className={cn(
                'p-2 rounded-full ml-2',
                'text-white/80 hover:text-white hover:bg-white/10',
                'transition-colors'
              )}
              aria-label="Close"
            >
              <CloseIcon className="w-6 h-6" />
            </button>
          </div>
        </header>

        {/* Main image area */}
        <div
          className="flex-1 flex items-center justify-center relative px-12 sm:px-20"
          style={{
            transform: `translateY(${dragOffset.y}px)`,
            transition: isDragging ? 'none' : 'transform 0.3s ease-out',
          }}
        >
          {/* LQIP placeholder */}
          {currentAsset.lqip && !isLoaded && (
            <img
              src={currentAsset.lqip}
              alt=""
              aria-hidden="true"
              className={cn(
                'absolute max-h-[80vh] max-w-full object-contain',
                'blur-xl scale-105'
              )}
            />
          )}

          {/* Full image */}
          {currentAsset.preview_url && (
            <img
              ref={imageRef}
              src={currentAsset.preview_url}
              alt={currentAsset.title || 'Photo'}
              onLoad={() => setIsLoaded(true)}
              className={cn(
                'max-h-[80vh] max-w-full object-contain',
                isLoaded ? 'opacity-100' : 'opacity-0'
              )}
              style={{
                transform: `scale(${zoom})`,
                transition: isDragging ? 'none' : 'transform 0.2s ease-out, opacity 0.3s',
              }}
            />
          )}

          {/* Navigation arrows */}
          {hasPrev && (
            <button
              onClick={goToPrev}
              className={cn(
                'absolute left-2 sm:left-4 top-1/2 -translate-y-1/2',
                'p-2 sm:p-3 rounded-full',
                'bg-black/40 hover:bg-black/60 backdrop-blur-sm',
                'text-white/80 hover:text-white',
                'transition-all duration-200',
                'touch-manipulation'
              )}
              aria-label="Previous photo"
            >
              <ArrowLeftIcon className="w-6 h-6 sm:w-8 sm:h-8" />
            </button>
          )}

          {hasNext && (
            <button
              onClick={goToNext}
              className={cn(
                'absolute right-2 sm:right-4 top-1/2 -translate-y-1/2',
                'p-2 sm:p-3 rounded-full',
                'bg-black/40 hover:bg-black/60 backdrop-blur-sm',
                'text-white/80 hover:text-white',
                'transition-all duration-200',
                'touch-manipulation'
              )}
              aria-label="Next photo"
            >
              <ArrowRightIcon className="w-6 h-6 sm:w-8 sm:h-8" />
            </button>
          )}
        </div>

        {/* Info panel - with safe area support for notched devices */}
        {showInfoPanel && (
          <div
            className={cn(
              'absolute bottom-0 left-0 right-0',
              'px-4 pt-4 sm:px-6 sm:pt-5',
              'bg-gradient-to-t from-black/80 to-transparent'
            )}
            style={{
              paddingBottom: 'max(env(safe-area-inset-bottom, 16px), 16px)',
              paddingLeft: 'max(env(safe-area-inset-left, 16px), 16px)',
              paddingRight: 'max(env(safe-area-inset-right, 16px), 16px)',
            }}
          >
            {currentAsset.title && (
              <h3 className="text-lg font-medium text-white mb-1">
                {currentAsset.title}
              </h3>
            )}
            <div className="flex flex-wrap items-center gap-4 text-sm text-white/70">
              <span>
                {currentAsset.width} × {currentAsset.height}
              </span>
              <span>{formatFileSize(currentAsset.file_size)}</span>
              <span>{currentAsset.mime_type}</span>
              {currentAsset.date_taken && (
                <span>
                  {new Date(currentAsset.date_taken).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              )}
            </div>
            {currentAsset.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {currentAsset.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 text-xs rounded-full bg-white/10 text-white/80"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }
);

Lightbox.displayName = 'Lightbox';

export default Lightbox;
