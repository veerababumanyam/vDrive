/**
 * Gallery Hooks
 *
 * React Query-based hooks for gallery data fetching and mutations.
 * Provides caching, optimistic updates, and automatic refetching.
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  useInfiniteQuery,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import {
  listGalleries,
  getGallery,
  createGallery,
  updateGallery,
  publishGallery,
  archiveGallery,
  deleteGallery,
  getGalleryPhotos,
  getPublicGalleryMetadata,
  getPublicGalleryPhotos,
  createShareLink,
  listShareLinks,
  revokeShareLink,
  batchUpdateVisibility,
  batchReassignSubGallery,
  batchUpdatePrivacy,
  batchUpdateTags,
  addToFavorites,
  removeFromFavorites,
} from '../services/gallery-api';
import type {
  Gallery,
  GalleryResponse,
  GalleryListResponse,
  GalleryCreateRequest,
  GalleryUpdateRequest,
  ShareLink,
  BatchVisibilityRequest,
  BatchSubGalleryRequest,
  BatchPrivacyRequest,
  BatchTagsRequest,
  BatchOperationResponse,
  GalleryStatus,
} from '../types/gallery';

// ============================================
// Query Keys
// ============================================

export const galleryKeys = {
  all: ['galleries'] as const,
  lists: () => [...galleryKeys.all, 'list'] as const,
  list: (filters: { status?: GalleryStatus; page?: number }) =>
    [...galleryKeys.lists(), filters] as const,
  details: () => [...galleryKeys.all, 'detail'] as const,
  detail: (id: string) => [...galleryKeys.details(), id] as const,
  photos: (id: string) => [...galleryKeys.detail(id), 'photos'] as const,
  shareLinks: (id: string) => [...galleryKeys.detail(id), 'shareLinks'] as const,
  public: () => [...galleryKeys.all, 'public'] as const,
  publicDetail: (id: string) => [...galleryKeys.public(), id] as const,
  publicPhotos: (id: string) => [...galleryKeys.publicDetail(id), 'photos'] as const,
};

// ============================================
// Staff Hooks (Authenticated)
// ============================================

/**
 * Fetch paginated gallery list for current workspace
 */
export function useGalleries(
  page = 1,
  pageSize = 20,
  status?: GalleryStatus,
  options?: Omit<UseQueryOptions<GalleryListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: galleryKeys.list({ status, page }),
    queryFn: () => listGalleries(page, pageSize, status),
    staleTime: 1000 * 60 * 2, // 2 minutes
    ...options,
  });
}

/**
 * Fetch single gallery details
 */
export function useGallery(
  galleryId: string,
  options?: Omit<UseQueryOptions<GalleryResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: galleryKeys.detail(galleryId),
    queryFn: () => getGallery(galleryId),
    enabled: !!galleryId,
    staleTime: 1000 * 60 * 2,
    ...options,
  });
}

/**
 * Fetch gallery photos with infinite scroll
 */
export function useGalleryPhotos(
  galleryId: string,
  options?: { subGalleryId?: string; includePrivate?: boolean }
) {
  return useInfiniteQuery({
    queryKey: galleryKeys.photos(galleryId),
    queryFn: ({ pageParam }) =>
      getGalleryPhotos(galleryId, {
        cursor: pageParam,
        limit: 50,
        sub_gallery_id: options?.subGalleryId,
        include_private: options?.includePrivate ?? true,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.cursor : undefined,
    enabled: !!galleryId,
    staleTime: 1000 * 60 * 2,
    initialPageParam: undefined as string | undefined,
  });
}

/**
 * Fetch share links for gallery
 */
export function useShareLinks(
  galleryId: string,
  options?: Omit<UseQueryOptions<ShareLink[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: galleryKeys.shareLinks(galleryId),
    queryFn: () => listShareLinks(galleryId),
    enabled: !!galleryId,
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

// ============================================
// Public Hooks (Magic Link Access)
// ============================================

/**
 * Fetch public gallery metadata
 */
export function usePublicGallery(
  galleryId: string,
  options?: Omit<UseQueryOptions<GalleryResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: galleryKeys.publicDetail(galleryId),
    queryFn: () => getPublicGalleryMetadata(galleryId),
    enabled: !!galleryId,
    staleTime: 1000 * 60 * 5,
    ...options,
  });
}

/**
 * Fetch public gallery photos with infinite scroll
 */
export function usePublicGalleryPhotos(
  galleryId: string,
  options?: { subGalleryId?: string }
) {
  return useInfiniteQuery({
    queryKey: galleryKeys.publicPhotos(galleryId),
    queryFn: ({ pageParam }) =>
      getPublicGalleryPhotos(galleryId, {
        cursor: pageParam,
        limit: 50,
        sub_gallery_id: options?.subGalleryId,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.cursor : undefined,
    enabled: !!galleryId,
    staleTime: 1000 * 60 * 5,
    initialPageParam: undefined as string | undefined,
  });
}

// ============================================
// Mutation Hooks
// ============================================

/**
 * Create new gallery
 */
export function useCreateGallery(
  options?: UseMutationOptions<Gallery, Error, GalleryCreateRequest>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createGallery,
    onSuccess: () => {
      // Invalidate gallery list to show new gallery
      queryClient.invalidateQueries({ queryKey: galleryKeys.lists() });
    },
    ...options,
  });
}

/**
 * Update gallery
 */
export function useUpdateGallery(
  galleryId: string,
  options?: UseMutationOptions<Gallery, Error, GalleryUpdateRequest>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GalleryUpdateRequest) => updateGallery(galleryId, data),
    onSuccess: (updatedGallery) => {
      // Update cache with new data
      queryClient.setQueryData(
        galleryKeys.detail(galleryId),
        (old: GalleryResponse | undefined) =>
          old ? { ...old, ...updatedGallery } : undefined
      );
      // Invalidate list to reflect changes
      queryClient.invalidateQueries({ queryKey: galleryKeys.lists() });
    },
    ...options,
  });
}

