/**
 * WorkspaceLayout Component
 * Main layout wrapper with header, sidebar, and mobile navigation
 * Provides consistent layout structure for all authenticated pages
 */

import { type FC } from 'react';
import { cn } from '../../lib/utils';
import { useBreakpoint, usePrefersReducedMotion, useSafeArea } from '../../hooks/useMobile';
import { useWorkspaceContext } from '../../contexts/WorkspaceContext';
import { useNavigation } from '../../hooks/useWorkspace';
import { WorkspaceHeader, HEADER_HEIGHT_MOBILE, HEADER_HEIGHT_DESKTOP } from './WorkspaceHeader';
import { WorkspaceSidebar, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED } from './WorkspaceSidebar';
import { MobileBottomNav } from './MobileBottomNav';
import { MobileSettingsDrawer } from './MobileSettingsDrawer';
import type { WorkspaceLayoutProps } from '../../types/workspace';

// ============================================================================
// CONSTANTS
// ============================================================================

const MOBILE_BOTTOM_NAV_HEIGHT = 49; // iOS standard tab bar height

// ============================================================================
// COMPONENT
// ============================================================================

export const WorkspaceLayout: FC<WorkspaceLayoutProps> = ({
  children,
  currentPage: currentPageProp,
  hideSidebar = false,
  pageTitle,
  className,
}) => {
  const { isMobile, isDesktop } = useBreakpoint();
  const prefersReducedMotion = usePrefersReducedMotion();
  const safeArea = useSafeArea();

  // Workspace context
  const {
    currentWorkspace,
    workspaces,
    switchWorkspace,
    userRole,
    sidebarCollapsed,
    toggleSidebar,
    mobileDrawerOpen,
    setMobileDrawerOpen,
    toggleMobileDrawer,
    settingsExpanded,
    toggleSettings,
  } = useWorkspaceContext();

  // Navigation
  const { currentPage: derivedCurrentPage, navigateTo } = useNavigation();

  // Use prop if provided, otherwise derive from URL
  const currentPage = currentPageProp ?? derivedCurrentPage;

  // Calculate sidebar width
  const sidebarWidth =
    hideSidebar || !isDesktop
      ? 0
      : sidebarCollapsed
      ? SIDEBAR_WIDTH_COLLAPSED
      : SIDEBAR_WIDTH_EXPANDED;

  // Calculate header height with safe area
  const headerHeight = isMobile
    ? HEADER_HEIGHT_MOBILE + safeArea.top
    : HEADER_HEIGHT_DESKTOP;

  // Calculate bottom nav height with safe area
  const bottomNavHeight = isMobile
    ? MOBILE_BOTTOM_NAV_HEIGHT + safeArea.bottom
    : 0;

  // Container styles
  const containerStyles = cn(
    'min-h-screen',
    'bg-neutral-50 dark:bg-warm-950',
    !prefersReducedMotion && 'transition-colors duration-300',
    className
  );

  // Main content styles
  const mainStyles = cn(
    'flex flex-col min-h-screen',
    !prefersReducedMotion && 'transition-all duration-300 ease-out'
  );

  // Content wrapper styles
  const contentWrapperStyles = cn(
    'flex-1',
    'overflow-auto'
  );

  return (
    <div className={containerStyles}>
      {/* Header */}
      <WorkspaceHeader
        workspace={currentWorkspace}
        workspaces={workspaces}
        currentPage={currentPage}
        pageTitle={pageTitle}
        onWorkspaceChange={switchWorkspace}
        onToggleMobileDrawer={toggleMobileDrawer}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={toggleSidebar}
      />

      {/* Desktop Sidebar */}
      {!hideSidebar && isDesktop && (
        <WorkspaceSidebar
          currentPage={currentPage}
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={toggleSidebar}
          userRole={userRole}
          settingsExpanded={settingsExpanded}
          onToggleSettings={toggleSettings}
        />
      )}

      {/* Main Content */}
      <main
        className={mainStyles}
        style={{
          paddingTop: headerHeight,
          paddingLeft: sidebarWidth,
          paddingBottom: bottomNavHeight,
        }}
      >
        <div className={contentWrapperStyles}>{children}</div>
      </main>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <MobileBottomNav
          currentPage={currentPage}
          onNavigate={navigateTo}
          onOpenDrawer={toggleMobileDrawer}
        />
      )}

      {/* Mobile Settings Drawer */}
      {isMobile && (
        <MobileSettingsDrawer
          isOpen={mobileDrawerOpen}
          onClose={() => setMobileDrawerOpen(false)}
          currentPage={currentPage}
          userRole={userRole}
          workspace={currentWorkspace}
          workspaces={workspaces}
          onWorkspaceChange={switchWorkspace}
        />
      )}
    </div>
  );
};

// ============================================================================
// DISPLAY NAME
// ============================================================================

WorkspaceLayout.displayName = 'WorkspaceLayout';

// ============================================================================
// EXPORTS
// ============================================================================

export { MOBILE_BOTTOM_NAV_HEIGHT };
export default WorkspaceLayout;
