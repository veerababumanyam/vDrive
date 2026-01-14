/**
 * Onboarding API Types
 * Based on services/onboarding-service Pydantic schemas
 */

// ============================================
// Registration Types
// ============================================

export interface RegistrationRequest {
  email: string;
  password: string;
  full_name: string;
  turnstile_token: string;
}

export interface RegistrationResponse {
  user_id: string;
  email: string;
  full_name: string;
  email_verified: boolean;
  message: string;
}

export interface EmailCheckRequest {
  email: string;
}

export interface EmailCheckResponse {
  available: boolean;
  message: string;
}

// ============================================
// Verification Types
// ============================================

export interface VerificationRequest {
  token: string;
}

export interface VerificationResponse {
  success: boolean;
  message: string;
  user_id?: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface ResendVerificationResponse {
  success: boolean;
  message: string;
}

// ============================================
// OAuth Types
// ============================================

export interface OAuthInitResponse {
  authorization_url: string;
  state: string;
}

export interface OAuthCallbackResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
  is_new_user: boolean;
}

// ============================================
// User Types
// ============================================

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  email_verified: boolean;
  google_id?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

// ============================================
// Workspace Types
// ============================================

export type BusinessType =
  | 'wedding'
  | 'portrait'
  | 'commercial'
  | 'event'
  | 'family'
  | 'newborn'
  | 'real_estate'
  | 'product'
  | 'other';

export interface WorkspaceCreateRequest {
  name: string;
  slug: string;
  business_type: BusinessType;
}

export interface WorkspaceResponse {
  id: string;
  name: string;
  slug: string;
  business_type: BusinessType;
  owner_id: string;
  settings: Record<string, unknown>;
  trial_ends_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SlugCheckRequest {
  slug: string;
}

export interface SlugCheckResponse {
  available: boolean;
  message: string;
  suggestions?: string[];
}

export interface SlugSuggestRequest {
  name: string;
}

export interface SlugSuggestResponse {
  suggestions: string[];
}

// ============================================
// Onboarding State Types
// ============================================

export type OnboardingStep =
  | 'registration'
  | 'email_verification'
  | 'workspace_setup'
  | 'profile_setup'
  | 'completed';

export interface OnboardingStateResponse {
  user_id: string;
  current_step: OnboardingStep;
  completed_steps: OnboardingStep[];
  workspace_data?: Partial<WorkspaceCreateRequest>;
  activation_checklist?: ActivationChecklistItem[];
  started_at: string;
  updated_at: string;
}

export interface OnboardingStateUpdateRequest {
  current_step?: OnboardingStep;
  completed_steps?: OnboardingStep[];
  workspace_data?: Partial<WorkspaceCreateRequest>;
}

// ============================================
// Activation Checklist Types
// ============================================

export interface ActivationChecklistItem {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  completed_at?: string;
  action_url?: string;
}

export interface ActivationChecklistResponse {
  items: ActivationChecklistItem[];
  total_items: number;
  completed_items: number;
  progress_percentage: number;
}

// ============================================
// Error Types
// ============================================

export interface ApiErrorDetail {
  field: string;
  message: string;
  code: string;
}

export interface ApiError {
  error: string;
  message: string;
  details?: ApiErrorDetail[];
  request_id?: string;
}

// ============================================
// Auth Types
// ============================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
