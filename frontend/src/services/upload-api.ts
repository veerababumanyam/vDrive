/**
 * Upload API Service
 * Handles file uploads using TUS protocol and status polling
 */

import * as tus from 'tus-js-client';
import axios from 'axios';
import { getTokenFromMemory } from './authService';

// API Configuration
const UPLOAD_API_URL = import.meta.env.VITE_UPLOAD_API_URL || '/api/v1/files';
// Note: In development, this might need to point to the upload service port directly
// or be routed via nginx. For now assuming /api/v1/files is proxied correctly.

// Types
export interface UploadStatus {
  id: string;
  filename: string;
  mime_type: string;
  expected_size: number;
  received_bytes: number;
  progress_percent: number;
  status: 'created' | 'uploading' | 'assembling' | 'completed' | 'failed';
  asset_id?: string;
  upload_url?: string;
}

export interface UploadProgress {
  bytesUploaded: number;
  bytesTotal: number;
  percentage: number;
}

/**
 * Get upload status
 */
export async function getUploadStatus(uploadId: string): Promise<UploadStatus> {
  const token = getTokenFromMemory();
  const response = await axios.get<UploadStatus>(`${UPLOAD_API_URL}/${uploadId}/status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
}

/**
 * Create and start a TUS upload
 */
export function createTusUpload(
  file: File,
  workspaceId: string, // In a real app, this might be inferred from token or context
  onProgress: (progress: UploadProgress) => void,
  onSuccess: (uploadId: string) => void,
  onError: (error: Error) => void
): tus.Upload {
  const token = getTokenFromMemory();

  // Create upload
  const upload = new tus.Upload(file, {
    endpoint: UPLOAD_API_URL,
    retryDelays: [0, 1000, 3000, 5000],
    headers: {
      Authorization: `Bearer ${token}`,
    },
    metadata: {
      filename: file.name,
      filetype: file.type,
      workspace_id: workspaceId, 
      // Note: Backend seems to extract workspace_id from token, 
      // but if specific workspace is needed it can be passed here if supported
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      onError(error);
    },
    onProgress: (bytesUploaded, bytesTotal) => {
      const percentage = (bytesUploaded / bytesTotal) * 100;
      onProgress({
        bytesUploaded,
        bytesTotal,
        percentage,
      });
    },
    onSuccess: () => {
      // The upload ID is usually the last part of the URL
      const uploadUrl = upload.url;
      if (uploadUrl) {
        const uploadId = uploadUrl.split('/').pop();
        if (uploadId) {
          onSuccess(uploadId);
        } else {
          onError(new Error('Could not extract upload ID from URL'));
        }
      } else {
        onError(new Error('Upload URL not found'));
      }
    },
  });

  return upload;
}
