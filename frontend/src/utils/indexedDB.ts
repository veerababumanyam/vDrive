/**
 * IndexedDB Utility Wrapper
 * Type-safe wrapper for offline gallery storage using IndexedDB
 *
 * Stores:
 * - galleries: Downloaded gallery metadata
 * - photos: Downloaded photo data and blob URLs
 * - syncQueue: Pending actions to sync when online (favorites, etc.)
 * - syncMetadata: Sync state and timestamps
 *
 * T1-3: Create IndexedDB utility wrapper
 */

import { openDB, type IDBPDatabase, type DBSchema } from 'idb';

/**
 * Database configuration
 */
const DB_NAME = 'vDriveOffline';
const DB_VERSION = 1;

/**
 * Type definitions for IndexedDB stores
 */

export interface OfflineGallery {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  cover_photo_url?: string;
  photo_count: number;
  total_size_bytes: number;
  downloaded_at: number; // Unix timestamp
  encrypted: boolean;
  last_synced?: number; // Unix timestamp
}

export interface OfflinePhoto {
  id: string;
  gallery_id: string;
  workspace_id: string;
  file_name: string;
  file_size_bytes: number;
  thumbnail_url?: string;
  preview_url?: string;
  full_url?: string;
  // Blob data for offline access
  thumbnail_blob?: Blob;
  preview_blob?: Blob;
  full_blob?: Blob;
  // Metadata
  width?: number;
  height?: number;
  taken_at?: number;
  is_favorite: boolean;
  downloaded_at: number;
}

export interface SyncQueueItem {
  id: string; // UUID for queue item
  action_type: 'favorite' | 'unfavorite' | 'delete' | 'update';
  entity_type: 'photo' | 'gallery';
  entity_id: string;
  workspace_id: string;
  payload: Record<string, unknown>;
  created_at: number;
  retry_count: number;
  last_error?: string;
}

export interface SyncMetadata {
  id: string; // Gallery ID or 'global'
  last_sync_at: number;
  sync_status: 'idle' | 'syncing' | 'error';
  pending_actions_count: number;
  last_error?: string;
  updated_at: number;
}

/**
 * IndexedDB Schema definition
 */
interface VDriveOfflineDB extends DBSchema {
  galleries: {
    key: string;
    value: OfflineGallery;
    indexes: {
      'by-workspace': string;
      'by-downloaded': number;
    };
  };
  photos: {
    key: string;
    value: OfflinePhoto;
    indexes: {
      'by-gallery': string;
      'by-workspace': string;
      'by-favorite': number; // 1 for favorite, 0 for not
    };
  };
  syncQueue: {
    key: string;
    value: SyncQueueItem;
    indexes: {
      'by-created': number;
      'by-workspace': string;
    };
  };
  syncMetadata: {
    key: string;
    value: SyncMetadata;
  };
}

/**
 * Database connection singleton
 */
let dbInstance: IDBPDatabase<VDriveOfflineDB> | null = null;

/**
 * Initialize and open IndexedDB connection
 * Creates object stores and indexes on first run
 */
