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
  expires_in: number;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar_url?: string;
    email_verified: boolean;
  };
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

  // Request interceptor - add auth token
  client.interceptors.request.use(
    (config) => {
      // Get token from memory (will be managed by AuthContext)
      const token = localStorage.getItem('access_token');
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

          // Update token in storage
          localStorage.setItem('access_token', newToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return client(originalRequest);
        } catch (refreshError) {
          // Refresh failed - redirect to login
          localStorage.removeItem('access_token');
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
    const response = await authClient.post<LoginResponse>('/login', request);
    return response.data;
  },

  /**
   * Initiate Google OAuth signin flow
   * Phase 4: User Story 2 - Google OAuth Signin
   */
  async googleSignin(): Promise<{ redirect_url: string }> {
    const response = await authClient.get<{ redirect_url: string }>('/oauth/google/signin');
    return response.data;
  },

  /**
   * Handle Google OAuth callback
   * Phase 4: User Story 2 - Google OAuth Signin
   */
  async googleCallback(code: string, state: string): Promise<LoginResponse> {
    const response = await authClient.get<LoginResponse>('/oauth/google/signin/callback', {
      params: { code, state },
    });
    return response.data;
  },

  /**
   * Refresh access token using refresh token cookie
   * Phase 5: User Story 3 - Session Refresh
   */
  async refreshToken(): Promise<RefreshResponse> {
    const response = await authClient.post<RefreshResponse>('/refresh');
    return response.data;
  },

  /**
   * Logout current session
   * Phase 6: User Story 4 - Logout
   */
  async logout(): Promise<LogoutResponse> {
    const response = await authClient.post<LogoutResponse>('/logout');
    return response.data;
  },

  /**
   * Logout all devices
   * Phase 6: User Story 4 - Logout
   */
  async logoutAll(): Promise<LogoutResponse> {
    const response = await authClient.post<LogoutResponse>('/logout/all');
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
