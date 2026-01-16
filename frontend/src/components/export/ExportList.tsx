/**
 * ExportList Component
 * List of export jobs with status filtering
 *
 * Subtask-4-3: Create export progress component with real-time updates
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listExportJobs, type ExportStatus } from '../../services/export-api';
import { AppCard } from '../ui/AppCard';
import { ExportProgress } from './ExportProgress';
import { cn } from '../../lib/utils';

// ============================================
// Icons
// ============================================

function FilterIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
  );
}

function InboxIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface ExportListProps {
  /** Callback when an export completes */
  onExportComplete?: () => void;
  /** Additional class names */
  className?: string;
}

// ============================================
// Status Filter Options
// ============================================

const statusFilters: { value: ExportStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Queued' },
  { value: 'processing', label: 'Processing' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

// ============================================
// Component
// ============================================

/**
 * List of export jobs with real-time progress tracking
 *
 * @example
 * ```tsx
 * <ExportList onExportComplete={(job) => handleExportComplete(job)} />
 * ```
 */
export function ExportList({ onExportComplete, className }: ExportListProps) {
  const [statusFilter, setStatusFilter] = useState<ExportStatus | 'all'>('all');

  // Fetch export jobs
  const { data, isLoading, error } = useQuery({
    queryKey: ['exportJobs', statusFilter],
    queryFn: () => {
      return listExportJobs({
        status: statusFilter === 'all' ? undefined : statusFilter,
        page: 1,
        page_size: 50,
      });
    },
    refetchInterval: 5000, // Refetch list every 5 seconds to catch new jobs
    staleTime: 0,
  });

  // Loading state
  if (isLoading) {
    return (
      <AppCard variant="glass" padding="lg" className={cn('w-full', className)}>
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-white/5 rounded-xl" />
          ))}
        </div>
      </AppCard>
    );
  }

  // Error state
  if (error) {
    return (
      <AppCard variant="glass" padding="lg" className={cn('w-full', className)}>
        <div className="text-center py-8">
          <div className="w-12 h-12 rounded-full bg-error-500/20 flex items-center justify-center mx-auto mb-4">
            <InboxIcon className="w-6 h-6 text-error-400" />
          </div>
          <p className="text-white font-medium mb-1">Failed to load exports</p>
          <p className="text-sm text-white/60">
            {(error as { message?: string })?.message || 'An error occurred'}
          </p>
        </div>
      </AppCard>
    );
  }

  const jobs = data?.jobs || [];

  return (
    <AppCard variant="glass" padding="lg" className={cn('w-full', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <InboxIcon className="w-5 h-5 text-primary-400" />
          <h2 className="text-lg font-semibold text-white">Export Jobs</h2>
          {data && (
            <span className="text-sm text-white/50">({data.total})</span>
          )}
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <FilterIcon className="w-4 h-4 text-white/40" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ExportStatus | 'all')}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm',
              'bg-white/5 border border-white/10',
              'text-white',
              'focus:outline-none focus:ring-2 focus:ring-primary-500/50',
              'cursor-pointer transition-colors',
              'hover:bg-white/10'
            )}
          >
            {statusFilters.map((filter) => (
              <option key={filter.value} value={filter.value}>
                {filter.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Job List */}
      {jobs.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
            <InboxIcon className="w-8 h-8 text-white/40" />
          </div>
          <p className="text-white/60 font-medium mb-1">No export jobs</p>
          <p className="text-sm text-white/40">
            {statusFilter === 'all'
              ? 'Create your first export to get started'
              : `No ${statusFilter} exports found`}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <ExportProgress
              key={job.id}
              jobId={job.id}
              onComplete={onExportComplete}
            />
          ))}
        </div>
      )}
    </AppCard>
  );
}

export default ExportList;
