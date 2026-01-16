/**
 * Export API Service
 * Handles all API calls to the export microservice
 *
 * Subtask-4-1: Create export API service client
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
// SECURITY: Import secure token management (never localStorage)
import { setTokenInMemory, getTokenFromMemory } from './authService';

// ============================================
// Export Types (based on export-service schemas)
// ============================================

export type ExportType = 'workspace' | 'gallery' | 'selection';

export type ExportStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface ExportOptions {
  include_metadata?: boolean;
  include_thumbnails?: boolean;
  gallery_ids?: string[];
  asset_ids?: string[];
}

export interface ExportCreateRequest {
  export_type: ExportType;
  options?: ExportOptions;
}

export interface ExportResponse {
  id: string;
  workspace_id: string;
  user_id: string;
  export_type: ExportType;
  status: ExportStatus;
  options?: ExportOptions;
  total_assets: number;
  processed_assets: number;
  progress_percentage: number;
  file_url?: string;
  file_size?: number;
  file_key?: string;
  error_message?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ExportListResponse {
  jobs: ExportResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  error: string;
  message: string;
}

// ============================================
// API Configuration
// ============================================

const API_BASE_URL = import.meta.env.VITE_EXPORT_API_URL || '/api/v1/export';
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

      // Don't try to refresh token for export endpoints that expect 401
      const isAuthEndpoint = false; // Export service doesn't have auth endpoints

      // Handle 401 - try to refresh token (only once to prevent infinite loop)
      if (error.response?.status === 401 &&
          originalRequest &&
          !originalRequest._retry &&
          !isAuthEndpoint) {
        originalRequest._retry = true;

        try {
          // Use onboarding service for token refresh
          const refreshResponse = await axios.post<{ access_token: string }>(
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
// Export API Functions
// ============================================

/**
 * Create a new export job
 *
 * @param data Export request with type and options
 * @returns Export job details
 * @throws {ApiError} If validation fails or concurrent limit exceeded
 */
export async function createExportJob(
  data: ExportCreateRequest
): Promise<ExportResponse> {
  const response = await apiClient.post<ExportResponse>('/jobs', data);
  return response.data;
}

/**
 * List export jobs for current workspace
 *
 * @param params Optional filters (status, page, page_size)
 * @returns Paginated list of export jobs
 */
export async function listExportJobs(params?: {
  status?: ExportStatus;
  page?: number;
  page_size?: number;
}): Promise<ExportListResponse> {
  const response = await apiClient.get<ExportListResponse>('/jobs', {
    params: {
      status_filter: params?.status,
      page: params?.page,
      page_size: params?.page_size,
    },
  });
  return response.data;
}

/**
 * Get export job status and progress
 *
 * @param jobId Export job UUID
 * @returns Export job details with current status
 * @throws {ApiError} If job not found or permission denied
 */
export async function getExportJobStatus(
  jobId: string
): Promise<ExportResponse> {
  const response = await apiClient.get<ExportResponse>(`/jobs/${jobId}`);
  return response.data;
}

/**
 * Cancel a pending or processing export job
 *
 * @param jobId Export job UUID
 * @throws {ApiError} If job not found, permission denied, or cannot be cancelled
 */
export async function cancelExportJob(jobId: string): Promise<void> {
  await apiClient.delete(`/jobs/${jobId}`);
}

// ============================================
// Helper Functions
// ============================================

/**
 * Format file size in bytes to human-readable string
 *
 * @param bytes File size in bytes
 * @returns Formatted string (e.g., "1.5 GB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
}

/**
 * Check if export job is in a terminal state
 *
 * @param status Export job status
 * @returns True if job is completed, failed, or cancelled
 */
export function isExportComplete(status: ExportStatus): boolean {
  return ['completed', 'failed', 'cancelled'].includes(status);
}

/**
 * Check if export job is actively processing
 *
 * @param status Export job status
 * @returns True if job is pending or processing
 */
export function isExportActive(status: ExportStatus): boolean {
  return ['pending', 'processing'].includes(status);
}

/**
 * Get status display text for UI
 *
 * @param status Export job status
 * @returns User-friendly status text
 */
export function getStatusDisplayText(status: ExportStatus): string {
  const statusMap: Record<ExportStatus, string> = {
    pending: 'Queued',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
    cancelled: 'Cancelled',
  };

  return statusMap[status] || status;
}

/**
 * Estimate remaining time based on progress
 *
 * @param job Export job with progress data
 * @param startTime Job start timestamp
 * @returns Estimated seconds remaining, or null if cannot estimate
 */
export function estimateTimeRemaining(
  job: ExportResponse,
  startTime?: Date
): number | null {
  if (!startTime || job.progress_percentage === 0) {
    return null;
  }

  const now = new Date();
  const elapsedMs = now.getTime() - startTime.getTime();
  const elapsedSec = elapsedMs / 1000;

  const percentComplete = job.progress_percentage / 100;
  const percentRemaining = 1 - percentComplete;

  if (percentComplete === 0) {
    return null;
  }

  const estimatedTotalSec = elapsedSec / percentComplete;
  const remainingSec = estimatedTotalSec * percentRemaining;

  return Math.round(remainingSec);
}

/**
 * Format seconds to human-readable duration
 *
 * @param seconds Duration in seconds
 * @returns Formatted string (e.g., "5m 30s")
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return `${hours}h ${remainingMinutes}m`;
}
