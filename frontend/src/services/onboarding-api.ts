/**
 * Onboarding API Service
 * Handles all API calls to the onboarding microservice
 *
 * T048: Create onboarding API service with registration methods
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
import type {
  RegistrationRequest,
  RegistrationResponse,
  EmailCheckResponse,
  VerificationResponse,
  ResendVerificationResponse,
  OAuthInitResponse,
  OAuthCallbackResponse,
  WorkspaceCreateRequest,
  WorkspaceResponse,
  SlugCheckResponse,
  SlugSuggestResponse,
  OnboardingStateResponse,
  OnboardingStateUpdateRequest,
  ActivationChecklistResponse,
  ApiError,
  LoginRequest,
  LoginResponse,
  RefreshTokenResponse,
} from '../types/onboarding';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1/onboarding';
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

  // Request interceptor - add auth token
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
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

      // Handle 401 - try to refresh token (only once to prevent infinite loop)
      if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshResponse = await axios.post<RefreshTokenResponse>(
            `${API_BASE_URL}/auth/refresh`,
            {},
            { withCredentials: true }
          );

          const { access_token } = refreshResponse.data;
          localStorage.setItem('access_token', access_token);

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        } catch {
          // Refresh failed - clear tokens and redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
      }

      // Transform error for consistent handling
      const apiError: ApiError = error.response?.data || {
        error: 'NetworkError',
        message: error.message || 'An unexpected error occurred',
      };

      return Promise.reject(apiError);
    }
  );

  return client;
}

const apiClient = createApiClient();

// ============================================
// Registration API
// ============================================

/**
 * Register a new user account
 */
export async function register(
  data: RegistrationRequest
): Promise<RegistrationResponse> {
  const response = await apiClient.post<RegistrationResponse>('/register', data);
  return response.data;
}

/**
 * Check if an email is available for registration
 */
export async function checkEmail(email: string): Promise<EmailCheckResponse> {
  const response = await apiClient.get<EmailCheckResponse>('/check-email', {
    params: { email },
  });
  return response.data;
}

// ============================================
// Email Verification API
// ============================================

/**
 * Verify email with token from email link
 */
export async function verifyEmail(token: string): Promise<VerificationResponse> {
  const response = await apiClient.post<VerificationResponse>('/verify-email', {
    token,
  });
  return response.data;
}

/**
 * Resend verification email
 */
export async function resendVerification(
  email: string
): Promise<ResendVerificationResponse> {
  const response = await apiClient.post<ResendVerificationResponse>(
    '/resend-verification',
    { email }
  );
  return response.data;
}

// ============================================
// OAuth API
// ============================================

/**
 * Get Google OAuth authorization URL
 */
export async function getGoogleAuthUrl(): Promise<OAuthInitResponse> {
  const response = await apiClient.get<OAuthInitResponse>('/oauth/google');
  return response.data;
}

/**
 * Handle Google OAuth callback
 */
export async function handleGoogleCallback(
  code: string,
  state: string
): Promise<OAuthCallbackResponse> {
  const response = await apiClient.get<OAuthCallbackResponse>(
    '/oauth/google/callback',
    { params: { code, state } }
  );

  // Store access token
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
  }

  return response.data;
}

// ============================================
// Workspace API
// ============================================

/**
 * Create a new workspace
 */
export async function createWorkspace(
  data: WorkspaceCreateRequest
): Promise<WorkspaceResponse> {
  const response = await apiClient.post<WorkspaceResponse>('/workspace', data);
  return response.data;
}

/**
 * Check if a workspace slug is available
 */
export async function checkSlug(slug: string): Promise<SlugCheckResponse> {
  const response = await apiClient.get<SlugCheckResponse>(
    '/workspace/slug-check',
    { params: { slug } }
  );
  return response.data;
}

/**
 * Get slug suggestions based on workspace name
 */
export async function suggestSlug(name: string): Promise<SlugSuggestResponse> {
  const response = await apiClient.get<SlugSuggestResponse>(
    '/workspace/suggest-slug',
    { params: { name } }
  );
  return response.data;
}

// ============================================
// Onboarding State API
// ============================================

/**
 * Get current onboarding state
 */
export async function getOnboardingState(): Promise<OnboardingStateResponse> {
  const response = await apiClient.get<OnboardingStateResponse>('/state');
  return response.data;
}

/**
 * Update onboarding state
 */
export async function updateOnboardingState(
  data: OnboardingStateUpdateRequest
): Promise<OnboardingStateResponse> {
  const response = await apiClient.patch<OnboardingStateResponse>('/state', data);
  return response.data;
}

/**
 * Reset onboarding state (start over)
 */
export async function resetOnboardingState(): Promise<OnboardingStateResponse> {
  const response = await apiClient.post<OnboardingStateResponse>('/state/reset');
  return response.data;
}

/**
 * Complete onboarding
 */
export async function completeOnboarding(): Promise<OnboardingStateResponse> {
  const response = await apiClient.post<OnboardingStateResponse>('/state/complete');
  return response.data;
}

// ============================================
// Activation Checklist API
// ============================================

/**
 * Get activation checklist
 */
export async function getActivationChecklist(): Promise<ActivationChecklistResponse> {
  const response = await apiClient.get<ActivationChecklistResponse>(
    '/activation-checklist'
  );
  return response.data;
}

/**
 * Mark a checklist item as complete
 */
export async function completeChecklistItem(
  itemId: string
): Promise<ActivationChecklistResponse> {
  const response = await apiClient.post<ActivationChecklistResponse>(
    `/activation-checklist/${itemId}/complete`
  );
  return response.data;
}

// ============================================
// Auth API
// ============================================

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/auth/login', data);

  // Store access token
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
  }

  return response.data;
}

/**
 * Logout - clear tokens
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/auth/logout');
  } finally {
    localStorage.removeItem('access_token');
  }
}

/**
 * Refresh access token
 */
export async function refreshToken(): Promise<RefreshTokenResponse> {
  const response = await apiClient.post<RefreshTokenResponse>('/auth/refresh');

  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
  }

  return response.data;
}

// ============================================
// Export all functions as named exports
// ============================================

export const onboardingApi = {
  // Registration
  register,
  checkEmail,

  // Verification
  verifyEmail,
  resendVerification,

  // OAuth
  getGoogleAuthUrl,
  handleGoogleCallback,

  // Workspace
  createWorkspace,
  checkSlug,
  suggestSlug,

  // Onboarding State
  getOnboardingState,
  updateOnboardingState,
  resetOnboardingState,
  completeOnboarding,

  // Activation Checklist
  getActivationChecklist,
  completeChecklistItem,

  // Auth
  login,
  logout,
  refreshToken,
};

export default onboardingApi;
