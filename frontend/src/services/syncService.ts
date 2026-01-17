/**
 * Sync Service
 * Handles background synchronization of offline actions (favorites, updates, etc.)
 * Uses Background Sync API to queue actions and sync when online
 *
 * Phase 3: Sync and Conflict Resolution
 * Subtask 3-1: Create sync service with background sync capability
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
import { syncQueueDB, syncMetadataDB, photoDB, type SyncQueueItem } from '../utils/indexedDB';
import { getTokenFromMemory } from './authService';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const TIMEOUT_MS = 30000;
const MAX_RETRY_COUNT = 3;
const SYNC_TAG = 'vdrive-sync';

/**
 * Type definitions for sync operations
 */

export interface SyncStatus {
  is_online: boolean;
  is_syncing: boolean;
  pending_count: number;
  last_sync_at?: number;
  last_error?: string;
}

export interface SyncResult {
  success: boolean;
  synced_count: number;
  failed_count: number;
  errors: Array<{ item_id: string; error: string }>;
}

export interface FavoritePhotoRequest {
  photo_id: string;
  is_favorite: boolean;
  workspace_id: string;
}

export interface ApiError {
  error: string;
  message: string;
  status_code?: number;
}

/**
 * Create axios instance for sync service
 */
function createSyncClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: TIMEOUT_MS,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
  });

  // Request interceptor - add auth token from memory
  client.interceptors.request.use(
    (config) => {
      const token = getTokenFromMemory();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiError>) => {
      // Log sync errors for debugging
      console.error('Sync API error:', error.response?.data || error.message);
      return Promise.reject(error);
    }
  );

  return client;
}

// Create singleton client
const syncClient = createSyncClient();

/**
 * Background Sync Registration
 * Registers a sync tag with the Service Worker to trigger sync when online
 */
async function registerBackgroundSync(): Promise<void> {
  if (!('serviceWorker' in navigator) || !('SyncManager' in window)) {
    console.warn('Background Sync API not supported');
    return;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    if ('sync' in registration) {
      await (registration as any).sync.register(SYNC_TAG);
      console.log('Background sync registered:', SYNC_TAG);
    }
  } catch (error) {
    console.error('Failed to register background sync:', error);
    // Continue without background sync - manual sync still works
  }
}

/**
 * Sync Queue Operations
 */
