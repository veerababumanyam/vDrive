/**
 * Workspace Types
 * Type definitions for workspace navigation and management
 */

import type { ComponentType } from 'react';

// ============================================================================
// WORKSPACE TYPES
// ============================================================================

/**
 * User role within a workspace
 * Hierarchy: owner > admin > editor > viewer
 */
export type WorkspaceRole = 'owner' | 'admin' | 'editor' | 'viewer';

/**
 * Role hierarchy for permission checking
 */
export const ROLE_HIERARCHY: Record<WorkspaceRole, number> = {
  owner: 4,
  admin: 3,
  editor: 2,
  viewer: 1,
};

/**
 * Check if a role has sufficient permissions
 */
export function hasRolePermission(
  userRole: WorkspaceRole,
  requiredRole: WorkspaceRole
): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

/**
 * Workspace data structure
 */
export interface Workspace {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
  role: WorkspaceRole;
  subscription_tier?: 'trial' | 'free' | 'pro' | 'business' | 'enterprise';
  trial_ends_at?: string;
  created_at?: string;
}

/**
 * Current workspace with additional context
 */
export interface CurrentWorkspace extends Workspace {
  isOwner: boolean;
  isAdmin: boolean;
  canEdit: boolean;
}

// ============================================================================
// NAVIGATION TYPES
// ============================================================================

/**
 * Navigation item identifiers
 */
export type NavItemId =
  | 'dashboard'
  | 'gallery'
  | 'invitations'
  | 'calendar'
  | 'clients'
  | 'visitors'
  | 'settings'
  | 'settings-company'
  | 'settings-profile'
  | 'settings-app';

/**
 * Icon component type
 */
export type IconComponent = ComponentType<{
  className?: string;
  size?: number | string;
}>;

/**
 * Navigation item configuration
 */
export interface NavItem {
  /** Unique identifier */
  id: NavItemId;
  /** Display label */
  label: string;
  /** Icon component */
  icon: IconComponent;
  /** Route path */
  href: string;
  /** Nested items (for settings) */
  children?: NavItem[];
  /** Minimum role required to view */
  requiredRole?: WorkspaceRole;
  /** Badge count for notifications */
  badge?: number;
  /** Whether this item is disabled */
  disabled?: boolean;
  /** Whether to show in mobile bottom nav */
  showInMobileNav?: boolean;
  /** Whether to show in mobile drawer */
  showInMobileDrawer?: boolean;
  /** Keyboard shortcut hint */
  shortcut?: string;
}

/**
 * Navigation section grouping
 */
export interface NavSection {
  /** Section title (optional) */
  title?: string;
  /** Items in this section */
  items: NavItem[];
}

// ============================================================================
// SIDEBAR STATE
// ============================================================================

/**
 * Sidebar collapse state
 */
export type SidebarState = 'expanded' | 'collapsed';

/**
 * Mobile drawer state
 */
export type DrawerState = 'open' | 'closed';

/**
 * Workspace layout state
 */
export interface WorkspaceLayoutState {
  sidebarState: SidebarState;
  mobileDrawerState: DrawerState;
  settingsExpanded: boolean;
}

// ============================================================================
// CONTEXT TYPES
// ============================================================================

/**
 * Workspace context value
 */
export interface WorkspaceContextValue {
  // Current workspace
  currentWorkspace: CurrentWorkspace | null;
  workspaces: Workspace[];
  isLoadingWorkspaces: boolean;
  workspacesError: Error | null;

  // Workspace operations
  switchWorkspace: (id: string) => Promise<void>;
  refreshWorkspaces: () => Promise<void>;

  // User role helpers
  userRole: WorkspaceRole;
  hasPermission: (requiredRole: WorkspaceRole) => boolean;

  // Sidebar state
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;

  // Mobile drawer state
  mobileDrawerOpen: boolean;
  setMobileDrawerOpen: (open: boolean) => void;
  toggleMobileDrawer: () => void;

