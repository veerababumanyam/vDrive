/**
 * GalleryGrid Component
 *
 * Responsive masonry-style grid for displaying photo thumbnails.
 * Supports infinite scroll with prefetching at 75% scroll.
 *
 * Features:
 * - Responsive columns (2 on mobile, 3 on tablet, 4+ on desktop)
 * - Infinite scroll with prefetching
 * - Selection mode for batch operations
 * - Empty and loading states
 */

import {
  forwardRef,
  useEffect,
  useRef,
  useCallback,
  type HTMLAttributes,
} from 'react';
import { cn } from '../../lib/utils';
import { PhotoThumbnail, type PhotoThumbnailProps } from './PhotoThumbnail';
import type { GalleryAsset } from '../../types/gallery';

export interface GalleryGridProps extends HTMLAttributes<HTMLDivElement> {
  /** Array of assets to display */
  assets: GalleryAsset[];
  /** Column count override (auto-responsive if not set) */
  columns?: 2 | 3 | 4 | 5 | 6;
  /** Gap between items */
  gap?: 'sm' | 'md' | 'lg';
  /** Enable selection mode */
  selectable?: boolean;
  /** Array of selected asset IDs */
  selectedIds?: string[];
  /** Array of favorited asset IDs */
  favoritedIds?: string[];
  /** Loading state */
  isLoading?: boolean;
  /** Has more items to load */
  hasMore?: boolean;
  /** Called when scrolled to 75% (for prefetching) */
  onLoadMore?: () => void;
  /** Photo click handler */
  onPhotoClick?: (asset: GalleryAsset) => void;
  /** Favorite toggle handler */
  onFavoriteToggle?: (asset: GalleryAsset) => void;
  /** Selection toggle handler */
  onSelectionToggle?: (asset: GalleryAsset) => void;
  /** Unlock private photo handler */
  onUnlockClick?: (asset: GalleryAsset) => void;
  /** Props to pass to each thumbnail */
  thumbnailProps?: Partial<PhotoThumbnailProps>;
}

const gapSizes = {
  sm: 'gap-2',
  md: 'gap-3 sm:gap-4',
  lg: 'gap-4 sm:gap-6',
};

const columnClasses = {
  2: 'grid-cols-2',
  3: 'grid-cols-2 sm:grid-cols-3',
  4: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4',
  5: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5',
  6: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6',
};

/**
 * Loading skeleton for photos with premium shimmer effect
 */
function PhotoSkeleton({ index = 0 }: { index?: number }) {
  return (
    <div
      className={cn(
        'aspect-square rounded-xl sm:rounded-2xl',
        'bg-neutral-200 dark:bg-white/10',
        'relative overflow-hidden'
      )}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      {/* Shimmer overlay */}
      <div className="absolute inset-0 animate-shimmer" />
    </div>
  );
}

/**
 * Empty state when no photos - with animated icon and slide-up entrance
 */
function EmptyState() {
  return (
    <div
      className={cn(
        'col-span-full flex flex-col items-center justify-center',
        'py-16 px-6 text-center',
        'animate-slide-up'
      )}
    >
      {/* Floating animated icon */}
      <div
        className={cn(
          'w-20 h-20 rounded-full mb-4',
          'bg-gradient-to-br from-primary-100 to-primary-50',
          'dark:from-primary-900/20 dark:to-primary-800/10',
          'flex items-center justify-center',
          'animate-float'
        )}
      >
        <svg
          className="w-10 h-10 text-primary-400"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-neutral-700 dark:text-neutral-300 mb-1">
        No photos yet
      </h3>
      <p className="text-sm text-neutral-500 dark:text-neutral-400 max-w-xs">
        Photos will appear here once they're added to the gallery
      </p>
    </div>
  );
}

/**
 * Loading indicator at bottom
 */
function LoadingMore() {
  return (
    <div className="col-span-full flex justify-center py-8">
      <div
        className={cn(
          'w-8 h-8 rounded-full border-2',
          'border-primary-500/30 border-t-primary-500',
          'animate-spin'
        )}
      />
    </div>
  );
}

