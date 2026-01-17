/**
 * Photography-Specific Icons for RawDrive
 * Modern, distinctive icons optimized for the photography platform
 * Features filled/stroke variants for active/inactive states
 */

import type { FC } from 'react';

interface IconProps {
  className?: string;
  size?: number | string;
  filled?: boolean;
}

// ============================================================================
// DASHBOARD - Aperture/Lens inspired icon
// ============================================================================

export const ApertureIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <circle cx="12" cy="12" r="10" fillOpacity="0.15" />
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M14.31 8l5.74 9.94M9.69 8h11.48M7.38 12l5.74-9.94M9.69 16L3.95 6.06M14.31 16H2.83M16.62 12l-5.74 9.94" />
      </>
    ) : (
      <>
        <circle cx="12" cy="12" r="10" />
        <path d="M14.31 8l5.74 9.94M9.69 8h11.48M7.38 12l5.74-9.94M9.69 16L3.95 6.06M14.31 16H2.83M16.62 12l-5.74 9.94" />
      </>
    )}
  </svg>
);

// ============================================================================
// GALLERY - Modern grid with photo frame
// ============================================================================

export const GalleryGridIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <rect x="3" y="3" width="7" height="9" rx="2" fill="currentColor" />
        <rect x="14" y="3" width="7" height="5" rx="2" fill="currentColor" />
        <rect x="3" y="16" width="7" height="5" rx="2" fill="currentColor" />
        <rect x="14" y="12" width="7" height="9" rx="2" fill="currentColor" />
      </>
    ) : (
      <>
        <rect x="3" y="3" width="7" height="9" rx="2" />
        <rect x="14" y="3" width="7" height="5" rx="2" />
        <rect x="3" y="16" width="7" height="5" rx="2" />
        <rect x="14" y="12" width="7" height="9" rx="2" />
      </>
    )}
  </svg>
);

// ============================================================================
// INVITATIONS - Elegant envelope with photo
// ============================================================================

export const PhotoEnvelopeIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <rect x="2" y="5" width="20" height="14" rx="2" fill="currentColor" fillOpacity="0.15" />
        <path d="M2 5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5z" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M22 6l-10 7L2 6" strokeWidth="2" fill="none" />
        <circle cx="17" cy="15" r="2" fill="currentColor" />
      </>
    ) : (
      <>
        <rect x="2" y="4" width="20" height="16" rx="2" />
        <path d="M22 7l-10 7L2 7" />
        <circle cx="17" cy="15" r="2" />
      </>
    )}
  </svg>
);

// ============================================================================
// CALENDAR - Modern calendar with lens
// ============================================================================

export const PhotoCalendarIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <rect x="3" y="4" width="18" height="18" rx="2" fill="currentColor" fillOpacity="0.15" />
        <path d="M3 4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4z" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M16 2v4M8 2v4M3 10h18" strokeWidth="2" fill="none" />
        <circle cx="12" cy="16" r="3" fill="currentColor" />
        <circle cx="12" cy="16" r="1" fill="white" />
      </>
    ) : (
      <>
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <path d="M16 2v4M8 2v4M3 10h18" />
        <circle cx="12" cy="16" r="3" />
        <circle cx="12" cy="16" r="1" />
      </>
    )}
  </svg>
);

// ============================================================================
// CLIENTS - People with camera
// ============================================================================

export const ClientsIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <circle cx="9" cy="7" r="4" fill="currentColor" />
        <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" fill="currentColor" fillOpacity="0.5" />
        <path d="M17 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" strokeWidth="2" fill="none" />
        <circle cx="16" cy="7" r="4" fill="currentColor" fillOpacity="0.6" stroke="currentColor" strokeWidth="2" />
      </>
    ) : (
      <>
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </>
    )}
  </svg>
);

// ============================================================================
// VISITORS - Eye/View analytics
// ============================================================================

export const ViewfinderIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <path d="M12 5C5.636 5 2 12 2 12s3.636 7 10 7 10-7 10-7-3.636-7-10-7z" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="2" />
        <circle cx="12" cy="12" r="4" fill="currentColor" />
        <circle cx="12" cy="12" r="1.5" fill="white" />
        {/* Viewfinder corners */}
        <path d="M3 8V5h3M21 8V5h-3M3 16v3h3M21 16v3h-3" stroke="currentColor" strokeWidth="2" fill="none" />
      </>
    ) : (
      <>
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
        {/* Viewfinder corners */}
        <path d="M4 8V5h3M20 8V5h-3M4 16v3h3M20 16v3h-3" />
      </>
    )}
  </svg>
);

// ============================================================================
// SETTINGS - Modern gear with aperture blend
// ============================================================================

export const SettingsGearIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <circle cx="12" cy="12" r="3" fill="currentColor" />
        <path
          d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
        />
        <circle cx="12" cy="12" r="7" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="2" />
      </>
    ) : (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </>
    )}
  </svg>
);

// ============================================================================
// COMPANY PROFILE - Building with lens
// ============================================================================