  // Settings expanded state
  settingsExpanded: boolean;
  setSettingsExpanded: (expanded: boolean) => void;
  toggleSettings: () => void;
}

// ============================================================================
// COMPONENT PROPS
// ============================================================================

/**
 * WorkspaceLayout props
 */
export interface WorkspaceLayoutProps {
  children: React.ReactNode;
  /** Current page identifier for nav highlighting */
  currentPage?: NavItemId;
  /** Hide sidebar (for fullscreen pages) */
  hideSidebar?: boolean;
  /** Page title for header breadcrumb */
  pageTitle?: string;
  /** Additional class name */
  className?: string;
}

/**
 * WorkspaceHeader props
 */
export interface WorkspaceHeaderProps {
  /** Current workspace */
  workspace: CurrentWorkspace | null;
  /** All workspaces */
  workspaces: Workspace[];
  /** Current page for breadcrumb */
  currentPage?: NavItemId;
  /** Page title override */
  pageTitle?: string;
  /** Callback when workspace changes */
  onWorkspaceChange: (id: string) => Promise<void>;
  /** Callback to toggle mobile drawer */
  onToggleMobileDrawer?: () => void;
  /** Whether sidebar is collapsed (desktop) */
  sidebarCollapsed?: boolean;
  /** Callback to toggle sidebar */
  onToggleSidebar?: () => void;
  /** Additional class name */
  className?: string;
}

/**
 * WorkspaceSidebar props
 */
export interface WorkspaceSidebarProps {
  /** Current active page */
  currentPage?: NavItemId;
  /** Collapsed state */
  isCollapsed: boolean;
  /** Callback to toggle collapse */
  onToggleCollapse: () => void;
  /** User role for RBAC visibility */
  userRole: WorkspaceRole;
  /** Settings expanded state */
  settingsExpanded: boolean;
  /** Callback to toggle settings */
  onToggleSettings: () => void;
  /** Additional class name */
  className?: string;
}

/**
 * SidebarNavItem props
 */
export interface SidebarNavItemProps {
  /** Navigation item data */
  item: NavItem;
  /** Whether this item is active */
  isActive: boolean;
  /** Whether sidebar is collapsed */
  isCollapsed: boolean;
  /** Click handler */
  onClick?: () => void;
  /** Depth level for nested items */
  depth?: number;
  /** Additional class name */
  className?: string;
}

/**
 * WorkspaceSwitcher props
 */
export interface WorkspaceSwitcherProps {
  /** Current workspace */
  currentWorkspace: CurrentWorkspace | null;
  /** All workspaces */
  workspaces: Workspace[];
  /** Callback when workspace is selected */
  onSelect: (id: string) => void;
  /** Compact mode for collapsed sidebar */
  compact?: boolean;
  /** Additional class name */
  className?: string;
}

/**
 * UserProfileMenu props
 */
export interface UserProfileMenuProps {
  /** Additional class name */
  className?: string;
}

/**
 * MobileBottomNav props
 */
export interface MobileBottomNavProps {
  /** Current active page */
  currentPage?: NavItemId;
  /** Callback when nav item is clicked */
  onNavigate: (page: NavItemId) => void;
  /** Callback to open settings/more drawer */
  onOpenDrawer: () => void;
  /** Additional class name */
  className?: string;
}

/**
 * MobileSettingsDrawer props
 */
export interface MobileSettingsDrawerProps {
  /** Whether drawer is open */
  isOpen: boolean;
  /** Callback to close drawer */
  onClose: () => void;
  /** Current active page */
  currentPage?: NavItemId;
  /** User role for RBAC */
  userRole: WorkspaceRole;
  /** Current workspace */
  workspace: CurrentWorkspace | null;
  /** All workspaces */
  workspaces: Workspace[];
  /** Callback when workspace changes */
  onWorkspaceChange: (id: string) => void;
  /** Additional class name */
  className?: string;
}
