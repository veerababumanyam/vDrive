/**
 * PhotoThumbnail Component
 *
 * High-performance image component with LQIP (Low Quality Image Placeholder)
 * blur-up effect for instant perceived loading.
 *
 * Features:
 * - LQIP blur placeholder loads instantly
 * - Progressive reveal with smooth transition
 * - Locked state for PIN-protected photos
 * - Favorite/Selection indicators
 * - Touch-friendly with haptic feedback
 */

import {
  forwardRef,
  useState,
  useCallback,
  useRef,
  useEffect,
  type HTMLAttributes,
  type MouseEvent as ReactMouseEvent,
  type TouchEvent as ReactTouchEvent,
} from 'react';
import { cn } from '../../lib/utils';
import { useHaptic } from '../../hooks';
import type { GalleryAsset } from '../../types/gallery';

export interface PhotoThumbnailProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onClick'> {
  /** The gallery asset to display */
  asset: GalleryAsset;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** Aspect ratio */
  aspectRatio?: 'square' | 'original' | '4:3' | '3:2' | '16:9';
  /** Enable selection mode */
  selectable?: boolean;
  /** Is this photo selected */
  isSelected?: boolean;
  /** Is this photo favorited */
  isFavorited?: boolean;
  /** Show favorite count */
  showFavoriteCount?: boolean;
  /** Show selection count */
  showSelectionCount?: boolean;
  /** Click handler */
  onClick?: (asset: GalleryAsset) => void;
  /** Favorite toggle handler */
  onFavoriteToggle?: (asset: GalleryAsset) => void;
  /** Selection toggle handler */
  onSelectionToggle?: (asset: GalleryAsset) => void;
  /** PIN unlock handler for private photos */
  onUnlockClick?: (asset: GalleryAsset) => void;
}

const sizes = {
  sm: 'w-24 h-24',
  md: 'w-36 h-36 sm:w-40 sm:h-40',
  lg: 'w-48 h-48 sm:w-56 sm:h-56',
  xl: 'w-64 h-64 sm:w-80 sm:h-80',
};

const aspectRatios = {
  square: 'aspect-square',
  original: '', // Uses natural aspect ratio from asset
  '4:3': 'aspect-[4/3]',
  '3:2': 'aspect-[3/2]',
  '16:9': 'aspect-video',
};

/**
 * Heart icon for favorites
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
 * Lock icon for private photos
 */
function LockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
    </svg>
  );
}

/**
 * Check icon for selections
 */
function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

/**
 * Video play icon overlay
 */
function PlayIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

/**
 * PhotoThumbnail - Premium image component with LQIP blur-up
 */
