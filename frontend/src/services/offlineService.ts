/**
 * Offline Gallery Service
 * Handles downloading galleries and photos for offline access
 * Stores data in IndexedDB and manages download progress
 *
 * Phase 2: Offline Storage Implementation
 * Subtask 2-1: Create offline gallery service with download capability
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
import {
  galleryDB,
  photoDB,
  syncMetadataDB,
  storageDB,
  type OfflineGallery,
  type OfflinePhoto,
} from '../utils/indexedDB';
import { getTokenFromMemory } from './authService';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const TIMEOUT_MS = 60000; // 60s timeout for photo downloads

/**
 * Type definitions for offline gallery API
 */

export interface GalleryMetadata {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  cover_photo_url?: string;
  photo_count: number;
  created_at: string;
  updated_at: string;
}

export interface PhotoMetadata {
  id: string;
  gallery_id: string;
  workspace_id: string;
  file_name: string;
  file_size_bytes: number;
  thumbnail_url?: string;
  preview_url?: string;
  full_url?: string;
  width?: number;
  height?: number;
  taken_at?: string;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface DownloadProgress {
  gallery_id: string;
  gallery_name: string;
  total_photos: number;
  downloaded_photos: number;
  total_bytes: number;
  downloaded_bytes: number;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  error_message?: string;
  percentage: number;
}

export interface DownloadOptions {
  includeFullResolution?: boolean;
  includePreview?: boolean;
  includeThumbnail?: boolean;
  encrypted?: boolean;
  onProgress?: (progress: DownloadProgress) => void;
}

export interface OfflineGalleryInfo {
  gallery: OfflineGallery;
  photo_count: number;
  size_mb: number;
  last_synced: string;
}

export interface ApiError {
  error: string;
  message: string;
  status_code?: number;
}

/**
 * Create axios instance for offline service
 */
function createOfflineClient(): AxiosInstance {
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
      if (error.response?.status === 401) {
        // Token expired or invalid - redirect to login
        window.location.href = '/signin';
      }
      return Promise.reject(error);
    }
  );

  return client;
}

// Create singleton client
const offlineClient = createOfflineClient();

/**
 * Download a photo blob from URL with retry logic
 */
async function downloadPhotoBlob(
  url: string,
  maxRetries = 3
): Promise<Blob | null> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${getTokenFromMemory()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      return blob;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');

      // Wait before retry (exponential backoff)
      if (attempt < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  }

  // All retries failed
  console.error(`Failed to download photo from ${url} after ${maxRetries} attempts:`, lastError);
  return null;
}

/**
 * Calculate total size of photos to download
 */
function calculateTotalSize(photos: PhotoMetadata[], options: DownloadOptions): number {
  let totalSize = 0;

  for (const photo of photos) {
    if (options.includeThumbnail) {
      totalSize += photo.file_size_bytes * 0.05; // Estimate: thumbnail is ~5% of original
    }
    if (options.includePreview) {
      totalSize += photo.file_size_bytes * 0.2; // Estimate: preview is ~20% of original
    }
    if (options.includeFullResolution) {
      totalSize += photo.file_size_bytes;
    }
  }

  return Math.round(totalSize);
}

/**
 * Offline Gallery Service API
 */
