/**
 * UserProfileMenu Component
 * User avatar dropdown with profile actions
 * iOS-inspired design with glassmorphism
 */

import { useState, useRef, useEffect, useCallback, type FC } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { useAuth, type User } from '../../contexts/AuthContext';
import { usePrefersReducedMotion, useHaptic } from '../../hooks/useMobile';
import { useTheme } from '../../hooks/useTheme';
import {
  UserIcon,
  SettingsIcon,
  LogOutIcon,
  ChevronRightIcon,
} from '../../hooks/useWorkspace';
import type { UserProfileMenuProps } from '../../types/workspace';

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

export const UserProfileMenu: FC<UserProfileMenuProps> = ({ className }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();
  const navigate = useNavigate();

  const { user, logout } = useAuth();
  const { theme, resolvedTheme, setTheme } = useTheme();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () =>
        document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        buttonRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // Toggle dropdown
  const handleToggle = useCallback(() => {
    if (haptic.isSupported) {
      haptic.light();
    }
    setIsOpen((prev) => !prev);
  }, [haptic]);

  // Handle logout
  const handleLogout = useCallback(async () => {
    if (haptic.isSupported) {
      haptic.medium();
    }
    setIsOpen(false);
    await logout();
    navigate('/signin');
  }, [logout, navigate, haptic]);

  // Toggle theme
  const handleToggleTheme = useCallback(() => {
    if (haptic.isSupported) {
      haptic.light();
    }
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  }, [resolvedTheme, setTheme, haptic]);

  // Get user initials
  const getInitials = (user: User | null): string => {
    if (!user) return '?';
    const first = user.first_name?.[0] || '';
    const last = user.last_name?.[0] || '';
    return (first + last).toUpperCase() || user.email[0].toUpperCase();
  };

  // Get display name
  const getDisplayName = (user: User | null): string => {
    if (!user) return 'Guest';
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user.email.split('@')[0];
  };

  // Avatar styles
  const avatarStyles = cn(
    'flex items-center justify-center',
    'w-9 h-9 rounded-full',
    'bg-gradient-to-br from-accent-400 to-accent-600',
    'text-white text-sm font-semibold',
    'shadow-sm',
    'ring-2 ring-white/20 dark:ring-white/10'
  );

  // Trigger button styles
  const triggerStyles = cn(
    'relative',
    'rounded-full',
    'hover:ring-2 hover:ring-primary-500/30',
    !prefersReducedMotion && 'transition-all duration-200',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
    'active:scale-[0.95]',
    className
  );

  // Dropdown panel styles
  const dropdownStyles = cn(
    'absolute top-full right-0 mt-2 z-50',
    'w-[280px]',
    'p-2',

    // Glass effect
    'bg-white/95 dark:bg-warm-950/95',
    'backdrop-blur-2xl',
    '[backdrop-filter:blur(40px)_saturate(180%)]',
    '[-webkit-backdrop-filter:blur(40px)_saturate(180%)]',

    // Border & shadow
    'border border-neutral-200/60 dark:border-white/15',
    'rounded-2xl',
    'shadow-2xl shadow-neutral-300/30 dark:shadow-black/40',

    // Animation
    !prefersReducedMotion && ['animate-fade-in-up', 'origin-top-right']
  );

  // Menu item styles
  const menuItemStyles = cn(
    'flex items-center gap-3 w-full',
    'min-h-[44px] px-3',
    'rounded-xl',
    'text-neutral-700 dark:text-neutral-200',
    'hover:bg-neutral-100 dark:hover:bg-white/[0.08]',
    'active:scale-[0.98]',
    !prefersReducedMotion && 'transition-all duration-150',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
  );

  return (
    <div ref={dropdownRef} className="relative">
      {/* Avatar Button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        className={triggerStyles}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={`User menu for ${getDisplayName(user)}`}
      >
        {user?.avatar_url ? (
          <img
            src={user.avatar_url}
            alt=""
            className={cn(avatarStyles, 'object-cover')}
          />
        ) : (
          <div className={avatarStyles}>{getInitials(user)}</div>
        )}

        {/* Online indicator */}
        <span
          className={cn(
            'absolute bottom-0 right-0',
            'w-3 h-3 rounded-full',
            'bg-green-500',
            'border-2 border-white dark:border-warm-950'
          )}
          aria-hidden="true"
        />
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className={dropdownStyles} role="menu" aria-label="User menu">
          {/* User Info Header */}
          <div className="px-3 py-3 mb-1">
            <div className="flex items-center gap-3">
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt=""
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div
                  className={cn(
                    'flex items-center justify-center',
                    'w-10 h-10 rounded-full',
                    'bg-gradient-to-br from-accent-400 to-accent-600',
                    'text-white font-semibold'
                  )}
                >
                  {getInitials(user)}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-neutral-900 dark:text-white truncate">
                  {getDisplayName(user)}
                </div>
                <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
                  {user?.email}
                </div>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="my-1 border-t border-neutral-200/60 dark:border-white/10" />

          {/* Menu Items */}
          <ul className="space-y-0.5">
            {/* Profile */}
            <li>
              <Link
                to="/settings/profile"
                className={menuItemStyles}
                role="menuitem"
                onClick={() => setIsOpen(false)}
              >
                <UserIcon className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
                <span className="flex-1 text-sm font-medium">My Profile</span>
                <ChevronRightIcon className="w-4 h-4 text-neutral-400" />
              </Link>
            </li>

            {/* Settings */}
            <li>
              <Link
                to="/settings"
                className={menuItemStyles}
                role="menuitem"
                onClick={() => setIsOpen(false)}
              >
                <SettingsIcon className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
                <span className="flex-1 text-sm font-medium">Settings</span>
                <ChevronRightIcon className="w-4 h-4 text-neutral-400" />
              </Link>
            </li>

            {/* Theme Toggle */}
            <li>
              <button
                type="button"
                className={menuItemStyles}
                role="menuitem"
                onClick={handleToggleTheme}
              >
                {resolvedTheme === 'dark' ? (
                  <SunIcon className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
                ) : (
                  <MoonIcon className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
                )}
                <span className="flex-1 text-sm font-medium text-left">
                  {resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                </span>
                <span
                  className={cn(
                    'px-2 py-0.5 rounded-md text-xs font-medium',
                    'bg-neutral-100 dark:bg-white/10',
                    'text-neutral-500 dark:text-neutral-400'
                  )}
                >
                  {theme === 'system' ? 'System' : theme}
                </span>
              </button>
            </li>
          </ul>

          {/* Divider */}
          <div className="my-1 border-t border-neutral-200/60 dark:border-white/10" />

          {/* Logout */}
          <button
            type="button"
            className={cn(
              menuItemStyles,
              'text-red-600 dark:text-red-400',
              'hover:bg-red-50 dark:hover:bg-red-500/10'
            )}
            role="menuitem"
            onClick={handleLogout}
          >
            <LogOutIcon className="w-5 h-5" />
            <span className="flex-1 text-sm font-medium text-left">
              Sign Out
            </span>
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// DISPLAY NAME
// ============================================================================

UserProfileMenu.displayName = 'UserProfileMenu';

// ============================================================================
// EXPORTS
// ============================================================================

export default UserProfileMenu;
