/**
 * GalleryList Page
 *
 * Premium iOS-inspired gallery listing for photographers.
 * Features:
 * - 📸 Photography-centric design with glassmorphism
 * - 🎨 Animated backgrounds and particle effects
 * - 📱 Mobile-first with haptic feedback
 * - ♿ WCAG 2.1 AA compliant
 */

import { useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useBreakpoint, useHaptic, usePrefersReducedMotion, useScrollPosition } from '../hooks';
import { GalleryCard } from '../components/gallery';
import { AppButton } from '../components/ui/AppButton';
import { AppInput } from '../components/ui/AppInput';
import { useGalleries } from '../hooks/useGallery';
import type { Gallery, GalleryStatus } from '../types/gallery';
import { WorkspaceLayout } from '../components/workspace/WorkspaceLayout';

// ============================================================================
// Icons
// ============================================================================

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
    </svg>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
    </svg>
  );
}

function GridIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 3v8h8V3H3zm6 6H5V5h4v4zm-6 4v8h8v-8H3zm6 6H5v-4h4v4zm4-16v8h8V3h-8zm6 6h-4V5h4v4zm-6 4v8h8v-8h-8zm6 6h-4v-4h4v4z" />
    </svg>
  );
}

function ListIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z" />
    </svg>
  );
}

function SparkleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3zm7 14l.62 2.38L22 20l-2.38.62L19 23l-.62-2.38L16 20l2.38-.62L19 17zM5 17l.62 2.38L8 20l-2.38.62L5 23l-.62-2.38L2 20l2.38-.62L5 17z" />
    </svg>
  );
}

function CameraIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 15.2c1.94 0 3.5-1.56 3.5-3.5S13.94 8.2 12 8.2s-3.5 1.56-3.5 3.5 1.56 3.5 3.5 3.5zM9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z" />
    </svg>
  );
}

// ============================================================================
// Animated Backgrounds
// ============================================================================

function MorphingBlob() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) {
    return (
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-accent-500/10 rounded-full blur-3xl" />
      </div>
    );
  }

  return (
    <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
      <div
        className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 bg-primary-500/10 rounded-full blur-3xl animate-morph"
        style={{ animationDuration: '20s' }}
      />
      <div
        className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-accent-500/10 rounded-full blur-3xl animate-morph"
        style={{ animationDuration: '25s', animationDelay: '-5s' }}
      />
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1/3 h-1/3 bg-purple-500/5 rounded-full blur-3xl animate-morph"
        style={{ animationDuration: '15s', animationDelay: '-10s' }}
      />
    </div>
  );
}

