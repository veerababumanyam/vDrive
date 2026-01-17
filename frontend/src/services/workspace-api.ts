/**
 * Workspace API Service
 * Handles workspace-related API calls
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
import { getTokenFromMemory } from './authService';
import type { Workspace, WorkspaceRole } from '../types/workspace';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1/onboarding';
const TIMEOUT_MS = 30000;

// ============================================================================
// API TYPES
// ============================================================================

export interface WorkspaceMemberResponse {
  id: string;
  workspace_id: string;
  user_id: string;
  role: WorkspaceRole;
  invited_by?: string;
  joined_at: string;
}

export interface WorkspaceListResponse {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  business_type: string;
  subscription_tier: 'trial' | 'free' | 'pro' | 'business' | 'enterprise';
  trial_ends_at?: string;
  created_at: string;
  updated_at: string;
  member_role: WorkspaceRole;
  logo_url?: string;
}

export interface WorkspaceSwitchRequest {
  workspace_id: string;
}

export interface WorkspaceSwitchResponse {
  success: boolean;
  workspace: WorkspaceListResponse;
  access_token?: string;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// API CLIENT
// ============================================================================

/**
 * Create axios instance for workspace API
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

  // Request interceptor - add auth token
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

  return client;
}

const apiClient = createApiClient();

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Get all workspaces the current user is a member of
 */
export async function getUserWorkspaces(): Promise<Workspace[]> {
  try {
    const response = await apiClient.get<WorkspaceListResponse[]>('/workspaces');
    return response.data.map(mapWorkspaceResponse);
  } catch (error) {
    // If endpoint doesn't exist yet, return mock data for development
    if ((error as AxiosError)?.response?.status === 404) {
      return getMockWorkspaces();
    }
    throw handleApiError(error);
  }
}

/**
 * Get current workspace from localStorage
 */
export function getCurrentWorkspaceFromStorage(): Workspace | null {
  const id = localStorage.getItem('current_workspace_id');
  const slug = localStorage.getItem('current_workspace_slug');
  const name = localStorage.getItem('workspace_name');

  if (!id || !slug) {
    return null;
  }

  return {
    id,
    slug,
    name: name || 'My Workspace',
    role: 'owner', // Default to owner for current workspace
  };
}

/**
 * Save current workspace to localStorage
 */
export function saveCurrentWorkspaceToStorage(workspace: Workspace): void {
  localStorage.setItem('current_workspace_id', workspace.id);
  localStorage.setItem('current_workspace_slug', workspace.slug);
  localStorage.setItem('workspace_name', workspace.name);
}

/**
 * Switch to a different workspace
 * This will update the JWT token with new workspace claims
 */
export async function switchWorkspace(workspaceId: string): Promise<Workspace> {
  try {
    const response = await apiClient.post<WorkspaceSwitchResponse>(
      '/workspace/switch',
      { workspace_id: workspaceId }
    );

    const workspace = mapWorkspaceResponse(response.data.workspace);
    saveCurrentWorkspaceToStorage(workspace);

    return workspace;
  } catch (error) {
    // If endpoint doesn't exist, just update localStorage
    if ((error as AxiosError)?.response?.status === 404) {
      const workspaces = await getUserWorkspaces();
      const workspace = workspaces.find((w) => w.id === workspaceId);
      if (workspace) {
        saveCurrentWorkspaceToStorage(workspace);
        return workspace;
      }
      throw new Error('Workspace not found');
    }
    throw handleApiError(error);
  }
}

/**
 * Get workspace details by ID
 */
export async function getWorkspaceById(workspaceId: string): Promise<Workspace> {
  try {
    const response = await apiClient.get<WorkspaceListResponse>(
      `/workspace/${workspaceId}`
    );
    return mapWorkspaceResponse(response.data);
  } catch (error) {
    throw handleApiError(error);
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Map API response to Workspace type
 */
function mapWorkspaceResponse(response: WorkspaceListResponse): Workspace {
  return {
    id: response.id,
    name: response.name,
    slug: response.slug,
    logoUrl: response.logo_url,
    role: response.member_role,
    subscription_tier: response.subscription_tier,
    trial_ends_at: response.trial_ends_at,
    created_at: response.created_at,
  };
}

/**
 * Handle API errors consistently
 */
function handleApiError(error: unknown): Error {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError | undefined;
    if (apiError?.message) {
      return new Error(apiError.message);
    }
    if (error.response?.status === 401) {
      return new Error('Authentication required');
    }
    if (error.response?.status === 403) {
      return new Error('Access denied');
    }
    if (error.response?.status === 404) {
      return new Error('Resource not found');
    }
  }
  return error instanceof Error ? error : new Error('Unknown error occurred');
}

/**
 * Mock workspaces for development
 */
function getMockWorkspaces(): Workspace[] {
  const currentId = localStorage.getItem('current_workspace_id');
  const currentSlug = localStorage.getItem('current_workspace_slug');
  const currentName = localStorage.getItem('workspace_name');

  // Return current workspace if available, otherwise empty array
  if (currentId && currentSlug) {
    return [
      {
        id: currentId,
        name: currentName || 'My Workspace',
        slug: currentSlug,
        role: 'owner',
        subscription_tier: 'trial',
      },
    ];
  }

  return [];
}

// ============================================================================
// EXPORTS
// ============================================================================

export const workspaceApi = {
  getUserWorkspaces,
  getCurrentWorkspaceFromStorage,
  saveCurrentWorkspaceToStorage,
  switchWorkspace,
  getWorkspaceById,
};

export default workspaceApi;
