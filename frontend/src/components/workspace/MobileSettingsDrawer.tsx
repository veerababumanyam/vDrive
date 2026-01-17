/**
 * MobileSettingsDrawer Component
 * Slide-out drawer for mobile with extended navigation
 * iOS-inspired design with swipe gestures
 */

import { useEffect, useRef, type FC } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { useAuth } from '../../contexts/AuthContext';
import {
  usePrefersReducedMotion,
  useHaptic,
  useSafeArea,
  useSwipeGesture,
  useFocusTrap,
} from '../../hooks/useMobile';
import { useTheme } from '../../hooks/useTheme';
import {
  useNavigation,
  XIcon,
  ChevronRightIcon,
  LogOutIcon,
} from '../../hooks/useWorkspace';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';
import type { MobileSettingsDrawerProps } from '../../types/workspace';

// ============================================================================
// SUN/MOON ICONS
// ============================================================================

const SunIcon: FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </svg>
);

const MoonIcon: FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

// ============================================================================
// COMPONENT
// ============================================================================

export const MobileSettingsDrawer: FC<MobileSettingsDrawerProps> = ({
  isOpen,
  onClose,
  currentPage,
  userRole: _userRole,
  workspace,
  workspaces,
  onWorkspaceChange,
  className,
}) => {
  const navigate = useNavigate();
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();
  const safeArea = useSafeArea();
  const focusTrapRef = useFocusTrap(isOpen);
  const drawerRef = useRef<HTMLDivElement>(null);

  const { user, logout } = useAuth();
  const { resolvedTheme, setTheme } = useTheme();
  const { mobileDrawerItems } = useNavigation();

  // Swipe to close
  const swipeHandlers = useSwipeGesture(
    onClose, // swipe left to close
    undefined,
    undefined,
    undefined,
    50
  );

  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isOpen]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Handle navigation
  const handleNavigate = (href: string) => {
    if (haptic.isSupported) {
      haptic.light();
    }
    navigate(href);
    onClose();
  };

  // Handle logout
  const handleLogout = async () => {
    if (haptic.isSupported) {
      haptic.medium();
    }
    onClose();
    await logout();
    navigate('/signin');
  };

  // Handle theme toggle
  const handleToggleTheme = () => {
    if (haptic.isSupported) {
      haptic.light();
    }
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  // Get initials
  const getInitials = (): string => {
    if (!user) return '?';
    const first = user.first_name?.[0] || '';
    const last = user.last_name?.[0] || '';
    return (first + last).toUpperCase() || user.email[0].toUpperCase();
  };

  // Get display name
  const getDisplayName = (): string => {
    if (!user) return 'Guest';
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user.email.split('@')[0];
  };

  // Overlay styles
  const overlayStyles = cn(
    'fixed inset-0 z-50',
    'bg-black/40',
    'backdrop-blur-sm',
    !prefersReducedMotion && 'transition-opacity duration-300',
    isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
  );

  // Drawer styles
  const drawerStyles = cn(
    'fixed inset-y-0 right-0 z-50',
    'w-[85%] max-w-[320px]',
    'flex flex-col',

    // Glass effect
    'bg-white/95 dark:bg-warm-950/95',
    'backdrop-blur-2xl',
    '[backdrop-filter:blur(40px)_saturate(180%)]',
    '[-webkit-backdrop-filter:blur(40px)_saturate(180%)]',

    // Border & shadow
    'border-l border-neutral-200/50 dark:border-white/10',
    'shadow-2xl',

    // Transform
    !prefersReducedMotion && 'transition-transform duration-300 ease-out',
    isOpen ? 'translate-x-0' : 'translate-x-full',

    className
  );

  // Menu item styles
  const menuItemStyles = cn(
    'flex items-center gap-3 w-full',
    'min-h-[52px] px-4',
    'text-neutral-700 dark:text-neutral-200',
    'hover:bg-neutral-100 dark:hover:bg-white/[0.08]',
    'active:scale-[0.98]',
    !prefersReducedMotion && 'transition-all duration-150'
  );

  // Active menu item styles
  const activeMenuItemStyles = cn(
    menuItemStyles,
    'bg-primary-500/10 dark:bg-primary-500/20',
    'text-primary-600 dark:text-primary-400'
  );

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className={overlayStyles}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className={drawerStyles}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        {...swipeHandlers}
      >
        <div ref={focusTrapRef as React.RefObject<HTMLDivElement>} className="flex flex-col h-full">
          {/* Header */}
          <div
            className="flex items-center justify-between px-4 py-3 border-b border-neutral-200/50 dark:border-white/10"
            style={{ paddingTop: safeArea.top + 12 }}
          >
            <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
              Menu
            </h2>
            <button
              type="button"
              onClick={onClose}
              className={cn(
                'flex items-center justify-center',
                'w-9 h-9 rounded-full',
                'text-neutral-500 dark:text-neutral-400',
                'hover:bg-neutral-100 dark:hover:bg-white/[0.08]',
                'active:scale-[0.95]',
                !prefersReducedMotion && 'transition-all duration-150'
              )}
              aria-label="Close menu"
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>

          {/* User Profile */}
          <div className="px-4 py-4 border-b border-neutral-200/50 dark:border-white/10">
            <div className="flex items-center gap-3">
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt=""
                  className="w-12 h-12 rounded-full object-cover"
                />
              ) : (
                <div
                  className={cn(
                    'flex items-center justify-center',
                    'w-12 h-12 rounded-full',
                    'bg-gradient-to-br from-accent-400 to-accent-600',
                    'text-white font-semibold'
                  )}
                >
                  {getInitials()}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-base font-semibold text-neutral-900 dark:text-white truncate">
                  {getDisplayName()}
                </div>
                <div className="text-sm text-neutral-500 dark:text-neutral-400 truncate">
                  {user?.email}
                </div>
              </div>
            </div>
          </div>

          {/* Workspace Switcher */}
          <div className="px-4 py-3 border-b border-neutral-200/50 dark:border-white/10">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500 mb-2 block">
              Workspace
            </span>
            <WorkspaceSwitcher
              currentWorkspace={workspace}
              workspaces={workspaces}
              onSelect={(id) => {
                onWorkspaceChange(id);
                onClose();
              }}
            />
          </div>

          {/* Navigation Items */}
          <nav className="flex-1 overflow-y-auto py-2">
            <ul>
              {mobileDrawerItems.map((item) => {
                const isActive = item.id === currentPage;
                const Icon = item.icon;
                const hasChildren = item.children && item.children.length > 0;

                return (
                  <li key={item.id}>
                    {hasChildren ? (
                      <>
                        {/* Section header */}
                        <div className="px-4 pt-4 pb-2">
                          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                            {item.label}
                          </span>
                        </div>
                        {/* Children */}
                        <ul>
                          {item.children!.map((child) => {
                            const isChildActive = child.id === currentPage;
                            const ChildIcon = child.icon;

                            return (
                              <li key={child.id}>
                                <button
                                  type="button"
                                  onClick={() => handleNavigate(child.href)}
                                  className={
                                    isChildActive
                                      ? activeMenuItemStyles
                                      : menuItemStyles
                                  }
                                >
                                  <ChildIcon
                                    className={cn(
                                      'w-5 h-5 flex-shrink-0',
                                      isChildActive
                                        ? 'text-primary-500'
                                        : 'text-neutral-400 dark:text-neutral-500'
                                    )}
                                  />
                                  <span className="flex-1 text-left text-sm font-medium">
                                    {child.label}
                                  </span>
                                  <ChevronRightIcon className="w-4 h-4 text-neutral-400" />
                                </button>
                              </li>
                            );
                          })}
                        </ul>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleNavigate(item.href)}
                        className={isActive ? activeMenuItemStyles : menuItemStyles}
                      >
                        <Icon
                          className={cn(
                            'w-5 h-5 flex-shrink-0',
                            isActive
                              ? 'text-primary-500'
                              : 'text-neutral-400 dark:text-neutral-500'
                          )}
                        />
                        <span className="flex-1 text-left text-sm font-medium">
                          {item.label}
                        </span>
                        <ChevronRightIcon className="w-4 h-4 text-neutral-400" />
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Footer Actions */}
          <div
            className="border-t border-neutral-200/50 dark:border-white/10 p-4 space-y-2"
            style={{ paddingBottom: safeArea.bottom + 16 }}
          >
            {/* Theme Toggle */}
            <button
              type="button"
              onClick={handleToggleTheme}
              className={menuItemStyles}
            >
              {resolvedTheme === 'dark' ? (
                <SunIcon className="w-5 h-5 text-neutral-400 dark:text-neutral-500" />
              ) : (
                <MoonIcon className="w-5 h-5 text-neutral-400 dark:text-neutral-500" />
              )}
              <span className="flex-1 text-left text-sm font-medium">
                {resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
              </span>
            </button>

            {/* Logout */}
            <button
              type="button"
              onClick={handleLogout}
              className={cn(
                menuItemStyles,
                'text-red-600 dark:text-red-400',
                'hover:bg-red-50 dark:hover:bg-red-500/10'
              )}
            >
              <LogOutIcon className="w-5 h-5" />
              <span className="flex-1 text-left text-sm font-medium">
                Sign Out
              </span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

// ============================================================================
// DISPLAY NAME
// ============================================================================

MobileSettingsDrawer.displayName = 'MobileSettingsDrawer';

// ============================================================================
// EXPORTS
// ============================================================================

export default MobileSettingsDrawer;
