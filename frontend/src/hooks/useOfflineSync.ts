/**
 * useOfflineSync Hook
 * Manages sync state, online/offline status, and manual sync operations
 */

import { useState, useCallback, useEffect } from 'react';
import {
  syncService,
  onStatusChange,
  isOnline,
  type SyncStatus,
  type SyncResult,
} from '../services/syncService';

// ============================================
// Types
// ============================================

export interface UseOfflineSyncOptions {
  /**
   * Callback when sync completes successfully
   */
  onSyncSuccess?: (result: SyncResult) => void;

  /**
   * Callback when sync fails
   */
  onSyncError?: (error: string) => void;

  /**
   * Auto-refresh interval in milliseconds (default: 5000ms)
   * Set to 0 to disable auto-refresh
   */
  refreshInterval?: number;
}

export interface UseOfflineSyncReturn {
  /**
   * Current online/offline status
   */
  isOnline: boolean;

  /**
   * Whether a sync operation is currently in progress
   */
  isSyncing: boolean;

  /**
   * Number of pending actions waiting to sync
   */
  pendingCount: number;

  /**
   * Timestamp of last successful sync (milliseconds since epoch)
   */
  lastSyncAt?: number;

  /**
   * Last error message if sync failed
   */
  lastError?: string;

  /**
   * Manually trigger a sync operation
   * Returns true if sync succeeded, false otherwise
   */
  sync: () => Promise<boolean>;

  /**
   * Refresh sync status from IndexedDB
   */
  refreshStatus: () => Promise<void>;

  /**
   * Clear all pending sync items (use with caution)
   */
  clearQueue: () => Promise<void>;

  /**
   * Whether the hook is currently loading sync status
   */
  isLoading: boolean;
}

// ============================================
// Hook
// ============================================

export function useOfflineSync(
  options: UseOfflineSyncOptions = {}
): UseOfflineSyncReturn {
  const { onSyncSuccess, onSyncError, refreshInterval = 5000 } = options;

  // Sync state
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    is_online: isOnline(),
    is_syncing: false,
    pending_count: 0,
  });

  // Loading state
  const [isLoading, setIsLoading] = useState(true);

  // Refresh sync status from service
  const refreshStatus = useCallback(async () => {
    try {
      const status = await syncService.getSyncStatus();
      setSyncStatus(status);
    } catch (error) {
      console.error('Failed to refresh sync status:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Manual sync trigger
  const sync = useCallback(async (): Promise<boolean> => {
    if (!syncStatus.is_online) {
      const errorMessage = 'Cannot sync while offline';
      onSyncError?.(errorMessage);
      return false;
    }

    if (syncStatus.is_syncing) {
      const errorMessage = 'Sync already in progress';
      onSyncError?.(errorMessage);
      return false;
    }

    try {
      // Update local state to show syncing
      setSyncStatus((prev) => ({ ...prev, is_syncing: true }));

      // Trigger sync
      const result = await syncService.manualSync();

      // Refresh status after sync
      await refreshStatus();

      // Call success callback
      onSyncSuccess?.(result);

      return result.success;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown sync error';

      // Update status with error
      setSyncStatus((prev) => ({
        ...prev,
        is_syncing: false,
        last_error: errorMessage,
      }));

      // Call error callback
      onSyncError?.(errorMessage);

      return false;
    }
  }, [syncStatus.is_online, syncStatus.is_syncing, onSyncSuccess, onSyncError, refreshStatus]);

  // Clear sync queue
  const clearQueue = useCallback(async () => {
    try {
      await syncService.clearSyncQueue();
      await refreshStatus();
    } catch (error) {
      console.error('Failed to clear sync queue:', error);
      throw error;
    }
  }, [refreshStatus]);

  // Subscribe to online/offline status changes
  useEffect(() => {
    // Update status when network changes
    const unsubscribe = onStatusChange((online) => {
      setSyncStatus((prev) => ({
        ...prev,
        is_online: online,
      }));

      // Refresh full status when coming back online
      if (online) {
        refreshStatus();
      }
    });

    // Initial status load
    refreshStatus();

    // Cleanup on unmount
    return () => {
      unsubscribe();
    };
  }, [refreshStatus]);

  // Auto-refresh status at interval
  useEffect(() => {
    if (refreshInterval <= 0) {
      return;
    }

    const intervalId = setInterval(() => {
      refreshStatus();
    }, refreshInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [refreshInterval, refreshStatus]);

  return {
    isOnline: syncStatus.is_online,
    isSyncing: syncStatus.is_syncing,
    pendingCount: syncStatus.pending_count,
    lastSyncAt: syncStatus.last_sync_at,
    lastError: syncStatus.last_error,
    sync,
    refreshStatus,
    clearQueue,
    isLoading,
  };
}

export default useOfflineSync;