export const PhotoThumbnail = forwardRef<HTMLDivElement, PhotoThumbnailProps>(
  (
    {
      asset,
      size = 'md',
      aspectRatio = 'square',
      selectable = false,
      isSelected = false,
      isFavorited = false,
      showFavoriteCount = false,
      showSelectionCount = false,
      onClick,
      onFavoriteToggle,
      onSelectionToggle,
      onUnlockClick,
      className,
      ...props
    },
    ref
  ) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const [hasError, setHasError] = useState(false);
    const [isLongPressing, setIsLongPressing] = useState(false);
    const longPressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const haptic = useHaptic();

    // Long press configuration
    const LONG_PRESS_DURATION = 500; // ms

    // Cleanup timer on unmount
    useEffect(() => {
      return () => {
        if (longPressTimerRef.current) {
          clearTimeout(longPressTimerRef.current);
        }
      };
    }, []);

    // Handle long press start
    const handleLongPressStart = useCallback(() => {
      longPressTimerRef.current = setTimeout(() => {
        setIsLongPressing(true);
        haptic.heavy();
        onSelectionToggle?.(asset);
      }, LONG_PRESS_DURATION);
    }, [asset, onSelectionToggle, haptic]);

    // Handle long press end
    const handleLongPressEnd = useCallback(() => {
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
        longPressTimerRef.current = null;
      }
      setIsLongPressing(false);
    }, []);

    // Touch handlers for long press
    const handleTouchStart = useCallback((e: ReactTouchEvent) => {
      // Only handle single touch
      if (e.touches.length === 1) {
        handleLongPressStart();
      }
    }, [handleLongPressStart]);

    const handleTouchEnd = useCallback(() => {
      handleLongPressEnd();
    }, [handleLongPressEnd]);

    const handleTouchMove = useCallback(() => {
      // Cancel long press if user moves finger
      handleLongPressEnd();
    }, [handleLongPressEnd]);

    // Handle image load complete
    const handleLoad = useCallback(() => {
      setIsLoaded(true);
    }, []);

    // Handle image error
    const handleError = useCallback(() => {
      setHasError(true);
    }, []);

    // Handle click (prevent if long press just occurred)
    const handleClick = useCallback(() => {
      // Don't trigger click if a long press just happened
      if (isLongPressing) return;

      if (asset.is_private && !onClick) {
        onUnlockClick?.(asset);
        haptic.medium();
      } else {
        onClick?.(asset);
        haptic.light();
      }
    }, [asset, onClick, onUnlockClick, haptic, isLongPressing]);

    // Handle favorite toggle
    const handleFavoriteClick = useCallback(
      (e: ReactMouseEvent) => {
        e.stopPropagation();
        onFavoriteToggle?.(asset);
        haptic.medium();
      },
      [asset, onFavoriteToggle, haptic]
    );

    // Handle selection toggle
    const handleSelectionClick = useCallback(
      (e: ReactMouseEvent) => {
        e.stopPropagation();
        onSelectionToggle?.(asset);
        haptic.medium();
      },
      [asset, onSelectionToggle, haptic]
    );

    const isPrivate = asset.is_private;
    const isVideo = asset.type === 'video';
    const thumbnailUrl = isPrivate ? asset.locked_thumbnail_url : asset.thumbnail_url;

    // Calculate aspect ratio from original dimensions if using 'original'
    const originalAspectStyle =
      aspectRatio === 'original' && asset.width && asset.height
        ? { aspectRatio: `${asset.width}/${asset.height}` }
        : undefined;

    return (
      <div
        ref={ref}
        className={cn(
          'group relative overflow-hidden rounded-xl sm:rounded-2xl',
          'bg-neutral-100 dark:bg-white/5',
          'cursor-pointer touch-manipulation',
          'transition-all duration-300 ease-out',
          // Enhanced hover effects with glow
          'hover:scale-[1.02]',
          'hover:shadow-[0_8px_30px_-12px_rgba(0,0,0,0.3)]',
          'hover:ring-1 hover:ring-white/20',
          'active:scale-[0.98]',
          // Selection ring
          isSelected && 'ring-4 ring-primary-500 ring-offset-2 dark:ring-offset-neutral-900',
          // Long press visual feedback
          isLongPressing && 'scale-95 opacity-80',
          // Size and aspect
          size !== 'md' && sizes[size],
          aspectRatios[aspectRatio],
          className
        )}
        style={originalAspectStyle}
        onClick={handleClick}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onTouchMove={handleTouchMove}
        onTouchCancel={handleTouchEnd}
        role="button"
        tabIndex={0}
        aria-label={
          isPrivate
            ? `Private photo: ${asset.title || 'Untitled'} - Click to unlock`
            : `Photo: ${asset.title || 'Untitled'}. Long press to select.`
        }
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
        {...props}
      >
        {/* LQIP Placeholder - Loads instantly */}
        {asset.lqip && (
          <img
            src={asset.lqip}
            alt=""
            aria-hidden="true"
            className={cn(
              'absolute inset-0 w-full h-full object-cover',
              'transition-opacity duration-500',
              // Blur effect when full image not loaded
              !isLoaded && 'blur-lg scale-110',
              // Fade out when full image loads
              isLoaded && 'opacity-0'
            )}
          />
        )}

        {/* Full quality thumbnail */}
        {thumbnailUrl && !hasError && (
          <img
            src={thumbnailUrl}
            alt={asset.title || 'Photo'}
            loading="lazy"
            onLoad={handleLoad}
            onError={handleError}
            className={cn(
              'absolute inset-0 w-full h-full object-cover',
              'transition-opacity duration-500',
              // Fade in when loaded
              !isLoaded && 'opacity-0',
              isLoaded && 'opacity-100'
            )}
          />
        )}

        {/* Error state */}
        {hasError && (
          <div className="absolute inset-0 flex items-center justify-center bg-neutral-200 dark:bg-white/10">
            <span className="text-sm text-neutral-500 dark:text-neutral-400">
              Failed to load
            </span>
          </div>
        )}

        {/* Private photo overlay */}
        {isPrivate && (
          <div
            className={cn(
              'absolute inset-0 flex flex-col items-center justify-center',
              'bg-black/60 backdrop-blur-sm',
              'transition-all duration-300'
            )}
          >
            <LockIcon className="w-10 h-10 text-white/90 mb-2" />
            <span className="text-sm font-medium text-white/90">PIN Protected</span>
          </div>
        )}

        {/* Video play button overlay */}
        {isVideo && !isPrivate && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div
              className={cn(
                'w-14 h-14 rounded-full',
                'bg-black/50 backdrop-blur-sm',
                'flex items-center justify-center',
                'transition-transform duration-200',
                'group-hover:scale-110'
              )}
            >
              <PlayIcon className="w-8 h-8 text-white ml-1" />
            </div>
          </div>
        )}

        {/* Selection checkbox (top-left) - 44px touch target for WCAG AAA */}
        {selectable && (
          <button
            onClick={handleSelectionClick}
            className={cn(
              'absolute top-0 left-0 z-10',
              'w-11 h-11',
              'flex items-center justify-center',
              'touch-manipulation'
            )}
            aria-label={isSelected ? 'Deselect photo' : 'Select photo'}
          >
            <span
              className={cn(
                'w-6 h-6 rounded-full',
                'flex items-center justify-center',
                'transition-all duration-200',
                isSelected
                  ? 'bg-primary-500 text-white scale-110'
                  : 'bg-black/40 text-white/80 hover:bg-black/60',
                'backdrop-blur-sm'
              )}
            >
              {isSelected && <CheckIcon className="w-4 h-4" />}
            </span>
          </button>
        )}

        {/* Favorite button (top-right) - 44px touch target for WCAG AAA */}
        {/* Reveals on hover (desktop) but always visible on touch (mobile) and when favorited */}
        {onFavoriteToggle && !isPrivate && (
          <button
            onClick={handleFavoriteClick}
            className={cn(
              'absolute top-0 right-0 z-10',
              'w-11 h-11',
              'flex items-center justify-center',
              'touch-manipulation',
              'transition-opacity duration-200',
              // Hide until hover on desktop, always visible when favorited
              !isFavorited && 'opacity-0 group-hover:opacity-100',
              isFavorited && 'opacity-100'
            )}
            aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
          >
            <span
              className={cn(
                'w-7 h-7 rounded-full',
                'flex items-center justify-center',
                'transition-all duration-200',
                isFavorited
                  ? 'bg-red-500/90 text-white scale-110'
                  : 'bg-black/40 text-white/80 hover:bg-black/60',
                'backdrop-blur-sm'
              )}
            >
              <HeartIcon filled={isFavorited} className="w-4 h-4" />
            </span>
          </button>
        )}

        {/* Stats overlay (bottom) */}
        {(showFavoriteCount || showSelectionCount) && !isPrivate && (
          <div
            className={cn(
              'absolute bottom-0 left-0 right-0 z-10',
              'px-2 py-1.5',
              'bg-gradient-to-t from-black/70 to-transparent',
              'flex items-center gap-3',
              'text-xs text-white/90'
            )}
          >
            {showFavoriteCount && asset.favorites_count > 0 && (
              <span className="flex items-center gap-1">
                <HeartIcon filled className="w-3.5 h-3.5 text-red-400" />
                {asset.favorites_count}
              </span>
            )}
            {showSelectionCount && asset.selections_count > 0 && (
              <span className="flex items-center gap-1">
                <CheckIcon className="w-3.5 h-3.5 text-primary-400" />
                {asset.selections_count}
              </span>
            )}
          </div>
        )}

        {/* Loading shimmer */}
        {!isLoaded && !hasError && !asset.lqip && (
          <div className="absolute inset-0 animate-pulse bg-neutral-200 dark:bg-white/10" />
        )}
      </div>
    );
  }
);

PhotoThumbnail.displayName = 'PhotoThumbnail';

export default PhotoThumbnail;
