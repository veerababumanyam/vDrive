// Custom Hooks
export {
  useTheme,
  ThemeProvider,
  usePrefersReducedMotion,
  type Theme,
  type ResolvedTheme,
  type ThemeContextValue,
  type ThemeProviderProps,
} from './useTheme';

export {
  useRegistration,
  type RegistrationFormData,
  type RegistrationFormErrors,
  type PasswordStrength,
  type UseRegistrationOptions,
  type UseRegistrationReturn,
} from './useRegistration';

export {
  useOnboardingState,
  type WorkspaceFormData,
  type UseOnboardingStateReturn,
} from './useOnboardingState';

// Mobile-first hooks
export { default as useMobile } from './useMobile';
export {
  useBreakpoint,
  useMediaQuery,
  useSwipeGesture,
  usePullToRefresh,
  usePinchZoom,
  useLongPress,
  useHaptic,
  useDeviceCapabilities,
  useScrollReveal,
  useInfiniteScroll,
  useScrollPosition,
  useFocusTrap,
  useAnnounce,
  useArrowNavigation,
  useSafeArea,
  useOnlineStatus,
  usePrefersColorScheme,
} from './useMobile';

// Gallery hooks
export {
  galleryKeys,
  useGalleries,
  useGallery,
  useGalleryPhotos,
  useShareLinks,
  usePublicGallery,
  usePublicGalleryPhotos,
  useCreateGallery,
  useUpdateGallery,
  usePublishGallery,
  useArchiveGallery,
  useDeleteGallery,
  useCreateShareLink,
  useRevokeShareLink,
  useBatchUpdateVisibility,
  useBatchReassignSubGallery,
  useBatchUpdatePrivacy,
  useBatchUpdateTags,
  useToggleFavorite,
} from './useGallery';