export const syncService = {
  /**
   * Queue a favorite/unfavorite action for sync
   * Adds to IndexedDB queue and registers background sync
   */
  async queueFavorite(
    photoId: string,
    workspaceId: string,
    isFavorite: boolean
  ): Promise<void> {
    const queueItem: SyncQueueItem = {
      id: crypto.randomUUID(),
      action_type: isFavorite ? 'favorite' : 'unfavorite',
      entity_type: 'photo',
      entity_id: photoId,
      workspace_id: workspaceId,
      payload: { is_favorite: isFavorite },
      created_at: Date.now(),
      retry_count: 0,
    };

    try {
      // Add to IndexedDB sync queue
      await syncQueueDB.add(queueItem);

      // Update local photo state immediately for optimistic UI
      await photoDB.updateFavorite(photoId, isFavorite);

      // Register background sync to process when online
      await registerBackgroundSync();

      // Update sync metadata
      await this.updateSyncMetadata();
    } catch (error) {
      console.error('Failed to queue favorite action:', error);
      throw new Error(
        `Failed to queue favorite: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  },

  /**
   * Queue a generic action for sync
   * Used for other types of offline actions (updates, deletes, etc.)
   */
  async queueAction(
    actionType: SyncQueueItem['action_type'],
    entityType: SyncQueueItem['entity_type'],
    entityId: string,
    workspaceId: string,
    payload: Record<string, unknown>
  ): Promise<void> {
    const queueItem: SyncQueueItem = {
      id: crypto.randomUUID(),
      action_type: actionType,
      entity_type: entityType,
      entity_id: entityId,
      workspace_id: workspaceId,
      payload,
      created_at: Date.now(),
      retry_count: 0,
    };

    try {
      await syncQueueDB.add(queueItem);
      await registerBackgroundSync();
      await this.updateSyncMetadata();
    } catch (error) {
      console.error('Failed to queue action:', error);
      throw new Error(
        `Failed to queue action: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  },

  /**
   * Process sync queue - send pending actions to API
   * Called by Service Worker on 'sync' event or manually when online
   */
  async processSyncQueue(): Promise<SyncResult> {
    const result: SyncResult = {
      success: true,
      synced_count: 0,
      failed_count: 0,
      errors: [],
    };

    try {
      // Update sync status to 'syncing'
      await syncMetadataDB.put({
        id: 'global',
        last_sync_at: Date.now(),
        sync_status: 'syncing',
        pending_actions_count: 0,
        updated_at: Date.now(),
      });

      // Get all pending sync items
      const pendingItems = await syncQueueDB.getAll();

      if (pendingItems.length === 0) {
        await syncMetadataDB.updateStatus('global', 'idle');
        return result;
      }

      // Process each item
      for (const item of pendingItems) {
        try {
          // Skip items that have exceeded max retry count
          if (item.retry_count >= MAX_RETRY_COUNT) {
            console.warn(`Skipping item ${item.id} - max retries exceeded`);
            result.errors.push({
              item_id: item.id,
              error: `Max retries (${MAX_RETRY_COUNT}) exceeded`,
            });
            result.failed_count++;
            // Keep in queue for manual resolution
            continue;
          }

          // Process based on action type
          await this.processSyncItem(item);

          // Remove from queue on success
          await syncQueueDB.delete(item.id);
          result.synced_count++;
        } catch (error) {
          // Update retry count on failure
          const errorMessage =
            error instanceof Error ? error.message : 'Unknown error';
          await syncQueueDB.updateRetry(item.id, errorMessage);

          result.errors.push({
            item_id: item.id,
            error: errorMessage,
          });
          result.failed_count++;
          result.success = false;
        }
      }

      // Update sync metadata
      await this.updateSyncMetadata();

      // Update status based on result
      const finalStatus = result.failed_count > 0 ? 'error' : 'idle';
      await syncMetadataDB.updateStatus(
        'global',
        finalStatus,
        result.errors.length > 0 ? result.errors[0].error : undefined
      );
    } catch (error) {
      console.error('Failed to process sync queue:', error);
      await syncMetadataDB.updateStatus(
        'global',
        'error',
        error instanceof Error ? error.message : 'Unknown error'
      );
      result.success = false;
    }

    return result;
  },

  /**
   * Process a single sync item - send to API
   * @internal
   */
  async processSyncItem(item: SyncQueueItem): Promise<void> {
    switch (item.action_type) {
      case 'favorite':
      case 'unfavorite':
        if (item.entity_type === 'photo') {
          await this.syncFavoritePhoto(item);
        }
        break;

      case 'update':
        // Handle other update types in future
        throw new Error(`Update action not implemented for ${item.entity_type}`);

      case 'delete':
        // Handle delete actions in future
        throw new Error(`Delete action not implemented for ${item.entity_type}`);

      default:
        throw new Error(`Unknown action type: ${item.action_type}`);
    }
  },

  /**
   * Sync favorite/unfavorite photo to API
   * @internal
   */
  async syncFavoritePhoto(item: SyncQueueItem): Promise<void> {
    const isFavorite = item.payload.is_favorite as boolean;
    const endpoint = `/gallery/photos/${item.entity_id}/favorite`;

    const payload: FavoritePhotoRequest = {
      photo_id: item.entity_id,
      is_favorite: isFavorite,
      workspace_id: item.workspace_id,
    };

    try {
      // Send favorite update to API
      await syncClient.post(endpoint, payload);
    } catch (error) {
      if (error instanceof AxiosError) {
        const status = error.response?.status;
        const message = error.response?.data?.message || error.message;

        // Handle specific error cases
        if (status === 404) {
          // Photo no longer exists - remove from queue without retry
          await syncQueueDB.delete(item.id);
          return;
        }

        throw new Error(`API error (${status}): ${message}`);
      }
      throw error;
    }
  },

  /**
   * Get current sync status
   */
  async getSyncStatus(): Promise<SyncStatus> {
    const metadata = await syncMetadataDB.getGlobal();
    const pendingItems = await syncQueueDB.getAll();

    return {
      is_online: navigator.onLine,
      is_syncing: metadata?.sync_status === 'syncing',
      pending_count: pendingItems.length,
      last_sync_at: metadata?.last_sync_at,
      last_error: metadata?.last_error,
    };
  },

  /**
   * Manually trigger sync (for user-initiated sync)
   */
  async manualSync(): Promise<SyncResult> {
    if (!navigator.onLine) {
      throw new Error('Cannot sync while offline');
    }

    return await this.processSyncQueue();
  },

  /**
   * Clear sync queue (for debugging or reset)
   */
  async clearSyncQueue(): Promise<void> {
    await syncQueueDB.clear();
    await this.updateSyncMetadata();
  },

  /**
   * Update sync metadata with current queue state
   * @internal
   */
  async updateSyncMetadata(): Promise<void> {
    const pendingItems = await syncQueueDB.getAll();
    const existingMetadata = await syncMetadataDB.getGlobal();

    await syncMetadataDB.put({
      id: 'global',
      last_sync_at: existingMetadata?.last_sync_at || Date.now(),
      sync_status: existingMetadata?.sync_status || 'idle',
      pending_actions_count: pendingItems.length,
      last_error: existingMetadata?.last_error,
      updated_at: Date.now(),
    });
  },

  /**
   * Get pending sync items count for a workspace
   */
  async getPendingCountByWorkspace(workspaceId: string): Promise<number> {
    const items = await syncQueueDB.getByWorkspace(workspaceId);
    return items.length;
  },
};

/**
 * Callback type for online/offline status changes
 */
export type OnlineStatusCallback = (isOnline: boolean) => void;

/**
 * Storage for status change callbacks
 */
const statusChangeCallbacks: Set<OnlineStatusCallback> = new Set();

/**
 * Initialize online/offline event listeners
 * Call this once when app starts (e.g., in main.tsx)
 *
 * Subtask 3-2: Online/offline detection and event handling
 */
export function initializeSyncListeners(): void {
  if (typeof window === 'undefined') {
    return;
  }

  // Listen for online event - trigger sync when back online
  window.addEventListener('online', handleOnlineEvent);

  // Listen for offline event - update metadata
  window.addEventListener('offline', handleOfflineEvent);

  // Initialize sync metadata if not exists
  syncMetadataDB.getGlobal().then((metadata) => {
    if (!metadata) {
      syncMetadataDB.put({
        id: 'global',
        last_sync_at: Date.now(),
        sync_status: 'idle',
        pending_actions_count: 0,
        updated_at: Date.now(),
      });
    }
  });
}

/**
 * Handle online event - trigger sync and notify callbacks
 * @internal
 */
async function handleOnlineEvent(): Promise<void> {
  console.log('Network online - triggering sync');

  // Notify all registered callbacks
  statusChangeCallbacks.forEach((callback) => {
    try {
      callback(true);
    } catch (error) {
      console.error('Error in online status callback:', error);
    }
  });

  // Update sync metadata to reflect online status
  try {
    const metadata = await syncMetadataDB.getGlobal();
    if (metadata) {
      await syncMetadataDB.put({
        ...metadata,
        updated_at: Date.now(),
      });
    }
  } catch (error) {
    console.error('Failed to update sync metadata on online:', error);
  }

  // Trigger automatic sync when back online
  try {
    await syncService.processSyncQueue();
  } catch (error) {
    console.error('Auto-sync failed:', error);
    // Error logged - user can manually retry via UI
  }
}

/**
 * Handle offline event - update metadata and notify callbacks
 * @internal
 */
async function handleOfflineEvent(): Promise<void> {
  console.log('Network offline - sync paused');

  // Notify all registered callbacks
  statusChangeCallbacks.forEach((callback) => {
    try {
      callback(false);
    } catch (error) {
      console.error('Error in offline status callback:', error);
    }
  });

  // Update sync metadata to reflect offline status
  try {
    const metadata = await syncMetadataDB.getGlobal();
    if (metadata) {
      await syncMetadataDB.put({
        ...metadata,
        sync_status: metadata.sync_status === 'syncing' ? 'error' : metadata.sync_status,
        last_error: metadata.sync_status === 'syncing' ? 'Network connection lost' : metadata.last_error,
        updated_at: Date.now(),
      });
    }
  } catch (error) {
    console.error('Failed to update sync metadata on offline:', error);
  }
}

/**
 * Register a callback to be notified of online/offline status changes
 * Useful for updating UI components when network status changes
 *
 * @param callback Function to call when status changes
 * @returns Cleanup function to unregister the callback
 *
 * @example
 * const unsubscribe = onStatusChange((isOnline) => {
 *   console.log('Network status:', isOnline ? 'online' : 'offline');
 * });
 * // Later: unsubscribe();
 */
export function onStatusChange(callback: OnlineStatusCallback): () => void {
  statusChangeCallbacks.add(callback);

  // Return cleanup function
  return () => {
    statusChangeCallbacks.delete(callback);
  };
}

/**
 * Get current online status
 */
export function isOnline(): boolean {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

/**
 * Cleanup sync listeners (call on app unmount if needed)
 */
export function cleanupSyncListeners(): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.removeEventListener('online', handleOnlineEvent);
  window.removeEventListener('offline', handleOfflineEvent);
  statusChangeCallbacks.clear();
}
