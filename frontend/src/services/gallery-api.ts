/**
 * Gallery API Service
 * Handles all API calls to the gallery microservice
 *
 * Supports both authenticated (staff) and public (Magic Link) access patterns
 */

import axios, { AxiosError, type AxiosInstance } from 'axios';
import { getTokenFromMemory, setTokenInMemory } from './authService';
import type {
  Gallery,
  GalleryResponse,
  GalleryListResponse,
  GalleryCreateRequest,
  GalleryUpdateRequest,
  GalleryPhotosResponse,
  SubGallery,
  SubGalleryCreate,
  ShareLink,
  MagicLinkAccessRequest,
  MagicLinkAccessResponse,
  VisitorCreate,
  VisitorRegistrationResponse,
  PinVerifyRequest,
  PinVerifyResponse,
  BatchVisibilityRequest,
  BatchSubGalleryRequest,
  BatchPrivacyRequest,
  BatchTagsRequest,
  BatchOperationResponse,
  BatchResponse,
  QRCodeConfig,
  QRCodeResponse,
  GalleryApiError,
  CursorPagination,
} from '../types/gallery';
import type { RefreshTokenResponse } from '../types/onboarding';

// API Configuration
const GALLERY_API_URL = import.meta.env.VITE_GALLERY_API_URL || '/api/v1';
const TIMEOUT_MS = 30000;

// Session storage for Magic Link access
let magicLinkSessionToken: string | null = null;

/**
 * Set Magic Link session token (stored in memory for security)
 */
export function setMagicLinkSession(token: string | null): void {
  magicLinkSessionToken = token;
}

/**
 * Get Magic Link session token
 */
export function getMagicLinkSession(): string | null {
  return magicLinkSessionToken;
}

/**
 * Create axios instance for authenticated staff requests
 */
function createAuthenticatedClient(): AxiosInstance {
  const client = axios.create({
    baseURL: GALLERY_API_URL,
    timeout: TIMEOUT_MS,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
  });

  // Request interceptor - add JWT auth token
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
    async (error: AxiosError<GalleryApiError>) => {
      const originalRequest = error.config as typeof error.config & { _retry?: boolean };

      // Handle 401 - try to refresh token
      if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshResponse = await axios.post<RefreshTokenResponse>(
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
          window.location.href = '/signin';
          return Promise.reject(error);
        }
      }

      return Promise.reject(transformError(error));
    }
  );

  return client;
}

/**
 * Create axios instance for public Magic Link requests
 */
