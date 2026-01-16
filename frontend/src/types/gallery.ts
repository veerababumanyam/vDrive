/**
 * Gallery Service API Types
 * Based on services/gallery-service Pydantic schemas
 */

// ============================================
// Gallery Core Types
// ============================================

export type GalleryStatus = 'draft' | 'published' | 'archived';
export type LayoutStyle = 'tab' | 'continuous_scroll';
export type DownloadPolicy = 'VIEW_ONLY' | 'WEB_ONLY' | 'WATERMARKED_ONLY' | 'ORIGINAL_ALLOWED';

export interface Gallery {
  gallery_id: string;
  workspace_id: string;
  title: string;
  description?: string;
  client_name?: string;
  shoot_date?: string;
  status: GalleryStatus;
  cover_asset_id?: string;
  cover_url?: string;

  // Settings
  password_protected: boolean;
  pin_protected: boolean;
  email_registration_required: boolean;
  expires_at?: string;
  download_policy: DownloadPolicy;
  layout_style: LayoutStyle;
  theme?: string;

  // Denormalized stats
  photo_count: number;
  video_count: number;
  favorites_count: number;
  total_size_bytes: number;

  // Relationships
  sub_galleries?: SubGallery[];

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface GalleryStats {
  photo_count: number;
  video_count: number;
  favorites_count: number;
  selections_count: number;
  total_size_bytes: number;
  views_count: number;
}

export interface GalleryResponse extends Gallery {
  stats: GalleryStats;
}

export interface GalleryListResponse {
  galleries: Gallery[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ============================================
// Sub-Gallery Types
// ============================================

export interface SubGallery {
  sub_gallery_id: string;
  gallery_id: string;
  name: string;
  sort_order: number;
  visible: boolean;
  cover_asset_id?: string;
  cover_url?: string;
  photo_count: number;
}

export interface SubGalleryCreate {
  name: string;
  sort_order?: number;
  visible?: boolean;
  cover_asset_id?: string;
}

// ============================================
// Gallery Asset Types
// ============================================

export type AssetType = 'photo' | 'video';

export interface GalleryAsset {
  gallery_asset_id: string;
  gallery_id: string;
  asset_id: string;
  sub_gallery_id?: string;
  sort_order: number;
  visible: boolean;
  is_private: boolean;
  title?: string;
  description?: string;
  tags: string[];

  // Asset metadata
  type: AssetType;
  width: number;
  height: number;
  mime_type: string;
  file_size: number;
  date_taken?: string;

  // URLs
  lqip?: string; // Base64 Low Quality Image Placeholder
  thumbnail_url?: string; // Signed URL for thumbnail
  preview_url?: string; // Signed URL for preview (medium size)
  download_url?: string; // Signed URL for download (if allowed)
  locked_thumbnail_url?: string; // For PIN-protected photos

  // Interaction counts
  favorites_count: number;
  selections_count: number;
}

export interface GalleryPhotosResponse {
  photos: GalleryAsset[];
  cursor?: string;
  has_more: boolean;
  total_count: number;
}

// ============================================
// Magic Link / Share Link Types
// ============================================

export type ShareLinkStatus = 'active' | 'expired' | 'revoked';
export type ShareTargetType = 'gallery' | 'sub_gallery' | 'photo';
export type AllowedAction = 'view' | 'favorite' | 'select' | 'comment' | 'download';

export interface ShareLink {
  link_id: string;
  gallery_id: string;
  label?: string;
  target_type: ShareTargetType;
  status: ShareLinkStatus;
  expires_at?: string;
  max_accesses?: number;
  access_count: number;

  // Policies
  password_required: boolean;
  email_registration_required: boolean;
  allowed_actions: AllowedAction[];
  download_variant?: DownloadPolicy;

  // QR Code config
  qr_code_url?: string;
  qr_size?: number;
  qr_color?: string;
  qr_logo_enabled?: boolean;
  qr_error_correction?: 'L' | 'M' | 'Q' | 'H';

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface MagicLinkAccessRequest {
  link_id: string;
  password?: string;
}

export interface MagicLinkAccessResponse {
  success: boolean;
  gallery_id: string;
  gallery_title: string;
  session_token: string;
  expires_at: string;
  email_registration_required: boolean;
  allowed_actions: AllowedAction[];
  download_policy: DownloadPolicy;
}

export interface VerifyLinkRequest {
  link_id: string;
  password?: string;
}

// ============================================
// Visitor / Email Registration Types
// ============================================

export interface Visitor {
  visitor_id: string;
  workspace_id: string;
  email: string;
  name?: string;
  phone?: string;
  address?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface VisitorCreate {
  email: string;
  name?: string;
  phone?: string;
  address?: string;
  metadata?: Record<string, unknown>;
}

export interface VisitorRegistrationResponse {
  success: boolean;
  visitor_id: string;
  session_token: string;
}

// ============================================
// PIN Protection Types
// ============================================

export interface PinVerifyRequest {
  asset_id: string;
  pin: string;
}

export interface PinVerifyResponse {
  success: boolean;
  unlocked_until?: string;
  remaining_attempts?: number;
  locked_until?: string;
}

// ============================================
// WebSocket Event Types
// ============================================

export type WebSocketEventType =
  | 'favorite_added'
  | 'favorite_removed'
  | 'selection_added'
  | 'selection_removed'
  | 'comment_added'
  | 'connection_opened'
  | 'connection_closed'
  | 'sync_response';

export interface WebSocketMessage {
  type: WebSocketEventType;
  gallery_id: string;
  asset_id?: string;
  data?: Record<string, unknown>;
  timestamp: string;
  seq: number;
}

export interface FavoriteEvent {
  asset_id: string;
  favorites_count: number;
  user_type: 'staff' | 'client';
}

export interface SelectionEvent {
  asset_id: string;
  selections_count: number;
  user_type: 'staff' | 'client';
}

export interface CommentEvent {
  asset_id: string;
  comment_id: string;
  comment_text: string;
  author_name?: string;
}

// ============================================
// Batch Operation Types
// ============================================

export interface BatchVisibilityRequest {
  asset_ids: string[];
  visible: boolean;
}

export interface BatchSubGalleryRequest {
  asset_ids: string[];
  sub_gallery_id: string;
}

export interface BatchPrivacyRequest {
  asset_ids: string[];
  is_private: boolean;
  pin?: string;
}

export interface BatchTagsRequest {
  asset_ids: string[];
  operation: 'add' | 'remove' | 'replace';
  tags: string[];
}

export interface BatchOperationResponse {
  success: boolean;
  updated_count: number;
  failed_count: number;
  errors?: Array<{
    asset_id: string;
    error: string;
  }>;
}

export interface BatchResponse {
  operation: string;
  total_requested: number;
  successful: number;
  failed: number;
  errors: Array<{
    asset_id: string;
    error: string;
  }>;
  processed_ids: string[];
  started_at: string;
  completed_at: string;
  duration_seconds: number;
}

// ============================================
// Gallery Create/Update Types
// ============================================

export interface GalleryCreateRequest {
  title: string;
  description?: string;
  client_name?: string;
  shoot_date?: string;
  password?: string;
  email_registration_required?: boolean;
  download_policy?: DownloadPolicy;
  layout_style?: LayoutStyle;
  theme?: string;
}

export interface GalleryUpdateRequest {
  title?: string;
  description?: string;
  client_name?: string;
  shoot_date?: string;
  status?: GalleryStatus;
  cover_asset_id?: string;
  password?: string;
  pin_protected?: boolean;
  email_registration_required?: boolean;
  download_policy?: DownloadPolicy;
  layout_style?: LayoutStyle;
  theme?: string;
}

// ============================================
// QR Code Types
// ============================================

export interface QRCodeConfig {
  size?: 200 | 300 | 500 | 1000;
  color?: string;
  logo_enabled?: boolean;
  error_correction?: 'L' | 'M' | 'Q' | 'H';
}

export interface QRCodeResponse {
  qr_code_url: string;
  encoded_url: string;
}

// ============================================
// Error Types
// ============================================

export interface GalleryApiError {
  error: string;
  message: string;
  details?: Array<{
    field: string;
    message: string;
    code: string;
  }>;
  request_id?: string;
}

// ============================================
// Pagination Types
// ============================================

export interface CursorPagination {
  cursor?: string;
  limit?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  cursor?: string;
  has_more: boolean;
  total_count?: number;
}
