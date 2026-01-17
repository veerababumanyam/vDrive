/**
 * Workspace Hooks
 * Custom hooks for workspace navigation and state
 * Uses photography-specific icons for premium aesthetics
 */

import { useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useWorkspaceContext } from '../contexts/WorkspaceContext';
import type { NavItem, NavItemId, WorkspaceRole } from '../types/workspace';
import { hasRolePermission } from '../types/workspace';

// Import photography-specific icons
import {
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
  LogoutIcon,
  ChevronExpandIcon,
} from '../components/workspace/icons/PhotographyIcons';

// ============================================================================
// ICONS - Re-export photography icons for backward compatibility
// ============================================================================

interface IconProps {
  className?: string;
  size?: number | string;
}

// Map to new icons while keeping old names for compatibility
export const HomeIcon = ApertureIcon;
export const ImageIcon = GalleryGridIcon;
export const MailIcon = PhotoEnvelopeIcon;
export const CalendarIcon = PhotoCalendarIcon;
export const UsersIcon = ClientsIcon;
export const EyeIcon = ViewfinderIcon;
export const SettingsIcon = SettingsGearIcon;
export const BuildingIcon = StudioIcon;
export const UserIcon = PhotographerIcon;
export const SlidersIcon = EditSlidersIcon;
export const ChevronLeftIcon = CollapseLeftIcon;
export const ChevronRightIcon = CollapseRightIcon;
export const MoreHorizontalIcon = MoreDotsIcon;
export const LogOutIcon = LogoutIcon;

// Additional utility icons (keep original implementations)
export const MenuIcon = ({ className, size = 20 }: IconProps) => (
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
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </svg>
);

