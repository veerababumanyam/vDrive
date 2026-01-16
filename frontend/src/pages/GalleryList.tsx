/**
 * GalleryList Page
 *
 * Authenticated gallery listing for photographers/staff.
 * Features:
 * - Gallery cards with cover images
 * - Filter by status (draft, published, archived)
 * - Search galleries
 * - Pagination
 * - Quick actions (publish, archive, delete)
 */


import { useNavigate, useSearchParams } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useBreakpoint } from '../hooks';
import { GalleryCard } from '../components/gallery';
import { AppButton } from '../components/ui/AppButton';
import { AppCard } from '../components/ui/AppCard';
import { AppInput } from '../components/ui/AppInput';
import { useGalleries } from '../hooks/useGallery';
import type { Gallery, GalleryStatus } from '../types/gallery';

/**
 * Plus icon for create button
 */
function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
    </svg>
  );
}

/**
 * Search icon
 */
function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
    </svg>
  );
}

/**
 * Empty state component
 */
function EmptyState({ hasFilters }: { hasFilters: boolean }) {
  const navigate = useNavigate();

  return (
    <AppCard variant="glass" padding="xl" className="text-center">
      <div
        className={cn(
          'w-20 h-20 mx-auto mb-4 rounded-full',
          'bg-neutral-100 dark:bg-white/5',
          'flex items-center justify-center'
        )}
      >
        <svg
          className="w-10 h-10 text-neutral-400 dark:text-neutral-500"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M22 16V4c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2zm-11-4l2.03 2.71L16 11l4 5H8l3-4zM2 6v14c0 1.1.9 2 2 2h14v-2H4V6H2z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-neutral-700 dark:text-neutral-300 mb-2">
        {hasFilters ? 'No galleries found' : 'No galleries yet'}
      </h3>
      <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-6">
        {hasFilters
          ? 'Try adjusting your filters to find what you\'re looking for'
          : 'Create your first gallery to get started'}
      </p>
      {!hasFilters && (
        <AppButton
          variant="primary"
          leftIcon={<PlusIcon className="w-5 h-5" />}
          onClick={() => navigate('/galleries/new')}
          glowOnHover
        >
          Create Gallery
        </AppButton>
      )}
    </AppCard>
  );
}

/**
 * Loading skeleton
 */
function GallerySkeleton() {
  return (
    <div className="h-64 sm:h-72 rounded-2xl sm:rounded-3xl bg-neutral-200 dark:bg-white/10 animate-pulse" />
  );
}

const statusFilters: Array<{ value: GalleryStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All Galleries' },
  { value: 'published', label: 'Published' },
  { value: 'draft', label: 'Drafts' },
  { value: 'archived', label: 'Archived' },
];

export function GalleryListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isMobile } = useBreakpoint();

  // Filters from URL params
  const statusFilter = (searchParams.get('status') as GalleryStatus | 'all') || 'all';
  const searchQuery = searchParams.get('q') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);

  // Fetch galleries using React Query
  const { 
    data, 
    isLoading, 
    error: queryError 
  } = useGalleries(page, 12, statusFilter === 'all' ? undefined : statusFilter);

  const galleries = data?.galleries || [];
  const totalCount = data?.total || 0;
  const hasNext = data?.has_next || false;
  const error = queryError instanceof Error ? queryError.message : null;

  // Handle status filter change
  const handleStatusChange = (status: GalleryStatus | 'all') => {
    const params = new URLSearchParams(searchParams);
    if (status === 'all') {
      params.delete('status');
    } else {
      params.set('status', status);
    }
    params.set('page', '1'); // Reset to page 1
    setSearchParams(params);
  };

  // Handle search
  const handleSearch = (query: string) => {
    const params = new URLSearchParams(searchParams);
    if (query) {
      params.set('q', query);
    } else {
      params.delete('q');
    }
    params.set('page', '1');
    setSearchParams(params);
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', newPage.toString());
    setSearchParams(params);
  };

  // Handle gallery click
  const handleGalleryClick = (gallery: Gallery) => {
    navigate(`/galleries/${gallery.gallery_id}`);
  };

  // Filter galleries by search query (client-side)
  const filteredGalleries = searchQuery
    ? galleries.filter(
        (g) =>
          g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          g.client_name?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : galleries;

  const hasFilters = statusFilter !== 'all' || !!searchQuery;

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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-neutral-800 dark:text-white">
                Galleries
              </h1>
              {!isLoading && (
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                  {totalCount} {totalCount === 1 ? 'gallery' : 'galleries'}
                </p>
              )}
            </div>

            <AppButton
              variant="primary"
              leftIcon={<PlusIcon className="w-5 h-5" />}
              onClick={() => navigate('/galleries/new')}
              glowOnHover
            >
              {isMobile ? 'New' : 'Create Gallery'}
            </AppButton>
          </div>

          {/* Filters */}
          <div className="mt-4 flex flex-col sm:flex-row gap-3">
            {/* Search */}
            <div className="flex-1 max-w-md">
              <AppInput
                type="search"
                placeholder="Search galleries..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                leftIcon={<SearchIcon className="w-5 h-5 text-neutral-400" />}
                size="md"
              />
            </div>

            {/* Status tabs */}
            <div className="flex overflow-x-auto gap-2 pb-1 scrollbar-hide">
              {statusFilters.map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => handleStatusChange(filter.value)}
                  className={cn(
                    'flex-shrink-0 px-4 py-2 rounded-full',
                    'text-sm font-medium',
                    'transition-all duration-200',
                    statusFilter === filter.value
                      ? 'bg-primary-500 text-white'
                      : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:bg-white/10 dark:text-neutral-300 dark:hover:bg-white/15'
                  )}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        {/* Error state */}
        {error && (
          <AppCard variant="glass" padding="md" className="mb-6 bg-red-50 dark:bg-red-500/10">
            <p className="text-red-700 dark:text-red-300">{error}</p>
          </AppCard>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <GallerySkeleton key={i} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && filteredGalleries.length === 0 && (
          <EmptyState hasFilters={hasFilters} />
        )}

        {/* Gallery grid */}
        {!isLoading && filteredGalleries.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {filteredGalleries.map((gallery) => (
                <GalleryCard
                  key={gallery.gallery_id}
                  gallery={gallery}
                  onClick={handleGalleryClick}
                  showStats
                  showStatus
                  showDate
                />
              ))}
            </div>

            {/* Pagination */}
            {(page > 1 || hasNext) && (
              <div className="flex justify-center gap-3 mt-8">
                <AppButton
                  variant="outline"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                >
                  Previous
                </AppButton>
                <span className="flex items-center px-4 text-neutral-600 dark:text-neutral-400">
                  Page {page}
                </span>
                <AppButton
                  variant="outline"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={!hasNext}
                >
                  Next
                </AppButton>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default GalleryListPage;