export const GalleryGrid = forwardRef<HTMLDivElement, GalleryGridProps>(
  (
    {
      assets,
      columns = 4,
      gap = 'md',
      selectable = false,
      selectedIds = [],
      favoritedIds = [],
      isLoading = false,
      hasMore = false,
      onLoadMore,
      onPhotoClick,
      onFavoriteToggle,
      onSelectionToggle,
      onUnlockClick,
      thumbnailProps,
      className,
      ...props
    },
    ref
  ) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    const loadMoreTriggered = useRef(false);

    // Intersection observer for infinite scroll
    useEffect(() => {
      if (!hasMore || !onLoadMore) return;

      const observer = new IntersectionObserver(
        (entries) => {
          const [entry] = entries;
          // Trigger at 75% scroll (entry is visible when we're 25% from bottom)
          if (entry.isIntersecting && !loadMoreTriggered.current && !isLoading) {
            loadMoreTriggered.current = true;
            onLoadMore();
            // Reset after a short delay to allow for debouncing
            setTimeout(() => {
              loadMoreTriggered.current = false;
            }, 1000);
          }
        },
        {
          rootMargin: '25% 0px', // Trigger 25% before reaching the sentinel
        }
      );

      // Create a sentinel element at 75% scroll position
      const sentinel = document.createElement('div');
      sentinel.style.height = '1px';
      sentinel.style.width = '100%';
      scrollRef.current?.appendChild(sentinel);
      observer.observe(sentinel);

      return () => {
        observer.disconnect();
        sentinel.remove();
      };
    }, [hasMore, onLoadMore, isLoading]);

    // Check if asset is selected
    const isSelected = useCallback(
      (assetId: string) => selectedIds.includes(assetId),
      [selectedIds]
    );

    // Check if asset is favorited
    const isFavorited = useCallback(
      (assetId: string) => favoritedIds.includes(assetId),
      [favoritedIds]
    );

    // Empty state
    if (!isLoading && (!assets || assets.length === 0)) {
      return (
        <div
          ref={ref}
          className={cn('grid', columnClasses[columns], gapSizes[gap], className)}
          {...props}
        >
          <EmptyState />
        </div>
      );
    }

    // Loading skeletons
    if (isLoading && assets.length === 0) {
      return (
        <div
          ref={ref}
          className={cn('grid', columnClasses[columns], gapSizes[gap], className)}
          {...props}
        >
          {Array.from({ length: 12 }).map((_, i) => (
            <PhotoSkeleton key={i} index={i} />
          ))}
        </div>
      );
    }

    return (
      <div
        ref={(node) => {
          // Merge refs
          if (typeof ref === 'function') {
            ref(node);
          } else if (ref) {
            ref.current = node;
          }
          (scrollRef as React.MutableRefObject<HTMLDivElement | null>).current = node;
        }}
        className={cn('grid', columnClasses[columns], gapSizes[gap], className)}
        {...props}
      >
        {assets.map((asset, index) => (
          <div
            key={asset.gallery_asset_id}
            className="animate-fade-in-scale"
            style={{
              animationDelay: `${Math.min(index * 50, 500)}ms`,
              animationFillMode: 'backwards',
            }}
          >
            <PhotoThumbnail
              asset={asset}
              selectable={selectable}
              isSelected={isSelected(asset.gallery_asset_id)}
              isFavorited={isFavorited(asset.gallery_asset_id)}
              onClick={onPhotoClick}
              onFavoriteToggle={onFavoriteToggle}
              onSelectionToggle={onSelectionToggle}
              onUnlockClick={onUnlockClick}
              {...thumbnailProps}
            />
          </div>
        ))}

        {/* Loading indicator for infinite scroll */}
        {isLoading && hasMore && <LoadingMore />}
      </div>
    );
  }
);

GalleryGrid.displayName = 'GalleryGrid';

export default GalleryGrid;