async function getDB(): Promise<IDBPDatabase<VDriveOfflineDB>> {
  if (dbInstance) {
    return dbInstance;
  }

  try {
    dbInstance = await openDB<VDriveOfflineDB>(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion, newVersion, transaction) {
        // V1: Initial schema
        if (oldVersion < 1) {
          // Galleries store
          const galleriesStore = db.createObjectStore('galleries', { keyPath: 'id' });
          galleriesStore.createIndex('by-workspace', 'workspace_id', { unique: false });
          galleriesStore.createIndex('by-downloaded', 'downloaded_at', { unique: false });

          // Photos store
          const photosStore = db.createObjectStore('photos', { keyPath: 'id' });
          photosStore.createIndex('by-gallery', 'gallery_id', { unique: false });
          photosStore.createIndex('by-workspace', 'workspace_id', { unique: false });
          photosStore.createIndex('by-favorite', 'is_favorite', { unique: false });

          // Sync queue store
          const syncQueueStore = db.createObjectStore('syncQueue', { keyPath: 'id' });
          syncQueueStore.createIndex('by-created', 'created_at', { unique: false });
          syncQueueStore.createIndex('by-workspace', 'workspace_id', { unique: false });

          // Sync metadata store
          db.createObjectStore('syncMetadata', { keyPath: 'id' });
        }

        // Future migrations would go here
        // if (oldVersion < 2) { ... }
      },
      blocked() {
        console.warn('IndexedDB upgrade blocked - close other tabs with this app');
      },
      blocking() {
        console.warn('IndexedDB blocking other connections');
        // Close current connection to allow upgrade
        dbInstance?.close();
        dbInstance = null;
      },
      terminated() {
        console.error('IndexedDB connection unexpectedly terminated');
        dbInstance = null;
      },
    });

    return dbInstance;
  } catch (error) {
    console.error('Failed to open IndexedDB:', error);
    throw new Error(`IndexedDB initialization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Close database connection
 * Call this when app is shutting down or for cleanup
 */
export async function closeDB(): Promise<void> {
  if (dbInstance) {
    dbInstance.close();
    dbInstance = null;
  }
}

/**
 * Gallery Operations
 */
export const galleryDB = {
  /**
   * Save a gallery to offline storage
   */
  async put(gallery: OfflineGallery): Promise<void> {
    const db = await getDB();
    await db.put('galleries', gallery);
  },

  /**
   * Get a gallery by ID
   */
  async get(id: string): Promise<OfflineGallery | undefined> {
    const db = await getDB();
    return await db.get('galleries', id);
  },

  /**
   * Get all galleries for a workspace
   */
  async getByWorkspace(workspaceId: string): Promise<OfflineGallery[]> {
    const db = await getDB();
    return await db.getAllFromIndex('galleries', 'by-workspace', workspaceId);
  },

  /**
   * Get all downloaded galleries
   */
  async getAll(): Promise<OfflineGallery[]> {
    const db = await getDB();
    return await db.getAll('galleries');
  },

  /**
   * Delete a gallery from offline storage
   */
  async delete(id: string): Promise<void> {
    const db = await getDB();
    await db.delete('galleries', id);
  },

  /**
   * Clear all galleries
   */
  async clear(): Promise<void> {
    const db = await getDB();
    await db.clear('galleries');
  },
};

/**
 * Photo Operations
 */
export const photoDB = {
  /**
   * Save a photo to offline storage
   */
  async put(photo: OfflinePhoto): Promise<void> {
    const db = await getDB();
    await db.put('photos', photo);
  },

  /**
   * Save multiple photos in batch
   */
  async putBatch(photos: OfflinePhoto[]): Promise<void> {
    const db = await getDB();
    const tx = db.transaction('photos', 'readwrite');
    await Promise.all([
      ...photos.map((photo) => tx.store.put(photo)),
      tx.done,
    ]);
  },

  /**
   * Get a photo by ID
   */
  async get(id: string): Promise<OfflinePhoto | undefined> {
    const db = await getDB();
    return await db.get('photos', id);
  },

  /**
   * Get all photos for a gallery
   */
  async getByGallery(galleryId: string): Promise<OfflinePhoto[]> {
    const db = await getDB();
    return await db.getAllFromIndex('photos', 'by-gallery', galleryId);
  },

  /**
   * Get all favorite photos for a workspace
   */
  async getFavoritesByWorkspace(workspaceId: string): Promise<OfflinePhoto[]> {
    const db = await getDB();
    const allPhotos = await db.getAllFromIndex('photos', 'by-workspace', workspaceId);
    return allPhotos.filter((photo) => photo.is_favorite);
  },

  /**
   * Update photo favorite status
   */
  async updateFavorite(photoId: string, isFavorite: boolean): Promise<void> {
    const db = await getDB();
    const photo = await db.get('photos', photoId);
    if (photo) {
      photo.is_favorite = isFavorite;
      await db.put('photos', photo);
    }
  },

  /**
   * Delete a photo from offline storage
   */
  async delete(id: string): Promise<void> {
    const db = await getDB();
    await db.delete('photos', id);
  },

  /**
   * Delete all photos for a gallery
   */
  async deleteByGallery(galleryId: string): Promise<void> {
    const db = await getDB();
    const photos = await db.getAllFromIndex('photos', 'by-gallery', galleryId);
    const tx = db.transaction('photos', 'readwrite');
    await Promise.all([
      ...photos.map((photo) => tx.store.delete(photo.id)),
      tx.done,
    ]);
  },

  /**
   * Clear all photos
   */
  async clear(): Promise<void> {
    const db = await getDB();
    await db.clear('photos');
  },
};

/**
 * Sync Queue Operations
 */
export const syncQueueDB = {
  /**
   * Add an action to sync queue
   */
  async add(item: SyncQueueItem): Promise<void> {
    const db = await getDB();
    await db.add('syncQueue', item);
  },

  /**
   * Get all pending sync items
   */
  async getAll(): Promise<SyncQueueItem[]> {
    const db = await getDB();
    return await db.getAll('syncQueue');
  },

  /**
   * Get pending items for a workspace
   */
  async getByWorkspace(workspaceId: string): Promise<SyncQueueItem[]> {
    const db = await getDB();
    return await db.getAllFromIndex('syncQueue', 'by-workspace', workspaceId);
  },

  /**
   * Remove an item from sync queue after successful sync
   */
  async delete(id: string): Promise<void> {
    const db = await getDB();
    await db.delete('syncQueue', id);
  },

  /**
   * Update retry count and error for failed sync
   */
  async updateRetry(id: string, error: string): Promise<void> {
    const db = await getDB();
    const item = await db.get('syncQueue', id);
    if (item) {
      item.retry_count += 1;
      item.last_error = error;
      await db.put('syncQueue', item);
    }
  },

  /**
   * Clear all sync queue items
   */
  async clear(): Promise<void> {
    const db = await getDB();
    await db.clear('syncQueue');
  },
};

/**
 * Sync Metadata Operations
 */
export const syncMetadataDB = {
  /**
   * Save or update sync metadata
   */
  async put(metadata: SyncMetadata): Promise<void> {
    const db = await getDB();
    await db.put('syncMetadata', metadata);
  },

  /**
   * Get sync metadata by ID
   */
  async get(id: string): Promise<SyncMetadata | undefined> {
    const db = await getDB();
    return await db.get('syncMetadata', id);
  },

  /**
   * Get global sync metadata
   */
  async getGlobal(): Promise<SyncMetadata | undefined> {
    return await this.get('global');
  },

  /**
   * Update sync status
   */
  async updateStatus(id: string, status: SyncMetadata['sync_status'], error?: string): Promise<void> {
    const db = await getDB();
    const metadata = await db.get('syncMetadata', id);
    if (metadata) {
      metadata.sync_status = status;
      metadata.updated_at = Date.now();
      if (error !== undefined) {
        metadata.last_error = error;
      }
      await db.put('syncMetadata', metadata);
    }
  },

  /**
   * Clear all sync metadata
   */
  async clear(): Promise<void> {
    const db = await getDB();
    await db.clear('syncMetadata');
  },
};

/**
 * Storage Management
 */
export const storageDB = {
  /**
   * Get estimated storage usage
   * Returns size in bytes
   */
  async getStorageEstimate(): Promise<{ usage: number; quota: number } | null> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage || 0,
        quota: estimate.quota || 0,
      };
    }
    return null;
  },

  /**
   * Calculate total size of offline galleries
   */
  async getTotalGallerySize(): Promise<number> {
    const galleries = await galleryDB.getAll();
    return galleries.reduce((total, gallery) => total + gallery.total_size_bytes, 0);
  },

  /**
   * Clear all offline data (galleries, photos, sync queue)
   */
  async clearAll(): Promise<void> {
    await Promise.all([
      galleryDB.clear(),
      photoDB.clear(),
      syncQueueDB.clear(),
      syncMetadataDB.clear(),
    ]);
  },

  /**
   * Delete a complete gallery with all its photos
   */
  async deleteGallery(galleryId: string): Promise<void> {
    await Promise.all([
      galleryDB.delete(galleryId),
      photoDB.deleteByGallery(galleryId),
      syncMetadataDB.get(galleryId).then((metadata) => {
        if (metadata) {
          return syncMetadataDB.put({
            ...metadata,
            last_sync_at: Date.now(),
            updated_at: Date.now(),
          });
        }
      }),
    ]);
  },
};

/**
 * Utility to check if IndexedDB is available
 */
export function isIndexedDBAvailable(): boolean {
  try {
    return typeof indexedDB !== 'undefined';
  } catch {
    return false;
  }
}