export const StudioIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <rect x="4" y="2" width="16" height="20" rx="2" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="2" />
        <path d="M9 22v-4h6v4" fill="currentColor" fillOpacity="0.3" stroke="currentColor" strokeWidth="2" />
        <circle cx="12" cy="9" r="3" fill="currentColor" />
        <circle cx="12" cy="9" r="1" fill="white" />
      </>
    ) : (
      <>
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <path d="M9 22v-4h6v4" />
        <circle cx="12" cy="9" r="3" />
        <circle cx="12" cy="9" r="1" />
        <path d="M8 15h8" />
      </>
    )}
  </svg>
);

// ============================================================================
// USER PROFILE - Photographer icon
// ============================================================================

export const PhotographerIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <circle cx="12" cy="8" r="5" fill="currentColor" />
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" fill="currentColor" fillOpacity="0.5" stroke="currentColor" strokeWidth="2" />
        <rect x="9" y="3" width="6" height="4" rx="1" fill="currentColor" fillOpacity="0.3" stroke="currentColor" strokeWidth="1.5" />
      </>
    ) : (
      <>
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </>
    )}
  </svg>
);

// ============================================================================
// APP SETTINGS - Sliders with photo preview
// ============================================================================

export const EditSlidersIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <rect x="2" y="4" width="20" height="16" rx="2" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="2" />
        <line x1="6" y1="10" x2="6" y2="18" stroke="currentColor" strokeWidth="2" />
        <line x1="12" y1="6" x2="12" y2="14" stroke="currentColor" strokeWidth="2" />
        <line x1="18" y1="10" x2="18" y2="18" stroke="currentColor" strokeWidth="2" />
        <circle cx="6" cy="8" r="2" fill="currentColor" />
        <circle cx="12" cy="16" r="2" fill="currentColor" />
        <circle cx="18" cy="8" r="2" fill="currentColor" />
      </>
    ) : (
      <>
        <line x1="4" y1="21" x2="4" y2="14" />
        <line x1="4" y1="10" x2="4" y2="3" />
        <line x1="12" y1="21" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12" y2="3" />
        <line x1="20" y1="21" x2="20" y2="16" />
        <line x1="20" y1="12" x2="20" y2="3" />
        <line x1="1" y1="14" x2="7" y2="14" />
        <line x1="9" y1="8" x2="15" y2="8" />
        <line x1="17" y1="16" x2="23" y2="16" />
      </>
    )}
  </svg>
);

// ============================================================================
// COLLAPSE ICONS - Chevrons with photography flair
// ============================================================================

export const CollapseLeftIcon: FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polyline points="15 18 9 12 15 6" />
    <line x1="4" y1="6" x2="4" y2="18" />
  </svg>
);

export const CollapseRightIcon: FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polyline points="9 6 15 12 9 18" />
    <line x1="20" y1="6" x2="20" y2="18" />
  </svg>
);

// ============================================================================
// MORE/MENU - Modern dots
// ============================================================================

export const MoreDotsIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    stroke="none"
  >
    <circle cx="12" cy="12" r={filled ? 2.5 : 2} />
    <circle cx="5" cy="12" r={filled ? 2.5 : 2} />
    <circle cx="19" cy="12" r={filled ? 2.5 : 2} />
  </svg>
);

// ============================================================================
// UPLOAD - Camera with plus
// ============================================================================

export const UploadPhotoIcon: FC<IconProps> = ({ className, size = 20, filled }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={filled ? 0 : 2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {filled ? (
      <>
        <rect x="3" y="6" width="18" height="14" rx="2" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="2" />
        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2" fill="none" />
        <circle cx="12" cy="13" r="4" fill="currentColor" />
        <path d="M12 10v6M9 13h6" stroke="white" strokeWidth="1.5" />
      </>
    ) : (
      <>
        <rect x="3" y="6" width="18" height="14" rx="2" />
        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        <circle cx="12" cy="13" r="4" />
        <path d="M12 10v6M9 13h6" />
      </>
    )}
  </svg>
);

// ============================================================================
// CHEVRON - For expandable items
// ============================================================================

export const ChevronExpandIcon: FC<IconProps & { expanded?: boolean }> = ({
  className,
  size = 16,
  expanded
}) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{
      transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
      transition: 'transform 0.2s ease-out',
    }}
  >
    <polyline points="9 6 15 12 9 18" />
  </svg>
);

// ============================================================================
// LOGOUT - Exit with style
// ============================================================================

export const LogoutIcon: FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

export default {
  ApertureIcon,
  GalleryGridIcon,
  PhotoEnvelopeIcon,
  PhotoCalendarIcon,
  ClientsIcon,
  ViewfinderIcon,
  SettingsGearIcon,
  StudioIcon,
  PhotographerIcon,
  EditSlidersIcon,
  CollapseLeftIcon,
  CollapseRightIcon,
  MoreDotsIcon,
  UploadPhotoIcon,
  ChevronExpandIcon,
  LogoutIcon,
};
