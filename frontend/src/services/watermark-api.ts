/**
 * Watermark API Service
 * Handles all API calls to the gallery-service watermark endpoints
 *
 * T003: Create watermark API service with configuration and batch operations
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
// SECURITY: Import secure token management (never localStorage)
import { setTokenInMemory, getTokenFromMemory } from './authService';
import type {
  WatermarkConfig,
  WatermarkConfigResponse,
  WatermarkPreviewRequest,
  WatermarkPreviewResponse,
  WatermarkApplyResponse,
  WatermarkStatusResponse,
  ApiError,
} from '../types/watermark';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_GALLERY_API_URL || '/api/v1/gallery';
const TIMEOUT_MS = 30000;

/**
 * Create axios instance with default configuration
 */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: TIMEOUT_MS,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true, // For cookies (refresh token)
  });

  // Request interceptor - add auth token from MEMORY (not localStorage)
  client.interceptors.request.use(
    (config) => {
      // SECURITY: Get token from module memory, NOT localStorage
      const token = getTokenFromMemory();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - handle errors and token refresh
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<ApiError>) => {
      const originalRequest = error.config as typeof error.config & { _retry?: boolean };
      const requestUrl = originalRequest?.url || '';

      // Don't try to refresh token for auth endpoints
      const isAuthEndpoint = requestUrl.includes('/auth/');

      // Handle 401 - try to refresh token (only once to prevent infinite loop)
      if (error.response?.status === 401 &&
          originalRequest &&
          !originalRequest._retry &&
          !isAuthEndpoint) {
        originalRequest._retry = true;

        try {
          // Use onboarding service refresh endpoint (shared auth)
          const refreshResponse = await axios.post(
            `${import.meta.env.VITE_API_URL || '/api/v1/onboarding'}/auth/refresh`,
            {},
            { withCredentials: true }
          );

          const { access_token } = refreshResponse.data;
          // SECURITY: Store token in memory, NOT localStorage
          setTokenInMemory(access_token);

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        } catch {
          // Refresh failed - clear memory and redirect to sign-in
          setTokenInMemory(null);
          window.location.href = '/sign-in';
          return Promise.reject(error);
        }
      }

      // Transform error for consistent handling
      const responseData = error.response?.data;

      // Handle FastAPI's detail field (can be string or object)
      let apiError: ApiError;

      if (responseData) {
        if (typeof responseData.detail === 'object' && responseData.detail !== null) {
          // Backend returns { detail: { error: "...", message: "..." } }
          apiError = {
            error: responseData.detail.error || 'UnknownError',
            message: responseData.detail.message || 'An unexpected error occurred',
          };
        } else if (typeof responseData.detail === 'string') {
          // Backend returns { detail: "Error message" }
          apiError = {
            error: 'UnknownError',
            message: responseData.detail,
          };
        } else if (responseData.error && responseData.message) {
          // Backend already returns correct format
          apiError = responseData as ApiError;
        } else {
          // Fallback
          apiError = {
            error: 'UnknownError',
            message: responseData.message || JSON.stringify(responseData),
          };
        }
      } else {
        // Network error or no response
        apiError = {
          error: 'NetworkError',
          message: error.message || 'Network error occurred. Please check your connection.',
        };
      }

      return Promise.reject(apiError);
    }
  );

  return client;
}

const apiClient = createApiClient();

// ============================================
// Watermark Configuration API
// ============================================

/**
 * Get watermark configuration for a gallery
 */
export async function getWatermarkConfig(
  galleryId: string,
  workspaceId: string
): Promise<WatermarkConfigResponse> {
  const response = await apiClient.get<WatermarkConfigResponse>(
    `/watermark/galleries/${galleryId}/config`,
    {
      params: { workspace_id: workspaceId },
    }
  );
  return response.data;
}

/**
 * Update watermark configuration for a gallery
 */
export async function updateWatermarkConfig(
  galleryId: string,
  workspaceId: string,
  config: WatermarkConfig
): Promise<WatermarkConfigResponse> {
  const response = await apiClient.put<WatermarkConfigResponse>(
    `/watermark/galleries/${galleryId}/config`,
    config,
    {
      params: { workspace_id: workspaceId },
    }
  );
  return response.data;
}

/**
 * Enable watermark for a gallery
 */
export async function enableWatermark(
  galleryId: string,
  workspaceId: string
): Promise<WatermarkConfigResponse> {
  const response = await apiClient.post<WatermarkConfigResponse>(
    `/watermark/galleries/${galleryId}/enable`,
    {},
    {
      params: { workspace_id: workspaceId },
    }
  );
  return response.data;
}

/**
 * Disable watermark for a gallery
 */
export async function disableWatermark(
  galleryId: string,
  workspaceId: string
): Promise<WatermarkConfigResponse> {
  const response = await apiClient.post<WatermarkConfigResponse>(
    `/watermark/galleries/${galleryId}/disable`,
    {},
    {
      params: { workspace_id: workspaceId },
    }
  );
  return response.data;
}

// ============================================
// Watermark Preview & Apply API
// ============================================

/**
 * Generate a preview of watermark on a single asset
 */
export async function previewWatermark(
  galleryId: string,
  workspaceId: string,
  previewRequest: WatermarkPreviewRequest
): Promise<WatermarkPreviewResponse> {
  const response = await apiClient.post<WatermarkPreviewResponse>(
    `/watermark/galleries/${galleryId}/preview`,
    previewRequest,
    {
      params: { workspace_id: workspaceId },
    }
  );
  return response.data;
}

/**
 * Batch apply watermark to all assets in a gallery
 */
export async function applyWatermark(
  galleryId: string,
  workspaceId: string
): Promise<WatermarkApplyResponse> {
  const response = await apiClient.post<WatermarkApplyResponse>(
    `/watermark/galleries/${galleryId}/apply`,
    {},
    {
      params: { workspace_id: workspaceId },
    }
  );
  return response.data;
}

/**
 * Get status of batch watermark operation
 */
export async function getWatermarkStatus(
  galleryId: string,
  workspaceId: string,
  jobId: string
): Promise<WatermarkStatusResponse> {
  const response = await apiClient.get<WatermarkStatusResponse>(
    `/watermark/galleries/${galleryId}/status`,
    {
      params: {
        workspace_id: workspaceId,
        job_id: jobId,
      },
    }
  );
  return response.data;
}

// ============================================
// Health Check API
// ============================================

/**
 * Check watermark API health
 */
export async function checkWatermarkHealth(): Promise<{ status: string; api: string }> {
  const response = await apiClient.get<{ status: string; api: string }>(
    '/watermark/health'
  );
  return response.data;
}
