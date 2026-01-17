/**
 * Watermark API Types
 * Based on services/gallery-service/src/app/schemas/watermark.py Pydantic schemas
 */

// ============================================
// Watermark Enums
// ============================================

export type WatermarkType = 'text' | 'image';

export type WatermarkPosition =
  | 'center'
  | 'top_left'
  | 'top_right'
  | 'bottom_left'
  | 'bottom_right'
  | 'tiled';

// ============================================
// Watermark Configuration Types
// ============================================

export interface TextWatermark {
  text: string;
  font_family?: string;
  font_size?: number;
  color?: string;
  opacity?: number;
  position?: WatermarkPosition;
  margin?: number;
  rotation?: number;
}

export interface ImageWatermark {
  image_url: string;
  scale?: number;
  opacity?: number;
  position?: WatermarkPosition;
  margin?: number;
  tile_spacing?: number;
}

export interface WatermarkConfig {
  enabled: boolean;
  watermark_type: WatermarkType;
  text_config?: TextWatermark | null;
  image_config?: ImageWatermark | null;
}

export interface WatermarkConfigResponse {
  gallery_id: string;
  enabled: boolean;
  watermark_type?: WatermarkType | null;
  text_config?: TextWatermark | null;
  image_config?: ImageWatermark | null;
  updated_at?: string | null;
}

// ============================================
// Watermark Preview Types
// ============================================

export interface WatermarkPreviewRequest {
  asset_id: string;
  config: WatermarkConfig;
}

export interface WatermarkPreviewResponse {
  preview_url?: string;
  preview_base64?: string;
  message?: string;
  status?: string;
}

// ============================================
// Watermark Batch Apply Types
// ============================================

export interface WatermarkApplyResponse {
  message: string;
  gallery_id: string;
  job_id: string;
  status: string;
}

export interface WatermarkStatusResponse {
  gallery_id: string;
  job_id: string;
  status: string;
  total?: number;
  completed?: number;
  failed?: number;
  progress_percentage?: number;
  message?: string;
}

// ============================================
// Error Types
// ============================================

export interface ApiError {
  error: string;
  message: string;
}