function ParticleEffect() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) return null;

  const particles = useMemo(() =>
    Array.from({ length: 12 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      size: Math.random() * 4 + 2,
      delay: Math.random() * 5,
      duration: Math.random() * 10 + 15,
    })), []
  );

  return (
    <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
      {particles.map(particle => (
        <div
          key={particle.id}
          className="absolute rounded-full bg-primary-500/20 animate-float"
          style={{
            left: particle.left,
            top: particle.top,
            width: particle.size,
            height: particle.size,
            animationDelay: `${particle.delay}s`,
            animationDuration: `${particle.duration}s`,
          }}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Status Filter Chips
// ============================================================================

interface StatusChipProps {
  label: string;
  emoji: string;
  isActive: boolean;
  count?: number;
  onClick: () => void;
}

function StatusChip({ label, emoji, isActive, count, onClick }: StatusChipProps) {
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  const handleClick = useCallback(() => {
    haptic.light();
    onClick();
  }, [haptic, onClick]);

  return (
    <button
      onClick={handleClick}
      className={cn(
        'flex-shrink-0 inline-flex items-center gap-2 px-4 py-2.5 rounded-full',
        'text-sm font-medium whitespace-nowrap',
        'min-h-[44px]', // WCAG touch target
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
        'focus-visible:ring-offset-neutral-50 dark:focus-visible:ring-offset-neutral-900',
        !prefersReducedMotion && 'transition-all duration-300',
        isActive
          ? cn(
              'bg-primary-500 text-white',
              'shadow-lg shadow-primary-500/30',
              'dark:shadow-primary-500/20'
            )
          : cn(
              'bg-white/80 dark:bg-white/10',
              'text-neutral-700 dark:text-neutral-300',
              'border border-neutral-200/80 dark:border-white/10',
              'backdrop-blur-xl',
              'hover:bg-white hover:border-neutral-300',
              'dark:hover:bg-white/15 dark:hover:border-white/20',
              'active:scale-[0.98]'
            )
      )}
      aria-pressed={isActive}
      role="switch"
    >
      <span aria-hidden="true">{emoji}</span>
      <span>{label}</span>
      {count !== undefined && count > 0 && (
        <span
          className={cn(
            'px-1.5 py-0.5 rounded-full text-xs font-semibold',
            isActive
              ? 'bg-white/20 text-white'
              : 'bg-neutral-200 text-neutral-600 dark:bg-white/10 dark:text-neutral-400'
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
}

// ============================================================================
// View Toggle
// ============================================================================

interface ViewToggleProps {
  view: 'grid' | 'list';
  onViewChange: (view: 'grid' | 'list') => void;
}

function ViewToggle({ view, onViewChange }: ViewToggleProps) {
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        'flex p-1 rounded-xl',
        'bg-white/80 dark:bg-white/10',
        'border border-neutral-200/80 dark:border-white/10',
        'backdrop-blur-xl'
      )}
      role="radiogroup"
      aria-label="View mode"
    >
      {[
        { id: 'grid', icon: GridIcon, label: 'Grid view' },
        { id: 'list', icon: ListIcon, label: 'List view' },
      ].map(({ id, icon: Icon, label }) => (
        <button
          key={id}
          onClick={() => {
            haptic.light();
            onViewChange(id as 'grid' | 'list');
          }}
          className={cn(
            'p-2.5 rounded-lg min-w-[44px] min-h-[44px]',
            'flex items-center justify-center',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
            !prefersReducedMotion && 'transition-all duration-200',
            view === id
              ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
              : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-white'
          )}
          role="radio"
          aria-checked={view === id}
          aria-label={label}
        >
          <Icon className="w-5 h-5" />
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState({ hasFilters }: { hasFilters: boolean }) {
  const navigate = useNavigate();
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        'relative overflow-hidden',
        'rounded-3xl p-8 sm:p-12 text-center',
        // Glassmorphism
        'bg-white/80 dark:bg-white/[0.08]',
        'border border-neutral-200/80 dark:border-white/10',
        'backdrop-blur-xl',
        // iOS-style shadows
        'shadow-[0_8px_40px_-12px_rgba(0,0,0,0.15),0_0_0_1px_rgba(255,255,255,0.05)_inset]',
        'dark:shadow-[0_8px_40px_-12px_rgba(0,0,0,0.4),0_0_0_1px_rgba(255,255,255,0.05)_inset]',
        // Animation
        !prefersReducedMotion && 'animate-fade-in-up'
      )}
    >
      {/* Decorative background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary-500/10 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-accent-500/10 via-transparent to-transparent rounded-full blur-3xl" />
      </div>

      {/* Icon */}
      <div
        className={cn(
          'w-24 h-24 mx-auto mb-6 rounded-3xl',
          'bg-gradient-to-br from-primary-500/20 to-accent-500/20',
          'dark:from-primary-500/30 dark:to-accent-500/30',
          'flex items-center justify-center',
          'shadow-lg shadow-primary-500/10'
        )}
      >
        <span className="text-5xl" role="img" aria-hidden="true">
          {hasFilters ? '🔍' : '📸'}
        </span>
      </div>

      {/* Content */}
      <h3 className="text-xl sm:text-2xl font-bold text-neutral-800 dark:text-white mb-3">
        {hasFilters ? 'No galleries found' : 'Create your first gallery'}
      </h3>
      <p className="text-neutral-600 dark:text-neutral-400 mb-8 max-w-md mx-auto">
        {hasFilters
          ? 'Try adjusting your filters or search terms to find what you\'re looking for ✨'
          : 'Start showcasing your amazing photography by creating a stunning gallery 🎨'}
      </p>

      {/* CTA */}
      {!hasFilters && (
        <AppButton
          variant="primary"
          size="lg"
          leftIcon={<PlusIcon className="w-5 h-5" />}
          onClick={() => {
            haptic.medium();
            navigate('/galleries/new');
          }}
          glowOnHover
          className="min-h-[48px]"
        >
          Create Gallery
        </AppButton>
      )}
    </div>
  );
}

// ============================================================================
// Loading Skeleton
// ============================================================================

function GalleryGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'h-64 sm:h-72 rounded-2xl sm:rounded-3xl overflow-hidden',
            'bg-white/60 dark:bg-white/[0.06]',
            'border border-neutral-200/60 dark:border-white/5',
            'backdrop-blur-xl'
          )}
          style={{ animationDelay: `${i * 100}ms` }}
        >
          <div className="w-full h-full bg-gradient-to-r from-neutral-200 via-neutral-100 to-neutral-200 dark:from-white/5 dark:via-white/10 dark:to-white/5 animate-shimmer bg-[length:200%_100%]" />
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// Floating Action Button (Mobile)
// ============================================================================

function FloatingActionButton({ onClick }: { onClick: () => void }) {
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();
  const { scrollY, direction } = useScrollPosition();

  // Hide FAB when scrolling down
  const isVisible = !(direction === 'down' && scrollY > 100);

  return (
    <button
      onClick={() => {
        haptic.medium();
        onClick();
      }}
      className={cn(
        'fixed bottom-6 right-6 z-40',
        'w-14 h-14 rounded-full',
        'bg-gradient-to-br from-primary-500 to-primary-600',
        'shadow-[0_8px_30px_-4px_rgba(14,165,233,0.5)]',
        'flex items-center justify-center',
        'focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/50',
        'active:scale-95',
        !prefersReducedMotion && 'transition-all duration-300',
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'
      )}
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      aria-label="Create new gallery"
    >
      <PlusIcon className="w-6 h-6 text-white" />
    </button>
  );
}

// ============================================================================
// Pagination
// ============================================================================

interface PaginationProps {
  page: number;
  hasNext: boolean;
  onPageChange: (page: number) => void;
}

function Pagination({ page, hasNext, onPageChange }: PaginationProps) {
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  if (page <= 1 && !hasNext) return null;

  return (
    <div
      className={cn(
        'flex items-center justify-center gap-3 mt-8',
        !prefersReducedMotion && 'animate-fade-in-up'
      )}
      style={{ animationDelay: '300ms' }}
    >
      <AppButton
        variant="outline"
        onClick={() => {
          haptic.light();
          onPageChange(page - 1);
        }}
        disabled={page <= 1}
        className="min-h-[44px]"
      >
        ← Previous
      </AppButton>

      <div
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-xl',
          'bg-white/80 dark:bg-white/10',
          'border border-neutral-200/80 dark:border-white/10',
          'backdrop-blur-xl'
        )}
      >
        <span className="text-neutral-600 dark:text-neutral-400">Page</span>
        <span className="font-semibold text-neutral-800 dark:text-white">{page}</span>
      </div>

      <AppButton
        variant="outline"
        onClick={() => {
          haptic.light();
          onPageChange(page + 1);
        }}
        disabled={!hasNext}
        className="min-h-[44px]"
      >
        Next →
      </AppButton>
    </div>
  );
}

// ============================================================================
// Status Filters Config
// ============================================================================

const statusFilters: Array<{
  value: GalleryStatus | 'all';
  label: string;
  emoji: string;
}> = [
  { value: 'all', label: 'All', emoji: '🖼️' },
  { value: 'published', label: 'Published', emoji: '✅' },
  { value: 'draft', label: 'Drafts', emoji: '📝' },
  { value: 'archived', label: 'Archived', emoji: '📦' },
];

// ============================================================================
// Main Component
// ============================================================================

export function GalleryListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isMobile, isTablet } = useBreakpoint();
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  // Filters from URL params
  const statusFilter = (searchParams.get('status') as GalleryStatus | 'all') || 'all';
  const searchQuery = searchParams.get('q') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);
  const viewMode = (searchParams.get('view') as 'grid' | 'list') || 'grid';

  // Fetch galleries
  const {
    data,
    isLoading,
    error: queryError
  } = useGalleries(page, 12, statusFilter === 'all' ? undefined : statusFilter);

  const galleries = data?.galleries || [];
  const totalCount = data?.total || 0;
  const hasNext = data?.has_next || false;
  const error = queryError instanceof Error ? queryError.message : null;

  // Handlers
  const handleStatusChange = useCallback((status: GalleryStatus | 'all') => {
    haptic.light();
    const params = new URLSearchParams(searchParams);
    if (status === 'all') {
      params.delete('status');
    } else {
      params.set('status', status);
    }
    params.set('page', '1');
    setSearchParams(params);
  }, [searchParams, setSearchParams, haptic]);

  const handleSearch = useCallback((query: string) => {
    const params = new URLSearchParams(searchParams);
    if (query) {
      params.set('q', query);
    } else {
      params.delete('q');
    }
    params.set('page', '1');
    setSearchParams(params);
  }, [searchParams, setSearchParams]);

  const handlePageChange = useCallback((newPage: number) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', newPage.toString());
    setSearchParams(params);
  }, [searchParams, setSearchParams]);

  const handleViewChange = useCallback((view: 'grid' | 'list') => {
    haptic.light();
    const params = new URLSearchParams(searchParams);
    params.set('view', view);
    setSearchParams(params);
  }, [searchParams, setSearchParams, haptic]);

  const handleGalleryClick = useCallback((gallery: Gallery) => {
    haptic.light();
    navigate(`/galleries/${gallery.gallery_id}`);
  }, [navigate, haptic]);

  const handleCreateGallery = useCallback(() => {
    haptic.medium();
    navigate('/galleries/new');
  }, [navigate, haptic]);

  // Filter galleries by search query (client-side)
  const filteredGalleries = useMemo(() => {
    if (!searchQuery) return galleries;
    const query = searchQuery.toLowerCase();
    return galleries.filter(
      (g) =>
        g.title.toLowerCase().includes(query) ||
        g.client_name?.toLowerCase().includes(query)
    );
  }, [galleries, searchQuery]);

  const hasFilters = statusFilter !== 'all' || !!searchQuery;

  return (
    <WorkspaceLayout currentPage="galleries" pageTitle="Galleries">
      <div
        className={cn(
          'min-h-screen relative',
          'bg-neutral-50 dark:bg-neutral-900'
        )}
      >
        {/* Animated Background */}
        <MorphingBlob />
        <ParticleEffect />

        {/* Page Header */}
        <header
          className={cn(
            'bg-white/80 dark:bg-neutral-900/80',
            'backdrop-blur-xl',
            'border-b border-neutral-200/80 dark:border-white/10',
            'shadow-sm'
          )}
        >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          {/* Title Row */}
          <div
            className={cn(
              'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4',
              !prefersReducedMotion && 'animate-fade-in-up'
            )}
          >
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  'w-12 h-12 rounded-2xl',
                  'bg-gradient-to-br from-primary-500 to-primary-600',
                  'shadow-lg shadow-primary-500/30',
                  'flex items-center justify-center'
                )}
              >
                <CameraIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-neutral-800 dark:text-white flex items-center gap-2">
                  Galleries
                  <SparkleIcon className="w-6 h-6 text-amber-400" />
                </h1>
                {!isLoading && (
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {totalCount} {totalCount === 1 ? 'gallery' : 'galleries'} 📸
                  </p>
                )}
              </div>
            </div>

            {/* Desktop Create Button */}
            {!isMobile && (
              <AppButton
                variant="primary"
                leftIcon={<PlusIcon className="w-5 h-5" />}
                onClick={handleCreateGallery}
                glowOnHover
                className="min-h-[44px]"
              >
                {isTablet ? 'New' : 'Create Gallery'}
              </AppButton>
            )}
          </div>

          {/* Search & Filters Row */}
          <div
            className={cn(
              'mt-4 flex flex-col sm:flex-row gap-3',
              !prefersReducedMotion && 'animate-fade-in-up stagger-2'
            )}
          >
            {/* Search Input */}
            <div className="flex-1 max-w-md">
              <AppInput
                type="search"
                placeholder="Search galleries... 🔍"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                leftIcon={<SearchIcon className="w-5 h-5 text-neutral-400" />}
                size="md"
                className="min-h-[44px]"
              />
            </div>

            {/* View Toggle (Desktop) */}
            {!isMobile && (
              <ViewToggle view={viewMode} onViewChange={handleViewChange} />
            )}
          </div>

          {/* Status Filter Chips */}
          <div
            className={cn(
              'mt-4 flex overflow-x-auto gap-2 pb-1 -mx-4 px-4 sm:mx-0 sm:px-0',
              'scrollbar-hide',
              !prefersReducedMotion && 'animate-fade-in-up stagger-3'
            )}
            role="group"
            aria-label="Filter galleries by status"
          >
            {statusFilters.map((filter) => (
              <StatusChip
                key={filter.value}
                label={filter.label}
                emoji={filter.emoji}
                isActive={statusFilter === filter.value}
                onClick={() => handleStatusChange(filter.value)}
              />
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        {/* Error State */}
        {error && (
          <div
            className={cn(
              'mb-6 p-4 rounded-2xl',
              'bg-rose-50 dark:bg-rose-500/10',
              'border border-rose-200 dark:border-rose-500/20',
              'text-rose-700 dark:text-rose-300',
              !prefersReducedMotion && 'animate-fade-in-up'
            )}
            role="alert"
          >
            <p className="flex items-center gap-2">
              <span aria-hidden="true">⚠️</span>
              {error}
            </p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && <GalleryGridSkeleton count={6} />}

        {/* Empty State */}
        {!isLoading && filteredGalleries.length === 0 && (
          <EmptyState hasFilters={hasFilters} />
        )}

        {/* Gallery Grid */}
        {!isLoading && filteredGalleries.length > 0 && (
          <>
            <div
              className={cn(
                viewMode === 'grid'
                  ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6'
                  : 'flex flex-col gap-4'
              )}
            >
              {filteredGalleries.map((gallery, index) => (
                <div
                  key={gallery.gallery_id}
                  className={cn(
                    !prefersReducedMotion && 'animate-fade-in-up'
                  )}
                  style={{
                    animationDelay: prefersReducedMotion ? '0ms' : `${index * 50}ms`,
                  }}
                >
                  <GalleryCard
                    gallery={gallery}
                    variant={viewMode === 'list' ? 'compact' : 'default'}
                    onClick={handleGalleryClick}
                    showStats
                    showStatus
                    showDate={viewMode === 'grid'}
                  />
                </div>
              ))}
            </div>

            {/* Pagination */}
            <Pagination
              page={page}
              hasNext={hasNext}
              onPageChange={handlePageChange}
            />
          </>
        )}
      </main>

        {/* Mobile FAB */}
        {isMobile && <FloatingActionButton onClick={handleCreateGallery} />}

        {/* Safe area padding for bottom nav */}
        <div
          className="h-20 sm:h-0"
          style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
        />
      </div>
    </WorkspaceLayout>
  );
}

export default GalleryListPage;
