/**
 * SyncStatus Indicator Component
 * Shows online/offline status, pending sync count, and sync progress
 *
 * Phase 4: Offline UI Components
 * Subtask 4-2: Create SyncStatus indicator component
 */

import { useCallback } from 'react';
import { useOfflineSync } from '../hooks/useOfflineSync';
import { cn } from '../lib/utils';

// ============================================
// Icons
// ============================================

function WifiIcon({ className }: { className?: string }) {
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
      <path d="M5 12.55a11 11 0 0 1 14.08 0" />
      <path d="M1.42 9a16 16 0 0 1 21.16 0" />
      <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
      <line x1="12" y1="20" x2="12.01" y2="20" />
    </svg>
  );
}

function WifiOffIcon({ className }: { className?: string }) {
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
      <line x1="2" y1="2" x2="22" y2="22" />
      <path d="M8.5 16.5a5 5 0 0 1 7 0" />
      <path d="M2 8.82a15 15 0 0 1 4.17-2.65" />
      <path d="M10.66 5c4.01-.36 8.14.9 11.34 3.76" />
      <path d="M16.85 11.25a10 10 0 0 1 2.22 1.68" />
      <path d="M5 13a10 10 0 0 1 5.24-2.76" />
      <line x1="12" y1="20" x2="12.01" y2="20" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
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
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
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

// ============================================
// Types
// ============================================

export interface SyncStatusProps {
  /** Additional class names */
  className?: string;
  /** Variant - compact shows icon only, full shows text */
  variant?: 'compact' | 'full';
  /** Show manual sync button */
  showSyncButton?: boolean;
}

// ============================================
// Component
// ============================================

/**
 * SyncStatus - Real-time sync status indicator
 *
 * Displays:
 * - Online/offline status with color-coded indicator
 * - Pending sync count badge
 * - Sync in progress spinner
 * - Optional manual sync button
 *
 * @example
 * ```tsx
 * // Compact mode (icon only)
 * <SyncStatus variant="compact" />
 *
 * // Full mode with text and sync button
 * <SyncStatus variant="full" showSyncButton />
 * ```
 */
export function SyncStatus({
  className,
  variant = 'compact',
  showSyncButton = false,
}: SyncStatusProps) {
  const { isOnline, isSyncing, pendingCount, sync, isLoading } = useOfflineSync({
    refreshInterval: 5000, // Refresh every 5 seconds
  });

  const handleSync = useCallback(async () => {
    if (!isOnline || isSyncing) return;
    await sync();
  }, [isOnline, isSyncing, sync]);

  if (isLoading) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <div className="w-2 h-2 rounded-full bg-neutral-300 dark:bg-white/20 animate-pulse" />
        {variant === 'full' && (
          <span className="text-sm text-neutral-500 dark:text-white/50">Loading...</span>
        )}
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Status Indicator */}
      <div className="relative flex items-center gap-2">
        {/* Online/Offline Icon */}
        <div
          className={cn(
            'relative flex items-center justify-center',
            variant === 'compact' ? 'w-5 h-5' : 'w-6 h-6'
          )}
        >
          {isOnline ? (
            <WifiIcon
              className={cn(
                'transition-colors duration-200',
                isSyncing
                  ? 'text-primary-500 animate-pulse'
                  : 'text-success-500 dark:text-success-400'
              )}
            />
          ) : (
            <WifiOffIcon className="text-error-500 dark:text-error-400" />
          )}

          {/* Syncing Pulse Animation */}
          {isSyncing && (
            <span className="absolute inset-0 flex items-center justify-center">
              <span className="absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75 animate-ping" />
            </span>
          )}

          {/* Pending Count Badge */}
          {!isSyncing && pendingCount > 0 && (
            <span
              className={cn(
                'absolute -top-1 -right-1 flex items-center justify-center',
                'min-w-[16px] h-4 px-1 text-[10px] font-bold',
                'text-white bg-warning-500 rounded-full',
                'shadow-sm'
              )}
            >
              {pendingCount > 99 ? '99+' : pendingCount}
            </span>
          )}
        </div>

        {/* Status Text (Full Variant) */}
        {variant === 'full' && (
          <div className="flex flex-col">
            <span
              className={cn(
                'text-sm font-medium transition-colors duration-200',
                isOnline
                  ? 'text-neutral-900 dark:text-white'
                  : 'text-error-600 dark:text-error-400'
              )}
            >
              {isSyncing ? 'Syncing...' : isOnline ? 'Online' : 'Offline'}
            </span>

            {/* Pending Count Text */}
            {pendingCount > 0 && !isSyncing && (
              <span className="text-xs text-warning-600 dark:text-warning-400">
                {pendingCount} pending
              </span>
            )}

            {/* Synced State */}
            {!isSyncing && pendingCount === 0 && isOnline && (
              <span className="text-xs text-success-600 dark:text-success-400 flex items-center gap-1">
                <CheckCircleIcon className="w-3 h-3" />
                Synced
              </span>
            )}
          </div>
        )}
      </div>

      {/* Manual Sync Button */}
      {showSyncButton && variant === 'full' && (
        <button
          onClick={handleSync}
          disabled={!isOnline || isSyncing}
          className={cn(
            'p-1.5 rounded-lg transition-all duration-200',
            'hover:bg-neutral-100 dark:hover:bg-white/10',
            'active:scale-95',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
          )}
          title={
            !isOnline
              ? 'Cannot sync while offline'
              : isSyncing
                ? 'Sync in progress'
                : 'Sync now'
          }
        >
          <RefreshIcon
            className={cn(
              'w-4 h-4',
              isSyncing && 'animate-spin',
              isOnline && !isSyncing
                ? 'text-primary-500 dark:text-primary-400'
                : 'text-neutral-400 dark:text-white/30'
            )}
          />
        </button>
      )}

      {/* Compact Sync Button */}
      {showSyncButton && variant === 'compact' && pendingCount > 0 && isOnline && (
        <button
          onClick={handleSync}
          disabled={isSyncing}
          className={cn(
            'p-1 rounded-md transition-all duration-200',
            'hover:bg-primary-50 dark:hover:bg-primary-500/10',
            'active:scale-95',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          title="Sync pending changes"
        >
          <RefreshIcon
            className={cn(
              'w-3.5 h-3.5 text-primary-500',
              isSyncing && 'animate-spin'
            )}
          />
        </button>
      )}
    </div>
  );
}

export default SyncStatus;
