/**
 * ExportProgress Component
 * Real-time progress tracking for export jobs
 *
 * Subtask-4-3: Create export progress component with real-time updates
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getExportJobStatus,
  cancelExportJob,
  formatFileSize,
  formatDuration,
  estimateTimeRemaining,
  getStatusDisplayText,
  isExportActive,
  isExportComplete,
  type ExportResponse,
} from '../../services/export-api';
import { AppButton } from '../ui/AppButton';
import { cn } from '../../lib/utils';

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
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" x2="12" y1="15" y2="3" />
    </svg>
  );
}

function XCircleIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <path d="m15 9-6 6" />
      <path d="m9 9 6 6" />
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

function AlertCircleIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn('animate-spin', className)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface ExportProgressProps {
  /** Export job ID to track */
  jobId: string;
  /** Callback when job completes */
  onComplete?: (job: ExportResponse) => void;
  /** Callback when job is cancelled */
  onCancel?: (jobId: string) => void;
  /** Additional class names */
  className?: string;
}

// ============================================
// Component
// ============================================

/**
 * Export progress component with real-time updates
 *
 * Polls job status every 2 seconds when active (pending/processing)
 *
 * @example
 * ```tsx
 * <ExportProgress
 *   jobId="123"
 *   onComplete={(job) => handleExportComplete(job)}
 * />
 * ```
 */
export function ExportProgress({
  jobId,
  onComplete,
  onCancel,
  className,
}: ExportProgressProps) {
  const queryClient = useQueryClient();
  const [startTime] = useState(() => new Date());

  // Fetch export job status
  const { data: job, isLoading, error } = useQuery({
    queryKey: ['exportJob', jobId],
    queryFn: () => getExportJobStatus(jobId),
    refetchInterval: (query) => {
      const jobData = query.state.data;
      // Poll every 2 seconds when active, stop when complete/failed/cancelled
      return jobData && isExportActive(jobData.status) ? 2000 : false;
    },
    staleTime: 0, // Always refetch to get latest status
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: () => cancelExportJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exportJob', jobId] });
      queryClient.invalidateQueries({ queryKey: ['exportJobs'] });
      onCancel?.(jobId);
    },
  });

  // Call onComplete when job finishes
  useEffect(() => {
    if (job && job.status === 'completed') {
      onComplete?.(job);
    }
  }, [job, onComplete]);

  // Estimate remaining time
  const remainingSeconds = job ? estimateTimeRemaining(job, startTime) : null;

  // Get status color
  const getStatusColor = (status: ExportResponse['status']) => {
    switch (status) {
      case 'pending':
        return 'text-white/60';
      case 'processing':
        return 'text-primary-400';
      case 'completed':
        return 'text-success-400';
      case 'failed':
        return 'text-error-400';
      case 'cancelled':
        return 'text-white/40';
      default:
        return 'text-white/60';
    }
  };

  // Get status icon
  const getStatusIcon = (status: ExportResponse['status']) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="w-5 h-5" />;
      case 'processing':
        return <LoaderIcon className="w-5 h-5" />;
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5" />;
      case 'failed':
        return <AlertCircleIcon className="w-5 h-5" />;
      case 'cancelled':
        return <XCircleIcon className="w-5 h-5" />;
      default:
        return <ClockIcon className="w-5 h-5" />;
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={cn('p-4 rounded-xl bg-white/5 border border-white/10 animate-pulse', className)}>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-5 h-5 bg-white/10 rounded" />
          <div className="h-4 bg-white/10 rounded w-24" />
        </div>
        <div className="h-2 bg-white/10 rounded-full mb-2" />
        <div className="h-3 bg-white/10 rounded w-32" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={cn('p-4 rounded-xl bg-error-500/20 border border-error-500/30', className)}>
        <div className="flex items-center gap-2 text-error-400">
          <AlertCircleIcon className="w-5 h-5" />
          <p className="text-sm font-medium">Failed to load export status</p>
        </div>
      </div>
    );
  }

  if (!job) return null;

  return (
    <div className={cn('p-4 rounded-xl bg-white/5 border border-white/10', className)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={cn('shrink-0', getStatusColor(job.status))}>
            {getStatusIcon(job.status)}
          </div>
          <div>
            <p className="text-white font-medium text-sm">
              {getStatusDisplayText(job.status)}
            </p>
            <p className="text-white/50 text-xs mt-0.5">
              Export #{job.id.slice(0, 8)}
            </p>
          </div>
        </div>

        {/* Actions */}
        {isExportActive(job.status) && (
          <AppButton
            variant="ghost"
            size="sm"
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
            leftIcon={<XCircleIcon className="w-4 h-4" />}
          >
            Cancel
          </AppButton>
        )}

        {job.status === 'completed' && job.file_url && (
          <AppButton
            variant="primary"
            size="sm"
            onClick={() => window.open(job.file_url, '_blank')}
            leftIcon={<DownloadIcon className="w-4 h-4" />}
          >
            Download
          </AppButton>
        )}
      </div>

      {/* Progress Bar (for active jobs) */}
      {isExportActive(job.status) && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-white/60">
              {job.processed_assets} / {job.total_assets} assets
            </span>
            <span className="text-white font-medium">
              {job.progress_percentage}%
            </span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${job.progress_percentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Details */}
      <div className="flex items-center justify-between text-xs text-white/50">
        <div className="flex items-center gap-4">
          {/* Export Type */}
          <span className="capitalize">{job.export_type} export</span>

          {/* File Size (when completed) */}
          {job.file_size && (
            <span>{formatFileSize(job.file_size)}</span>
          )}

          {/* Estimated Time (when processing) */}
          {job.status === 'processing' && remainingSeconds !== null && remainingSeconds > 0 && (
            <span className="text-primary-400">
              ~{formatDuration(remainingSeconds)} remaining
            </span>
          )}
        </div>

        {/* Timestamp */}
        <span>
          {new Date(job.created_at).toLocaleTimeString()}
        </span>
      </div>

      {/* Error Message */}
      {job.status === 'failed' && job.error_message && (
        <div className="mt-3 p-2 rounded bg-error-500/20 border border-error-500/30">
          <p className="text-xs text-error-400">{job.error_message}</p>
        </div>
      )}

      {/* Expiration Notice (when completed) */}
      {job.status === 'completed' && job.expires_at && (
        <div className="mt-3 p-2 rounded bg-white/5">
          <p className="text-xs text-white/50">
            Download expires: {new Date(job.expires_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}

export default ExportProgress;
