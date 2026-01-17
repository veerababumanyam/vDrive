/**
 * Authentication API Service
 * Handles all API calls for authentication (signin, logout, token refresh)
 *
 * T013: Create authService.ts API client
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1/onboarding';
const TIMEOUT_MS = 30000;

/**
 * Type definitions for auth API
 * These will be expanded in Phase 3-6 as we implement each user story
 */

export interface LoginRequest {
  email: string;
  password: string;
  turnstile_token?: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  full_name: string;
  email_verified: boolean;
  has_workspace: boolean;
  workspace_id?: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LogoutResponse {
  message: string;
}

export interface ApiError {
  error: string;
  message: string;
  status_code?: number;
}

/**
 * SECURITY: In-memory token storage (never localStorage)
 * This module-level variable is only accessible within JavaScript runtime
 * Protected from XSS attacks that target localStorage
 */
let memoryAccessToken: string | null = null;

/**
 * Set access token in memory (called by AuthContext)
 * @internal - Only for use by AuthContext
 */
export function setTokenInMemory(token: string | null): void {
  // DEBUG: Log when token is set
  console.log('[Auth] setTokenInMemory called:', token ? `token set (${token.substring(0, 20)}...)` : 'token cleared');
  memoryAccessToken = token;
}

/**
 * Get access token from memory
 * @internal - Only for use by axios interceptors
 */
export function getTokenFromMemory(): string | null {
  return memoryAccessToken;
}

/**
 * Create axios instance with default configuration
 */
function createAuthClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: TIMEOUT_MS,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true, // For HttpOnly refresh token cookie
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

  // Response interceptor - handle errors
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<ApiError>) => {
      const originalRequest = error.config as typeof error.config & { _retry?: boolean };
      const requestUrl = originalRequest?.url || '';

      // Don't try to refresh token for login/refresh endpoints
      const isAuthEndpoint = requestUrl.includes('/login') || requestUrl.includes('/refresh');

      // Handle 401 - try to refresh token (only once to prevent infinite loop)
      if (
        error.response?.status === 401 &&
        originalRequest &&
        !originalRequest._retry &&
        !isAuthEndpoint
      ) {
        originalRequest._retry = true;

        try {
          // Attempt token refresh
          const refreshResponse = await authApi.refreshToken();
          const newToken = refreshResponse.access_token;

          // SECURITY: Update token in memory (not localStorage)
          setTokenInMemory(newToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return client(originalRequest);
        } catch (refreshError) {
          // Refresh failed - clear memory and redirect to login
          setTokenInMemory(null);
          window.location.href = '/signin';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
}

// Create singleton client
const authClient = createAuthClient();

/**
 * Authentication API methods
 */
export const authApi = {
  /**
   * Login with email and password
   * Phase 3: User Story 1 - Email/Password Signin
   */
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await authClient.post<LoginResponse>('/auth/login', request);
    return response.data;
  },

  /**
   * Initiate Google OAuth signin flow
   * Phase 4: User Story 2 - Google OAuth Signin
   */
  async googleSignin(): Promise<{ redirect_url: string }> {
    const response = await authClient.get<{ redirect_url: string }>('/oauth/google');
    return response.data;
  },

  /**
   * Handle Google OAuth callback
   * Phase 4: User Story 2 - Google OAuth Signin
   */
  async googleCallback(code: string, state: string): Promise<LoginResponse> {
    const response = await authClient.get<LoginResponse>('/oauth/google/callback', {
      params: { code, state },
    });
    return response.data;
  },

  /**
   * Refresh access token using refresh token cookie
   * Phase 5: User Story 3 - Session Refresh
   */
  async refreshToken(): Promise<RefreshResponse> {
    const response = await authClient.post<RefreshResponse>('/auth/refresh');
    return response.data;
  },

  /**
   * Logout current session
   * Phase 6: User Story 4 - Logout
   */
  async logout(): Promise<LogoutResponse> {
    const response = await authClient.post<LogoutResponse>('/auth/logout');
    return response.data;
  },

  /**
   * Logout all devices
   * Phase 6: User Story 4 - Logout
   */
  async logoutAll(): Promise<LogoutResponse> {
    const response = await authClient.post<LogoutResponse>('/auth/logout/all');
    return response.data;
  },
};

/**
 * Error handling helper
 */
export function handleAuthError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError;
    return apiError?.message || error.message || 'An error occurred during authentication';
  }
  return 'An unexpected error occurred';
}