/**
 * Publish gallery
 */
export function usePublishGallery(
  galleryId: string,
  options?: UseMutationOptions<Gallery, Error, void>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => publishGallery(galleryId),
    onSuccess: (updatedGallery) => {
      queryClient.setQueryData(
        galleryKeys.detail(galleryId),
        (old: GalleryResponse | undefined) =>
          old ? { ...old, ...updatedGallery } : undefined
      );
      queryClient.invalidateQueries({ queryKey: galleryKeys.lists() });
    },
    ...options,
  });
}

/**
 * Archive gallery
 */
export function useArchiveGallery(
  galleryId: string,
  options?: UseMutationOptions<Gallery, Error, void>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => archiveGallery(galleryId),
    onSuccess: (updatedGallery) => {
      queryClient.setQueryData(
        galleryKeys.detail(galleryId),
        (old: GalleryResponse | undefined) =>
          old ? { ...old, ...updatedGallery } : undefined
      );
      queryClient.invalidateQueries({ queryKey: galleryKeys.lists() });
    },
    ...options,
  });
}

/**
 * Delete gallery
 */
export function useDeleteGallery(
  options?: UseMutationOptions<void, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteGallery,
    onSuccess: (_, galleryId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: galleryKeys.detail(galleryId) });
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: galleryKeys.lists() });
    },
    ...options,
  });
}

/**
 * Create share link
 */
export function useCreateShareLink(
  galleryId: string,
  options?: UseMutationOptions<ShareLink, Error, Parameters<typeof createShareLink>[1]>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (linkOptions) => createShareLink(galleryId, linkOptions),
    onSuccess: (newLink) => {
      queryClient.setQueryData(
        galleryKeys.shareLinks(galleryId),
        (old: ShareLink[] | undefined) => (old ? [newLink, ...old] : [newLink])
      );
    },
    ...options,
  });
}

/**
 * Revoke share link
 */
export function useRevokeShareLink(
  galleryId: string,
  options?: UseMutationOptions<void, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (linkId: string) => revokeShareLink(galleryId, linkId),
    onSuccess: (_, linkId) => {
      queryClient.setQueryData(
        galleryKeys.shareLinks(galleryId),
        (old: ShareLink[] | undefined) =>
          old ? old.filter((link) => link.link_id !== linkId) : []
      );
    },
    ...options,
  });
}

// ============================================
// Batch Operation Hooks
// ============================================

/**
 * Batch update photo visibility
 */
export function useBatchUpdateVisibility(
  galleryId: string,
  options?: UseMutationOptions<BatchOperationResponse, Error, BatchVisibilityRequest>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchVisibilityRequest) =>
      batchUpdateVisibility(galleryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: galleryKeys.photos(galleryId) });
    },
    ...options,
  });
}

/**
 * Batch reassign to sub-gallery
 */
export function useBatchReassignSubGallery(
  galleryId: string,
  options?: UseMutationOptions<BatchOperationResponse, Error, BatchSubGalleryRequest>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchSubGalleryRequest) =>
      batchReassignSubGallery(galleryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: galleryKeys.photos(galleryId) });
      queryClient.invalidateQueries({ queryKey: galleryKeys.detail(galleryId) });
    },
    ...options,
  });
}

/**
 * Batch update privacy
 */
export function useBatchUpdatePrivacy(
  galleryId: string,
  options?: UseMutationOptions<BatchOperationResponse, Error, BatchPrivacyRequest>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchPrivacyRequest) =>
      batchUpdatePrivacy(galleryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: galleryKeys.photos(galleryId) });
    },
    ...options,
  });
}

/**
 * Batch update tags
 */
export function useBatchUpdateTags(
  galleryId: string,
  options?: UseMutationOptions<BatchOperationResponse, Error, BatchTagsRequest>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchTagsRequest) =>
      batchUpdateTags(galleryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: galleryKeys.photos(galleryId) });
    },
    ...options,
  });
}

// ============================================
// Favorite Hooks (Public)
// ============================================

/**
 * Toggle favorite on a photo
 */
export function useToggleFavorite(galleryId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      assetId,
      isFavorited,
    }: {
      assetId: string;
      isFavorited: boolean;
    }) => {
      if (isFavorited) {
        await removeFromFavorites(galleryId, assetId);
      } else {
        await addToFavorites(galleryId, assetId);
      }
      return { assetId, isFavorited: !isFavorited };
    },
    // Optimistic update
    onMutate: async () => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: galleryKeys.publicPhotos(galleryId),
      });

      // Snapshot previous value for rollback
      const previousPhotos = queryClient.getQueryData(
        galleryKeys.publicPhotos(galleryId)
      );

      return { previousPhotos };
    },
    onError: (_, __, context) => {
      // Rollback on error
      if (context?.previousPhotos) {
        queryClient.setQueryData(
          galleryKeys.publicPhotos(galleryId),
          context.previousPhotos
        );
      }
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({
        queryKey: galleryKeys.publicPhotos(galleryId),
      });
    },
  });
}