function createPublicClient(): AxiosInstance {
  const client = axios.create({
    baseURL: GALLERY_API_URL,
    timeout: TIMEOUT_MS,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add Magic Link session token
  client.interceptors.request.use(
    (config) => {
      if (magicLinkSessionToken) {
        config.headers['X-Magic-Link-Token'] = magicLinkSessionToken;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - transform errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<GalleryApiError>) => {
      return Promise.reject(transformError(error));
    }
  );

  return client;
}

/**
 * Transform axios error to consistent format
 */
function transformError(error: AxiosError<GalleryApiError>): GalleryApiError {
  const responseData = error.response?.data;

  if (responseData?.error && responseData?.message) {
    return responseData;
  }

  if (responseData) {
    return {
      error: 'UnknownError',
      message: typeof responseData === 'string' ? responseData : JSON.stringify(responseData),
    };
  }

  return {
    error: 'NetworkError',
    message: error.message || 'Network error occurred. Please check your connection.',
  };
}

const authClient = createAuthenticatedClient();
const publicClient = createPublicClient();

// ============================================
// Public API (Magic Link Access)
// ============================================

/**
 * Verify Magic Link and get session token
 */
export async function verifyMagicLink(data: MagicLinkAccessRequest): Promise<MagicLinkAccessResponse> {
  const response = await publicClient.post<MagicLinkAccessResponse>('/public/verify-link', data);

  // Store session token for subsequent requests
  if (response.data.session_token) {
    setMagicLinkSession(response.data.session_token);
  }

  return response.data;
}

/**
 * Get gallery photos for public viewing
 */
export async function getPublicGalleryPhotos(
  galleryId: string,
  options?: CursorPagination & { sub_gallery_id?: string }
): Promise<GalleryPhotosResponse> {
  const response = await publicClient.get<GalleryPhotosResponse>(
    `/public/gallery/${galleryId}/photos`,
    {
      params: {
        cursor: options?.cursor,
        limit: options?.limit || 50,
        sub_gallery_id: options?.sub_gallery_id,
      },
    }
  );
  return response.data;
}

/**
 * Get gallery metadata for public viewing
 */
export async function getPublicGalleryMetadata(galleryId: string): Promise<GalleryResponse> {
  const response = await publicClient.get<GalleryResponse>(`/public/gallery/${galleryId}`);
  return response.data;
}

/**
 * Verify PIN for private photo
 */
export async function verifyPhotoPin(data: PinVerifyRequest): Promise<PinVerifyResponse> {
  const response = await publicClient.post<PinVerifyResponse>(
    `/public/photo/${data.asset_id}/verify-pin`,
    { pin: data.pin }
  );
  return response.data;
}

/**
 * Register visitor email for gallery access
 */
export async function registerVisitor(
  galleryId: string,
  data: VisitorCreate
): Promise<VisitorRegistrationResponse> {
  const response = await publicClient.post<VisitorRegistrationResponse>(
    '/public/register-visitor',
    { ...data, gallery_id: galleryId }
  );

  // Update session with visitor token
  if (response.data.session_token) {
    setMagicLinkSession(response.data.session_token);
  }

  return response.data;
}

/**
 * Add photo to favorites (public)
 */
export async function addToFavorites(galleryId: string, assetId: string): Promise<void> {
  await publicClient.post(`/public/gallery/${galleryId}/favorite/${assetId}`);
}

/**
 * Remove photo from favorites (public)
 */
export async function removeFromFavorites(galleryId: string, assetId: string): Promise<void> {
  await publicClient.delete(`/public/gallery/${galleryId}/favorite/${assetId}`);
}

/**
 * Add photo to selections (public)
 */
export async function addToSelections(galleryId: string, assetId: string): Promise<void> {
  await publicClient.post(`/public/gallery/${galleryId}/selection/${assetId}`);
}

/**
 * Remove photo from selections (public)
 */
export async function removeFromSelections(galleryId: string, assetId: string): Promise<void> {
  await publicClient.delete(`/public/gallery/${galleryId}/selection/${assetId}`);
}

// ============================================
// Staff API (Authenticated)
// ============================================

/**
 * List galleries for current workspace
 */
export async function listGalleries(
  page = 1,
  pageSize = 20,
  status?: string
): Promise<GalleryListResponse> {
  const response = await authClient.get<GalleryListResponse>('/galleries', {
    params: { page, page_size: pageSize, status },
  });
  return response.data;
}

/**
 * Get single gallery details
 */
export async function getGallery(galleryId: string): Promise<GalleryResponse> {
  const response = await authClient.get<GalleryResponse>(`/galleries/${galleryId}`);
  return response.data;
}

/**
 * Create new gallery
 */
export async function createGallery(data: GalleryCreateRequest): Promise<Gallery> {
  const response = await authClient.post<Gallery>('/galleries', data);
  return response.data;
}

/**
 * Update gallery
 */
export async function updateGallery(
  galleryId: string,
  data: GalleryUpdateRequest
): Promise<Gallery> {
  const response = await authClient.patch<Gallery>(`/galleries/${galleryId}`, data);
  return response.data;
}

/**
 * Delete gallery
 */
export async function deleteGallery(galleryId: string): Promise<void> {
  await authClient.delete(`/galleries/${galleryId}`);
}

/**
 * Publish gallery (change status to published)
 */
export async function publishGallery(galleryId: string): Promise<Gallery> {
  const response = await authClient.post<Gallery>(`/galleries/${galleryId}/publish`);
  return response.data;
}

/**
 * Archive gallery
 */
export async function archiveGallery(galleryId: string): Promise<Gallery> {
  const response = await authClient.post<Gallery>(`/galleries/${galleryId}/archive`);
  return response.data;
}

/**
 * Get gallery photos (staff view includes all photos)
 */
export async function getGalleryPhotos(
  galleryId: string,
  options?: CursorPagination & { sub_gallery_id?: string; include_private?: boolean }
): Promise<GalleryPhotosResponse> {
  const response = await authClient.get<GalleryPhotosResponse>(
    `/galleries/${galleryId}/photos`,
    {
      params: {
        cursor: options?.cursor,
        limit: options?.limit || 50,
        sub_gallery_id: options?.sub_gallery_id,
        include_private: options?.include_private ?? true,
      },
    }
  );
  return response.data;
}

// ============================================
// Sub-Gallery API (Staff)
// ============================================

/**
 * Create sub-gallery
 */
export async function createSubGallery(
  galleryId: string,
  data: SubGalleryCreate
): Promise<SubGallery> {
  const response = await authClient.post<SubGallery>(
    `/galleries/${galleryId}/sub-galleries`,
    data
  );
  return response.data;
}

/**
 * Update sub-gallery
 */
export async function updateSubGallery(
  galleryId: string,
  subGalleryId: string,
  data: Partial<SubGalleryCreate>
): Promise<SubGallery> {
  const response = await authClient.patch<SubGallery>(
    `/galleries/${galleryId}/sub-galleries/${subGalleryId}`,
    data
  );
  return response.data;
}

/**
 * Delete sub-gallery
 */
export async function deleteSubGallery(galleryId: string, subGalleryId: string): Promise<void> {
  await authClient.delete(`/galleries/${galleryId}/sub-galleries/${subGalleryId}`);
}

/**
 * Reorder sub-galleries
 */
export async function reorderSubGalleries(
  galleryId: string,
  subGalleryIds: string[]
): Promise<SubGallery[]> {
  const response = await authClient.post<SubGallery[]>(
    `/galleries/${galleryId}/sub-galleries/reorder`,
    { sub_gallery_ids: subGalleryIds }
  );
  return response.data;
}

// ============================================
// Batch Operations API (Staff)
// ============================================

/**
 * Batch update visibility
 */
export async function batchUpdateVisibility(
  galleryId: string,
  data: BatchVisibilityRequest
): Promise<BatchOperationResponse> {
  const response = await authClient.post<BatchOperationResponse>(
    `/galleries/${galleryId}/batch/visibility`,
    data
  );
  return response.data;
}

/**
 * Batch reassign to sub-gallery
 */
export async function batchReassignSubGallery(
  galleryId: string,
  data: BatchSubGalleryRequest
): Promise<BatchOperationResponse> {
  const response = await authClient.post<BatchOperationResponse>(
    `/galleries/${galleryId}/batch/sub-gallery`,
    data
  );
  return response.data;
}

/**
 * Batch update privacy settings
 */
export async function batchUpdatePrivacy(
  galleryId: string,
  data: BatchPrivacyRequest
): Promise<BatchOperationResponse> {
  const response = await authClient.post<BatchOperationResponse>(
    `/galleries/${galleryId}/batch/privacy`,
    data
  );
  return response.data;
}

/**
 * Batch update tags
 */
export async function batchUpdateTags(
  galleryId: string,
  data: BatchTagsRequest
): Promise<BatchOperationResponse> {
  const response = await authClient.post<BatchOperationResponse>(
    `/galleries/${galleryId}/batch/tags`,
    data
  );
  return response.data;
}

// ============================================
// Share Link API (Staff)
// ============================================

/**
 * Create share link for gallery
 */
export async function createShareLink(
  galleryId: string,
  options?: {
    label?: string;
    password?: string;
    expires_at?: string;
    max_accesses?: number;
    email_registration_required?: boolean;
    allowed_actions?: string[];
  }
): Promise<ShareLink> {
  const response = await authClient.post<ShareLink>(
    `/galleries/${galleryId}/share-links`,
    options
  );
  return response.data;
}

/**
 * List share links for gallery
 */
export async function listShareLinks(galleryId: string): Promise<ShareLink[]> {
  const response = await authClient.get<ShareLink[]>(`/galleries/${galleryId}/share-links`);
  return response.data;
}

/**
 * Revoke share link
 */
export async function revokeShareLink(galleryId: string, linkId: string): Promise<void> {
  await authClient.delete(`/galleries/${galleryId}/share-links/${linkId}`);
}

/**
 * Generate QR code for share link
 */
export async function generateQRCode(
  linkId: string,
  config?: QRCodeConfig
): Promise<QRCodeResponse> {
  const response = await authClient.get<QRCodeResponse>(`/staff/share-link/${linkId}/qr-code`, {
    params: config,
  });
  return response.data;
}

/**
 * Batch add assets to gallery
 */
export async function batchAddAssets(
  assetIds: string[],
  galleryId: string,
  workspaceId: string
): Promise<BatchResponse> {
  const response = await authClient.post<BatchResponse>('/batch/assets/add', assetIds, {
    params: {
      gallery_id: galleryId,
      workspace_id: workspaceId,
    }
  });
  return response.data;
}

// ============================================
// WebSocket Connection
// ============================================

/**
 * Create WebSocket connection for real-time updates
 */
export function createGalleryWebSocket(
  galleryId: string,
  onMessage: (event: MessageEvent) => void,
  onError?: (event: Event) => void,
  onClose?: (event: CloseEvent) => void
): WebSocket {
  // Build WebSocket URL properly for both dev (Vite proxy) and production
  // In dev: relative URL works with Vite's WebSocket proxy
  // In prod: use VITE_GALLERY_WS_URL if set, otherwise derive from current location
  const token = magicLinkSessionToken || getTokenFromMemory();

  if (!token) {
    console.error('No authentication token available for WebSocket connection');
    throw new Error('Authentication required for WebSocket connection');
  }

  // Use environment variable if set, otherwise construct from current location
  let wsUrl: string;
  if (import.meta.env.VITE_GALLERY_WS_URL) {
    wsUrl = import.meta.env.VITE_GALLERY_WS_URL;
  } else {
    // For Vite dev server, use relative URL which will be proxied
    // The proxy config in vite.config.ts handles /api/v1/ws -> ws://localhost:8004
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl = `${wsProtocol}//${window.location.host}`;
  }

  const fullUrl = `${wsUrl}/api/v1/ws/gallery/${galleryId}?token=${token}`;
  console.log('WebSocket connecting to:', fullUrl.replace(/token=.*$/, 'token=[REDACTED]'));

  const ws = new WebSocket(fullUrl);

  ws.onmessage = onMessage;
  ws.onerror = onError || ((e) => console.error('WebSocket error:', e));
  ws.onclose = onClose || ((e) => console.log('WebSocket closed:', e.code, e.reason));

  return ws;
}

/**
 * WebSocket reconnection helper with exponential backoff
 */
export function createReconnectingWebSocket(
  galleryId: string,
  handlers: {
    onMessage: (event: MessageEvent) => void;
    onOpen?: () => void;
    onError?: (event: Event) => void;
    onClose?: (event: CloseEvent) => void;
  },
  maxRetries = 5
): { ws: WebSocket | null; disconnect: () => void } {
  let ws: WebSocket | null = null;
  let retryCount = 0;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let isDisconnected = false;

  const connect = () => {
    if (isDisconnected) return;

    ws = createGalleryWebSocket(
      galleryId,
      handlers.onMessage,
      (event) => {
        handlers.onError?.(event);
        scheduleReconnect();
      },
      (event) => {
        handlers.onClose?.(event);
        if (event.code !== 1000) {
          // Not a normal closure
          scheduleReconnect();
        }
      }
    );

    ws.onopen = () => {
      retryCount = 0;
      handlers.onOpen?.();
    };
  };

  const scheduleReconnect = () => {
    if (isDisconnected || retryCount >= maxRetries) return;

    const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
    retryCount++;

    reconnectTimeout = setTimeout(connect, delay);
  };

  const disconnect = () => {
    isDisconnected = true;
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
    }
    if (ws) {
      ws.close(1000, 'Client disconnect');
      ws = null;
    }
  };

  connect();

  return { ws, disconnect };
}

// ============================================
// Export all functions
// ============================================

export const galleryApi = {
  // Public API
  verifyMagicLink,
  getPublicGalleryPhotos,
  getPublicGalleryMetadata,
  verifyPhotoPin,
  registerVisitor,
  addToFavorites,
  removeFromFavorites,
  addToSelections,
  removeFromSelections,

  // Staff API
  listGalleries,
  getGallery,
  createGallery,
  updateGallery,
  deleteGallery,
  publishGallery,
  archiveGallery,
  getGalleryPhotos,

  // Sub-galleries
  createSubGallery,
  updateSubGallery,
  deleteSubGallery,
  reorderSubGalleries,

  // Batch operations
  batchUpdateVisibility,
  batchReassignSubGallery,
  batchUpdatePrivacy,
  batchUpdateTags,

  // Share links
  createShareLink,
  listShareLinks,
  revokeShareLink,
  generateQRCode,

  // WebSocket
  createGalleryWebSocket,
  createReconnectingWebSocket,

  // Session management
  setMagicLinkSession,
  getMagicLinkSession,
};

export default galleryApi;
