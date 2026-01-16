/**
 * Migration API Service
 * Handles all API calls to the migration microservice
 *
 * Subtask-5-4: Create migration wizard UI component
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
import { setTokenInMemory, getTokenFromMemory } from './authService';

// ============================================
// Migration Types
// ============================================

export type MigrationPlatform = 'pixieset' | 'pictime' | 'shootproof' | 'zenfolio' | 'smugmug';

export type MigrationStatus = 'pending' | 'authenticating' | 'scanning' | 'importing' | 'completed' | 'failed' | 'cancelled';

export interface MigrationCredentials {
  platform: MigrationPlatform;
  api_key?: string;
  api_secret?: string;
  username?: string;
  password?: string;
  access_token?: string;
}

export interface MigrationCreateRequest {
  credentials: MigrationCredentials;
  options?: {
    include_metadata?: boolean;
    preserve_structure?: boolean;
    gallery_ids?: string[];
  };
}

export interface MigrationResponse {
  id: string;
  workspace_id: string;
  user_id: string;
  platform: MigrationPlatform;
  status: MigrationStatus;
  total_galleries: number;
  imported_galleries: number;
  total_assets: number;
  imported_assets: number;
  progress_percentage: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface MigrationListResponse {
  migrations: MigrationResponse[];
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

const API_BASE_URL = import.meta.env.VITE_MIGRATION_API_URL || '/api/v1/migration';
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
    withCredentials: true,
  });

  // Request interceptor - add auth token from MEMORY
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

  // Response interceptor - handle errors and token refresh
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<ApiError>) => {
      const originalRequest = error.config as typeof error.config & { _retry?: boolean };

      // Handle 401 - try to refresh token
      if (error.response?.status === 401 &&
          originalRequest &&
          !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshResponse = await axios.post<{ access_token: string }>(
            `${import.meta.env.VITE_API_URL || '/api/v1/onboarding'}/auth/refresh`,
            {},
            { withCredentials: true }
          );

          const { access_token } = refreshResponse.data;
          setTokenInMemory(access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        } catch {
          setTokenInMemory(null);
          window.location.href = '/sign-in';
          return Promise.reject(error);
        }
      }

      // Transform error for consistent handling
      const responseData = error.response?.data;
      let apiError: ApiError;

      if (responseData) {
        if (typeof responseData.detail === 'object' && responseData.detail !== null) {
          apiError = {
            error: responseData.detail.error || 'UnknownError',
            message: responseData.detail.message || 'An unexpected error occurred',
          };
        } else if (typeof responseData.detail === 'string') {
          apiError = {
            error: 'UnknownError',
            message: responseData.detail,
          };
        } else if (responseData.error && responseData.message) {
          apiError = responseData as ApiError;
        } else {
          apiError = {
            error: 'UnknownError',
            message: responseData.message || JSON.stringify(responseData),
          };
        }
      } else {
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
// Migration API Functions
// ============================================

/**
 * Create a new migration job
 */
export async function createMigrationJob(
  data: MigrationCreateRequest
): Promise<MigrationResponse> {
  const response = await apiClient.post<MigrationResponse>('/jobs', data);
  return response.data;
}

/**
 * List migration jobs for current workspace
 */
export async function listMigrationJobs(params?: {
  status?: MigrationStatus;
  page?: number;
  page_size?: number;
}): Promise<MigrationListResponse> {
  const response = await apiClient.get<MigrationListResponse>('/jobs', {
    params: {
      status_filter: params?.status,
      page: params?.page,
      page_size: params?.page_size,
    },
  });
  return response.data;
}

/**
 * Get migration job status and progress
 */
export async function getMigrationJobStatus(
  jobId: string
): Promise<MigrationResponse> {
  const response = await apiClient.get<MigrationResponse>(`/jobs/${jobId}`);
  return response.data;
}

/**
 * Cancel a pending or processing migration job
 */
export async function cancelMigrationJob(jobId: string): Promise<void> {
  await apiClient.delete(`/jobs/${jobId}`);
}

// ============================================
// Helper Functions
// ============================================

/**
 * Get platform display name
 */
export function getPlatformDisplayName(platform: MigrationPlatform): string {
  const platformMap: Record<MigrationPlatform, string> = {
    pixieset: 'Pixieset',
    pictime: 'Pic-Time',
    shootproof: 'ShootProof',
    zenfolio: 'Zenfolio',
    smugmug: 'SmugMug',
  };
  return platformMap[platform] || platform;
}

/**
 * Get status display text for UI
 */
export function getStatusDisplayText(status: MigrationStatus): string {
  const statusMap: Record<MigrationStatus, string> = {
    pending: 'Queued',
    authenticating: 'Authenticating',
    scanning: 'Scanning Galleries',
    importing: 'Importing',
    completed: 'Completed',
    failed: 'Failed',
    cancelled: 'Cancelled',
  };
  return statusMap[status] || status;
}

/**
 * Check if migration job is in a terminal state
 */
export function isMigrationComplete(status: MigrationStatus): boolean {
  return ['completed', 'failed', 'cancelled'].includes(status);
}

/**
 * Check if migration job is actively processing
 */
export function isMigrationActive(status: MigrationStatus): boolean {
  return ['pending', 'authenticating', 'scanning', 'importing'].includes(status);
}