export const ChevronDownIcon = ({ className, size = 20 }: IconProps) => (
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
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

export const XIcon = ({ className, size = 20 }: IconProps) => (
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
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

export const PlusIcon = ({ className, size = 20 }: IconProps) => (
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
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

export const CheckIcon = ({ className, size = 20 }: IconProps) => (
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
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

// Re-export ChevronExpandIcon for use in other components
export { ChevronExpandIcon };

// ============================================================================
// NAVIGATION CONFIGURATION
// ============================================================================

/**
 * Main navigation items configuration
 */
export const NAV_ITEMS: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: HomeIcon,
    href: '/dashboard',
    showInMobileNav: true,
    shortcut: '⌘D',
  },
  {
    id: 'gallery',
    label: 'Gallery',
    icon: ImageIcon,
    href: '/galleries',
    showInMobileNav: true,
    shortcut: '⌘G',
  },
  {
    id: 'invitations',
    label: 'Invitations',
    icon: MailIcon,
    href: '/invitations',
    showInMobileNav: true,
    shortcut: '⌘I',
  },
  {
    id: 'calendar',
    label: 'Calendar',
    icon: CalendarIcon,
    href: '/calendar',
    showInMobileNav: true,
    shortcut: '⌘K',
  },
  {
    id: 'clients',
    label: 'Clients',
    icon: UsersIcon,
    href: '/clients',
    requiredRole: 'editor',
    showInMobileDrawer: true,
    shortcut: '⌘C',
  },
  {
    id: 'visitors',
    label: 'Visitors',
    icon: EyeIcon,
    href: '/visitors',
    requiredRole: 'admin',
    showInMobileDrawer: true,
    shortcut: '⌘V',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: SettingsIcon,
    href: '/settings',
    showInMobileDrawer: true,
    children: [
      {
        id: 'settings-company',
        label: 'Company Profile',
        icon: BuildingIcon,
        href: '/settings/company',
        requiredRole: 'admin',
      },
      {
        id: 'settings-profile',
        label: 'My Profile',
        icon: UserIcon,
        href: '/settings/profile',
      },
      {
        id: 'settings-app',
        label: 'App Settings',
        icon: SlidersIcon,
        href: '/settings/app',
      },
    ],
  },
];

// ============================================================================
// HOOKS
// ============================================================================

/**
 * Re-export the context hook for convenience
 */
export { useWorkspaceContext } from '../contexts/WorkspaceContext';

/**
 * Hook to get filtered navigation items based on user role
 */
export function useNavigation() {
  const { userRole, hasPermission } = useWorkspaceContext();
  const location = useLocation();
  const navigate = useNavigate();

  // Filter nav items by role
  const filteredNavItems = useMemo(() => {
    return filterNavItemsByRole(NAV_ITEMS, userRole);
  }, [userRole]);

  // Get mobile nav items (bottom bar)
  const mobileNavItems = useMemo(() => {
    return filteredNavItems.filter((item) => item.showInMobileNav);
  }, [filteredNavItems]);

  // Get mobile drawer items (settings, clients, visitors)
  const mobileDrawerItems = useMemo(() => {
    return filteredNavItems.filter(
      (item) => item.showInMobileDrawer || item.children
    );
  }, [filteredNavItems]);

  // Determine current page from location
  const currentPage = useMemo<NavItemId | undefined>(() => {
    const path = location.pathname;

    // Check exact matches first
    for (const item of NAV_ITEMS) {
      if (item.href === path) {
        return item.id;
      }
      // Check children
      if (item.children) {
        for (const child of item.children) {
          if (child.href === path) {
            return child.id;
          }
        }
      }
    }

    // Check prefix matches (e.g., /galleries/123 matches gallery)
    if (path.startsWith('/galleries')) return 'gallery';
    if (path.startsWith('/invitations')) return 'invitations';
    if (path.startsWith('/calendar')) return 'calendar';
    if (path.startsWith('/clients')) return 'clients';
    if (path.startsWith('/visitors')) return 'visitors';
    if (path.startsWith('/settings/company')) return 'settings-company';
    if (path.startsWith('/settings/profile')) return 'settings-profile';
    if (path.startsWith('/settings/app')) return 'settings-app';
    if (path.startsWith('/settings')) return 'settings';
    if (path.startsWith('/dashboard')) return 'dashboard';

    return undefined;
  }, [location.pathname]);

  // Check if a nav item is active
  const isNavItemActive = useCallback(
    (item: NavItem): boolean => {
      if (item.id === currentPage) return true;
      // Check if any child is active
      if (item.children) {
        return item.children.some((child) => child.id === currentPage);
      }
      return false;
    },
    [currentPage]
  );

  // Navigate to a page
  const navigateTo = useCallback(
    (pageId: NavItemId) => {
      const item = findNavItem(NAV_ITEMS, pageId);
      if (item && hasPermission(item.requiredRole ?? 'viewer')) {
        navigate(item.href);
      }
    },
    [navigate, hasPermission]
  );

  return {
    navItems: filteredNavItems,
    mobileNavItems,
    mobileDrawerItems,
    currentPage,
    isNavItemActive,
    navigateTo,
    hasPermission,
  };
}

/**
 * Hook for keyboard navigation shortcuts
 */
export function useNavShortcuts() {
  const { navigateTo } = useNavigation();

  // Register keyboard shortcuts
  // This could be expanded with useEffect to add global listeners
  const shortcuts = useMemo(
    () => ({
      dashboard: '⌘D',
      gallery: '⌘G',
      invitations: '⌘I',
      calendar: '⌘K',
      clients: '⌘C',
      visitors: '⌘V',
      settings: '⌘S',
    }),
    []
  );

  return { shortcuts, navigateTo };
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Filter navigation items by user role
 */
function filterNavItemsByRole(
  items: NavItem[],
  role: WorkspaceRole
): NavItem[] {
  return items
    .filter((item) => {
      if (!item.requiredRole) return true;
      return hasRolePermission(role, item.requiredRole);
    })
    .map((item) => ({
      ...item,
      children: item.children
        ? filterNavItemsByRole(item.children, role)
        : undefined,
    }));
}

/**
 * Find a nav item by ID (recursive)
 */
function findNavItem(items: NavItem[], id: NavItemId): NavItem | undefined {
  for (const item of items) {
    if (item.id === id) return item;
    if (item.children) {
      const found = findNavItem(item.children, id);
      if (found) return found;
    }
  }
  return undefined;
}

// ============================================================================
// EXPORTS
// ============================================================================

export type { IconProps };
