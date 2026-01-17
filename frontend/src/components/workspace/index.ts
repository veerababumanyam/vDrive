/**
 * Workspace Components
 * Exports all workspace navigation components
 */

// Layout
export { WorkspaceLayout, MOBILE_BOTTOM_NAV_HEIGHT } from './WorkspaceLayout';
export { WorkspaceHeader, HEADER_HEIGHT_MOBILE, HEADER_HEIGHT_DESKTOP } from './WorkspaceHeader';
export { WorkspaceSidebar, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED } from './WorkspaceSidebar';

// Navigation Items
export { SidebarNavItem, ChildNavItem } from './SidebarNavItem';

// Dropdowns & Menus
export { WorkspaceSwitcher } from './WorkspaceSwitcher';
export { UserProfileMenu } from './UserProfileMenu';

// Mobile
export { MobileBottomNav, TAB_BAR_HEIGHT } from './MobileBottomNav';
export { MobileSettingsDrawer } from './MobileSettingsDrawer';

// Icons - Photography-specific icon set
export * from './icons/PhotographyIcons';

// Default export
export { WorkspaceLayout as default } from './WorkspaceLayout';
