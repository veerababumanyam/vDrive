/**
 * GalleryCard Component
 *
 * Premium card component for displaying gallery previews in list/grid views.
 * Features glass morphism, hover effects, and status indicators.
 */

import { forwardRef, useCallback, type HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';
import { useHaptic } from '../../hooks';
import type { Gallery } from '../../types/gallery';

export interface GalleryCardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onClick'> {
  /** Gallery data */
  gallery: Gallery;
  /** Card size variant */
  variant?: 'compact' | 'default' | 'large';
  /** Click handler */
  onClick?: (gallery: Gallery) => void;
  /** Show stats */
  showStats?: boolean;
  /** Show status badge */
  showStatus?: boolean;
  /** Show date */
  showDate?: boolean;
}

/**
 * Camera icon
 */
function CameraIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 15.2c1.94 0 3.5-1.56 3.5-3.5S13.94 8.2 12 8.2s-3.5 1.56-3.5 3.5 1.56 3.5 3.5 3.5zM9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z" />
    </svg>
  );
}

/**
 * Video icon
 */
function VideoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z" />
    </svg>
  );
}

/**
 * Heart icon
 */
function HeartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  );
}

/**
 * Calendar icon
 */
function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z" />
    </svg>
  );
}

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

/**
 * Format file size for display
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Format date for display
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export const GalleryCard = forwardRef<HTMLDivElement, GalleryCardProps>(
  (
    {
      gallery,
      variant = 'default',
      onClick,
      showStats = true,
      showStatus = true,
      showDate = true,
      className,
      ...props
    },
    ref
  ) => {
    const haptic = useHaptic();

    const handleClick = useCallback(() => {
      onClick?.(gallery);
      haptic.light();
    }, [gallery, onClick, haptic]);

    const coverUrl = gallery.cover_url;

    return (
      <div
        ref={ref}
        className={cn(
          'group relative overflow-hidden',
          'rounded-2xl sm:rounded-3xl',
          'cursor-pointer touch-manipulation',
          // Glass morphism background
          'bg-white/80 dark:bg-white/[0.08]',
          'border border-neutral-200/80 dark:border-white/10',
          'backdrop-blur-xl',
          // Shadow with Apple-style glow on hover
          'shadow-lg shadow-neutral-200/40 dark:shadow-black/20',
          // Transitions
          'transition-all duration-300 ease-out',
          // Hover effects - enhanced with primary color glow
          'hover:shadow-[0_20px_40px_-12px_rgba(0,0,0,0.2),0_0_30px_-5px_rgba(14,165,233,0.25)]',
          'hover:-translate-y-1',
          'hover:border-neutral-300 dark:hover:border-white/25',
          'hover:ring-1 hover:ring-primary-500/20',
          'active:scale-[0.98]',
          // Variants
          variant === 'compact' && 'h-48',
          variant === 'default' && 'h-64 sm:h-72',
          variant === 'large' && 'h-80 sm:h-96',
          className
        )}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label={`View gallery: ${gallery.title}`}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
        {...props}
      >
        {/* Cover Image */}
        <div className="absolute inset-0">
          {coverUrl ? (
            <img
              src={coverUrl}
              alt={gallery.title}
              className={cn(
                'w-full h-full object-cover',
                'transition-transform duration-500',
                'group-hover:scale-105'
              )}
            />
          ) : (
            <div
              className={cn(
                'w-full h-full',
                'bg-gradient-to-br from-primary-500/20 via-accent-500/10 to-transparent',
                'dark:from-primary-500/30 dark:via-accent-500/20'
              )}
            />
          )}
          {/* Gradient overlay for text readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
        </div>

        {/* Status Badge */}
        {showStatus && (
          <div className="absolute top-3 right-3 z-10">
            <span
              className={cn(
                'inline-flex items-center px-2.5 py-1 rounded-full',
                'text-xs font-medium',
                'backdrop-blur-sm',
                statusColors[gallery.status]
              )}
            >
              {statusLabels[gallery.status]}
            </span>
          </div>
        )}

        {/* Content */}
        <div className="absolute bottom-0 left-0 right-0 z-10 p-4 sm:p-5">
          {/* Client Name */}
          {gallery.client_name && (
            <p className="text-xs text-white/70 font-medium mb-1 truncate">
              {gallery.client_name}
            </p>
          )}

          {/* Title */}
          <h3
            className={cn(
              'font-semibold text-white mb-2 truncate',
              variant === 'compact' ? 'text-lg' : 'text-xl sm:text-2xl'
            )}
          >
            {gallery.title}
          </h3>

          {/* Stats Row */}
          {showStats && (
            <div className="flex flex-wrap items-center gap-3 text-xs sm:text-sm text-white/80">
              {/* Photo count */}
              <span className="flex items-center gap-1">
                <CameraIcon className="w-4 h-4" />
                {gallery.photo_count}
              </span>

              {/* Video count */}
              {gallery.video_count > 0 && (
                <span className="flex items-center gap-1">
                  <VideoIcon className="w-4 h-4" />
                  {gallery.video_count}
                </span>
              )}

              {/* Favorites count */}
              {gallery.favorites_count > 0 && (
                <span className="flex items-center gap-1">
                  <HeartIcon className="w-3.5 h-3.5 text-red-400" />
                  {gallery.favorites_count}
                </span>
              )}

              {/* Total size */}
              {gallery.total_size_bytes > 0 && variant !== 'compact' && (
                <span className="text-white/60">
                  {formatFileSize(gallery.total_size_bytes)}
                </span>
              )}
            </div>
          )}

          {/* Date */}
          {showDate && gallery.shoot_date && variant !== 'compact' && (
            <div className="flex items-center gap-1.5 mt-2 text-xs text-white/60">
              <CalendarIcon className="w-3.5 h-3.5" />
              {formatDate(gallery.shoot_date)}
            </div>
          )}
        </div>

        {/* Hover glow effect */}
        <div
          className={cn(
            'absolute inset-0 opacity-0 transition-opacity duration-300',
            'bg-gradient-to-t from-primary-500/20 to-transparent',
            'group-hover:opacity-100'
          )}
        />
      </div>
    );
  }
);

GalleryCard.displayName = 'GalleryCard';

export default GalleryCard;