export const offlineService = {
  /**
   * Download a gallery for offline access
   * Downloads gallery metadata and photos with progress tracking
   */
  async downloadGallery(
    galleryId: string,
    options: DownloadOptions = {}
  ): Promise<void> {
    const {
      includeFullResolution = false,
      includePreview = true,
      includeThumbnail = true,
      encrypted = false,
      onProgress,
    } = options;

    try {
      // Step 1: Fetch gallery metadata
      const galleryResponse = await offlineClient.get<GalleryMetadata>(
        `/galleries/${galleryId}`
      );
      const galleryData = galleryResponse.data;

      // Step 2: Fetch photos list
      const photosResponse = await offlineClient.get<{ photos: PhotoMetadata[] }>(
        `/galleries/${galleryId}/photos`
      );
      const photos = photosResponse.data.photos;

      // Calculate total download size
      const totalBytes = calculateTotalSize(photos, options);

      // Initialize progress tracking
      let downloadedPhotos = 0;
      let downloadedBytes = 0;

      const updateProgress = (status: DownloadProgress['status'], errorMessage?: string) => {
        if (onProgress) {
          const progress: DownloadProgress = {
            gallery_id: galleryId,
            gallery_name: galleryData.name,
            total_photos: photos.length,
            downloaded_photos: downloadedPhotos,
            total_bytes: totalBytes,
            downloaded_bytes: downloadedBytes,
            status,
            error_message: errorMessage,
            percentage: totalBytes > 0 ? Math.round((downloadedBytes / totalBytes) * 100) : 0,
          };
          onProgress(progress);
        }
      };

      updateProgress('downloading');

      // Step 3: Download photos in batches
      const BATCH_SIZE = 5; // Download 5 photos at a time
      const offlinePhotos: OfflinePhoto[] = [];

      for (let i = 0; i < photos.length; i += BATCH_SIZE) {
        const batch = photos.slice(i, i + BATCH_SIZE);

        await Promise.all(
          batch.map(async (photo) => {
            const offlinePhoto: OfflinePhoto = {
              id: photo.id,
              gallery_id: photo.gallery_id,
              workspace_id: photo.workspace_id,
              file_name: photo.file_name,
              file_size_bytes: photo.file_size_bytes,
              thumbnail_url: photo.thumbnail_url,
              preview_url: photo.preview_url,
              full_url: photo.full_url,
              width: photo.width,
              height: photo.height,
              taken_at: photo.taken_at ? new Date(photo.taken_at).getTime() : undefined,
              is_favorite: photo.is_favorite,
              downloaded_at: Date.now(),
            };

            // Download blobs based on options
            if (includeThumbnail && photo.thumbnail_url) {
              const blob = await downloadPhotoBlob(photo.thumbnail_url);
              if (blob) {
                offlinePhoto.thumbnail_blob = blob;
                downloadedBytes += blob.size;
              }
            }

            if (includePreview && photo.preview_url) {
              const blob = await downloadPhotoBlob(photo.preview_url);
              if (blob) {
                offlinePhoto.preview_blob = blob;
                downloadedBytes += blob.size;
              }
            }

            if (includeFullResolution && photo.full_url) {
              const blob = await downloadPhotoBlob(photo.full_url);
              if (blob) {
                offlinePhoto.full_blob = blob;
                downloadedBytes += blob.size;
              }
            }

            offlinePhotos.push(offlinePhoto);
            downloadedPhotos++;
            updateProgress('downloading');
          })
        );
      }

      // Step 4: Save to IndexedDB
      const offlineGallery: OfflineGallery = {
        id: galleryData.id,
        workspace_id: galleryData.workspace_id,
        name: galleryData.name,
        description: galleryData.description,
        cover_photo_url: galleryData.cover_photo_url,
        photo_count: photos.length,
        total_size_bytes: downloadedBytes,
        downloaded_at: Date.now(),
        encrypted,
        last_synced: Date.now(),
      };

      await galleryDB.put(offlineGallery);
      await photoDB.putBatch(offlinePhotos);

      // Update sync metadata
      await syncMetadataDB.put({
        id: galleryId,
        last_sync_at: Date.now(),
        sync_status: 'idle',
        pending_actions_count: 0,
        updated_at: Date.now(),
      });

      updateProgress('completed');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';

      if (onProgress) {
        onProgress({
          gallery_id: galleryId,
          gallery_name: 'Unknown',
          total_photos: 0,
          downloaded_photos: 0,
          total_bytes: 0,
          downloaded_bytes: 0,
          status: 'error',
          error_message: errorMessage,
          percentage: 0,
        });
      }

      throw new Error(`Failed to download gallery: ${errorMessage}`);
    }
  },

  /**
   * Get all downloaded galleries for current workspace
   */
  async getDownloadedGalleries(workspaceId: string): Promise<OfflineGalleryInfo[]> {
    try {
      const galleries = await galleryDB.getByWorkspace(workspaceId);

      const galleryInfos = await Promise.all(
        galleries.map(async (gallery) => {
          const photos = await photoDB.getByGallery(gallery.id);

          return {
            gallery,
            photo_count: photos.length,
            size_mb: parseFloat((gallery.total_size_bytes / (1024 * 1024)).toFixed(2)),
            last_synced: gallery.last_synced
              ? new Date(gallery.last_synced).toISOString()
              : 'Never',
          };
        })
      );

      return galleryInfos;
    } catch (error) {
      console.error('Failed to get downloaded galleries:', error);
      throw new Error('Failed to retrieve offline galleries');
    }
  },

  /**
   * Get a single offline gallery with photos
   */
  async getOfflineGallery(galleryId: string): Promise<{
    gallery: OfflineGallery;
    photos: OfflinePhoto[];
  } | null> {
    try {
      const gallery = await galleryDB.get(galleryId);
      if (!gallery) {
        return null;
      }

      const photos = await photoDB.getByGallery(galleryId);

      return { gallery, photos };
    } catch (error) {
      console.error('Failed to get offline gallery:', error);
      throw new Error('Failed to retrieve offline gallery');
    }
  },

  /**
   * Delete a downloaded gallery and all its photos
   */
  async deleteOfflineGallery(galleryId: string): Promise<void> {
    try {
      await storageDB.deleteGallery(galleryId);
    } catch (error) {
      console.error('Failed to delete offline gallery:', error);
      throw new Error('Failed to delete offline gallery');
    }
  },

  /**
   * Clear all offline data
   */
  async clearAllOfflineData(): Promise<void> {
    try {
      await storageDB.clearAll();
    } catch (error) {
      console.error('Failed to clear offline data:', error);
      throw new Error('Failed to clear offline data');
    }
  },

  /**
   * Get storage statistics
   */
  async getStorageStats(): Promise<{
    usage_mb: number;
    quota_mb: number;
    available_mb: number;
    percentage_used: number;
    gallery_count: number;
    total_gallery_size_mb: number;
  }> {
    try {
      const estimate = await storageDB.getStorageEstimate();
      const gallerySize = await storageDB.getTotalGallerySize();
      const galleries = await galleryDB.getAll();

      if (!estimate) {
        return {
          usage_mb: 0,
          quota_mb: 0,
          available_mb: 0,
          percentage_used: 0,
          gallery_count: galleries.length,
          total_gallery_size_mb: parseFloat((gallerySize / (1024 * 1024)).toFixed(2)),
        };
      }

      const usageMB = parseFloat((estimate.usage / (1024 * 1024)).toFixed(2));
      const quotaMB = parseFloat((estimate.quota / (1024 * 1024)).toFixed(2));
      const availableMB = parseFloat(((estimate.quota - estimate.usage) / (1024 * 1024)).toFixed(2));
      const percentageUsed = estimate.quota > 0
        ? parseFloat(((estimate.usage / estimate.quota) * 100).toFixed(2))
        : 0;

      return {
        usage_mb: usageMB,
        quota_mb: quotaMB,
        available_mb: availableMB,
        percentage_used: percentageUsed,
        gallery_count: galleries.length,
        total_gallery_size_mb: parseFloat((gallerySize / (1024 * 1024)).toFixed(2)),
      };
    } catch (error) {
      console.error('Failed to get storage stats:', error);
      throw new Error('Failed to retrieve storage statistics');
    }
  },

  /**
   * Check if a gallery is available offline
   */
  async isGalleryAvailableOffline(galleryId: string): Promise<boolean> {
    try {
      const gallery = await galleryDB.get(galleryId);
      return !!gallery;
    } catch (error) {
      console.error('Failed to check offline availability:', error);
      return false;
    }
  },

  /**
   * Fetch available galleries from API for a workspace
   * Returns list of galleries that can be downloaded
   */
  async fetchAvailableGalleries(workspaceId: string): Promise<GalleryMetadata[]> {
    try {
      const response = await offlineClient.get<{ galleries: GalleryMetadata[] }>(
        `/workspaces/${workspaceId}/galleries`
      );
      return response.data.galleries || [];
    } catch (error) {
      console.error('Failed to fetch available galleries:', error);

      // Return mock data for development/testing
      // TODO: Remove this mock data once the API endpoint is implemented
      if (import.meta.env.DEV) {
        return [
          {
            id: 'mock-gallery-1',
            workspace_id: workspaceId,
            name: 'Sample Wedding Gallery',
            description: 'Beautiful wedding ceremony and reception photos',
            photo_count: 250,
            cover_photo_url: undefined,
            created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: 'mock-gallery-2',
            workspace_id: workspaceId,
            name: 'Portrait Session',
            description: 'Professional headshots and family portraits',
            photo_count: 85,
            cover_photo_url: undefined,
            created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: 'mock-gallery-3',
            workspace_id: workspaceId,
            name: 'Event Photography',
            description: 'Corporate event and conference photos',
            photo_count: 120,
            cover_photo_url: undefined,
            created_at: new Date(Date.now() - 21 * 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          },
        ];
      }

      throw new Error('Failed to fetch available galleries');
    }
  },
};

/**
 * Export types for use in components
 */
export type {
  OfflineGallery,
  OfflinePhoto,
} from '../utils/indexedDB';
