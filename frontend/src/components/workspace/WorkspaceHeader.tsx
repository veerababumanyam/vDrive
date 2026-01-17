/**
 * WorkspaceHeader Component
 * Futuristic, mobile-first sticky header with photography-inspired design
 * WCAG 2.1 AA compliant with proper contrast ratios
 * Features: glassmorphism, neon accents, micro-animations, camera-lens effects
 */

import { useState, useEffect, type FC } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';
import {
  useBreakpoint,
  usePrefersReducedMotion,
  useSafeArea,
  useScrollPosition,
  useHaptic,
} from '../../hooks/useMobile';
import { AppLogo } from '../ui/AppLogo';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';
import { UserProfileMenu } from './UserProfileMenu';
import type { WorkspaceHeaderProps } from '../../types/workspace';

// ============================================================================
// CONSTANTS
// ============================================================================

const HEADER_HEIGHT_MOBILE = 56;
const HEADER_HEIGHT_DESKTOP = 64;

// ============================================================================
// PHOTOGRAPHY ICONS - Modern, elegant camera-inspired icons
// Stroke width increased to 2 for better visibility (WCAG)
// ============================================================================

// Focus/Grid icon for gallery
const FocusGridIcon: FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
  </svg>
);

// Sparkle/AI icon for smart features
const SparkleIcon: FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
  >
    <path d="M12 1L13.8 9.2L22 11L13.8 12.8L12 21L10.2 12.8L2 11L10.2 9.2L12 1Z" />
    <path d="M19 14L20 18L24 19L20 20L19 24L18 20L14 19L18 18L19 14Z" />
  </svg>
);

// Lens/Search icon
const LensIcon: FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

// Notification bell with dot
const BellIcon: FC<{ className?: string; hasNotification?: boolean }> = ({
  className,
  hasNotification,
}) => (
  <div className="relative">
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
    {hasNotification && (
      <motion.span
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className={cn(
          'absolute -top-1 -right-1',
          'w-3 h-3 rounded-full',
          'bg-red-500',
          'border-2 border-white dark:border-warm-900',
          'shadow-sm'
        )}
        aria-label="You have notifications"
      />
    )}
  </div>
);

// ============================================================================
// ANIMATED MENU BUTTON - WCAG compliant with high contrast
// ============================================================================

const AnimatedMenuButton: FC<{
  isOpen: boolean;
  onClick: () => void;
  className?: string;
}> = ({ isOpen, onClick, className }) => {
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();

  const handleClick = () => {
    haptic.light();
    onClick();
  };

  return (
    <motion.button
      type="button"
      onClick={handleClick}
      className={cn(
        'relative flex items-center justify-center',
        'w-11 h-11 min-w-[44px] min-h-[44px]',
        'rounded-xl',
        // High contrast backgrounds
        'bg-neutral-100 dark:bg-neutral-800',
        'border border-neutral-300 dark:border-neutral-600',
        // High contrast text colors (4.5:1+ ratio)
        'text-neutral-700 dark:text-neutral-100',
        // Visible hover states
        'hover:bg-neutral-200 dark:hover:bg-neutral-700',
        'hover:border-accent-500 dark:hover:border-accent-400',
        'hover:text-accent-700 dark:hover:text-accent-300',
        // Strong focus ring (3:1+ ratio for UI components)
        'focus-visible:outline-none',
        'focus-visible:ring-2 focus-visible:ring-accent-600 dark:focus-visible:ring-accent-400',
        'focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-warm-950',
        'active:scale-[0.95]',
        !prefersReducedMotion && 'transition-all duration-200',
        className
      )}
      whileHover={!prefersReducedMotion ? { scale: 1.02 } : undefined}
      whileTap={!prefersReducedMotion ? { scale: 0.95 } : undefined}
      aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
      aria-expanded={isOpen}
    >
      <div className="relative w-5 h-5 flex flex-col items-center justify-center gap-1">
        <motion.span
          className="w-[18px] h-[2px] bg-current rounded-full origin-center"
          animate={isOpen ? { rotate: 45, y: 4 } : { rotate: 0, y: 0 }}
          transition={{ duration: 0.2 }}
        />
        <motion.span
          className="w-[14px] h-[2px] bg-current rounded-full"
          animate={isOpen ? { opacity: 0, x: -8 } : { opacity: 1, x: 0 }}
          transition={{ duration: 0.15 }}
        />
        <motion.span
          className="w-[18px] h-[2px] bg-current rounded-full origin-center"
          animate={isOpen ? { rotate: -45, y: -4 } : { rotate: 0, y: 0 }}
          transition={{ duration: 0.2 }}
        />
      </div>
    </motion.button>
  );
};

// ============================================================================
// QUICK ACTION BUTTON - WCAG compliant
// ============================================================================

const QuickActionButton: FC<{
  icon: FC<{ className?: string; hasNotification?: boolean }>;
  label: string;
  onClick?: () => void;
  hasNotification?: boolean;
  className?: string;
}> = ({ icon: Icon, label, onClick, hasNotification, className }) => {
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();

  const handleClick = () => {
    haptic.light();
    onClick?.();
  };

  return (
    <motion.button
      type="button"
      onClick={handleClick}
      className={cn(
        'relative flex items-center justify-center',
        'w-10 h-10 min-w-[44px] min-h-[44px]',
        'rounded-xl',
        'bg-transparent',
        // High contrast default colors
        'text-neutral-600 dark:text-neutral-300',
        // Visible hover with background
        'hover:bg-neutral-100 dark:hover:bg-neutral-800',
        'hover:text-neutral-900 dark:hover:text-white',
        // Strong focus ring
        'focus-visible:outline-none',
        'focus-visible:ring-2 focus-visible:ring-accent-600 dark:focus-visible:ring-accent-400',
        'focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-warm-950',
        'active:scale-[0.95]',
        !prefersReducedMotion && 'transition-all duration-200',
        className
      )}
      whileHover={!prefersReducedMotion ? { scale: 1.05 } : undefined}
      whileTap={!prefersReducedMotion ? { scale: 0.95 } : undefined}
      aria-label={label}
    >
      <Icon className="w-5 h-5" hasNotification={hasNotification} />
    </motion.button>
  );
};

// ============================================================================
// BREADCRUMB / PAGE INDICATOR - WCAG compliant
// ============================================================================

const PageIndicator: FC<{ title?: string }> = ({ title }) => {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (!title) return null;

  return (
    <motion.div
      initial={!prefersReducedMotion ? { opacity: 0, x: -10 } : false}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-3 px-3"
    >
      {/* Separator slash - higher contrast */}
      <span
        className="text-neutral-400 dark:text-neutral-500 font-medium"
        aria-hidden="true"
      >
        /
      </span>

      {/* Page title - high contrast text */}
      <h1 className={cn(
        'text-sm font-semibold',
        'text-neutral-700 dark:text-neutral-200',
        'truncate max-w-[200px]'
      )}>
        {title}
      </h1>
    </motion.div>
  );
};

// ============================================================================
// COMPONENT
// ============================================================================

export const WorkspaceHeader: FC<WorkspaceHeaderProps> = ({
  workspace,
  workspaces,
  currentPage: _currentPage,
  pageTitle,
  onWorkspaceChange,
  onToggleMobileDrawer,
  sidebarCollapsed: _sidebarCollapsed,
  onToggleSidebar: _onToggleSidebar,
  className,
}) => {
  const { isMobile, isDesktop } = useBreakpoint();
  const prefersReducedMotion = usePrefersReducedMotion();
  const safeArea = useSafeArea();
  const { isAtTop, direction } = useScrollPosition();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Track scroll state for header styling
  useEffect(() => {
    setIsScrolled(!isAtTop);
  }, [isAtTop]);

  // Hide header on scroll down (mobile only), show on scroll up
  const [isVisible, setIsVisible] = useState(true);
  useEffect(() => {
    if (isMobile) {
      setIsVisible(direction === 'up' || isAtTop);
    } else {
      setIsVisible(true);
    }
  }, [direction, isAtTop, isMobile]);

  // Toggle mobile drawer
  const handleToggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
    onToggleMobileDrawer?.();
  };

  // Header container styles - WCAG compliant with higher opacity backgrounds
  const headerStyles = cn(
    // Positioning
    'fixed top-0 inset-x-0 z-50',

    // Height
    isMobile ? 'h-14' : 'h-16',

    // Visibility transition on mobile
    !prefersReducedMotion && 'transition-all duration-300 ease-out',
    !isVisible && isMobile && '-translate-y-full',

    // Higher opacity backgrounds for readability (WCAG compliant)
    'bg-white/95 dark:bg-warm-950/95',
    'backdrop-blur-xl',
    '[backdrop-filter:blur(20px)_saturate(180%)]',
    '[-webkit-backdrop-filter:blur(20px)_saturate(180%)]',

    // Visible shadow for depth perception
    isScrolled
      ? [
          'shadow-lg shadow-neutral-200/50',
          'dark:shadow-lg dark:shadow-black/30',
        ]
      : 'shadow-sm shadow-neutral-100/50 dark:shadow-black/10',

    // Visible border
    'border-b',
    isScrolled
      ? 'border-neutral-200 dark:border-neutral-700'
      : 'border-neutral-100 dark:border-neutral-800',

    className
  );

  // Inner container styles
  const innerStyles = cn(
    'flex items-center h-full',
    'px-3 sm:px-4 lg:px-6',
    'gap-2 sm:gap-3 lg:gap-4'
  );

  // Logo section with hover effect
  const logoSectionStyles = cn(
    'flex items-center gap-2',
    'flex-shrink-0',
    'group',
    // Focus styles for accessibility
    'rounded-lg',
    'focus-visible:outline-none',
    'focus-visible:ring-2 focus-visible:ring-accent-600 dark:focus-visible:ring-accent-400',
    'focus-visible:ring-offset-2'
  );

  // Center section styles
  const centerSectionStyles = cn(
    'hidden md:flex items-center flex-1',
    'min-w-0'
  );

  // Right section styles
  const rightSectionStyles = cn(
    'flex items-center gap-1 sm:gap-2 lg:gap-3',
    'flex-shrink-0 ml-auto'
  );

  return (
    <motion.header
      className={headerStyles}
      style={{
        paddingTop: safeArea.top > 0 ? safeArea.top : undefined,
        height:
          safeArea.top > 0
            ? `calc(${isMobile ? HEADER_HEIGHT_MOBILE : HEADER_HEIGHT_DESKTOP}px + ${safeArea.top}px)`
            : undefined,
      }}
      role="banner"
      initial={!prefersReducedMotion ? { y: -100, opacity: 0 } : false}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* Accent gradient border on top - only on scroll for visual enhancement */}
      <div
        className={cn(
          'absolute inset-x-0 top-0 h-[2px]',
          'bg-gradient-to-r from-transparent via-accent-500 to-transparent',
          'opacity-0',
          isScrolled && 'opacity-60',
          !prefersReducedMotion && 'transition-opacity duration-500'
        )}
        aria-hidden="true"
      />

      <div className={innerStyles}>
        {/* Mobile Menu Button */}
        <div className="lg:hidden">
          <AnimatedMenuButton
            isOpen={mobileMenuOpen}
            onClick={handleToggleMobileMenu}
          />
        </div>

        {/* Logo Section */}
        <Link to="/dashboard" className={logoSectionStyles}>
          <motion.div
            whileHover={!prefersReducedMotion ? { scale: 1.05 } : undefined}
            whileTap={!prefersReducedMotion ? { scale: 0.95 } : undefined}
            className="relative"
          >
            {/* Subtle glow effect behind logo on hover */}
            <div
              className={cn(
                'absolute inset-0 -m-2 rounded-full',
                'bg-accent-400/30 dark:bg-accent-500/20 blur-xl',
                'opacity-0 group-hover:opacity-100',
                !prefersReducedMotion && 'transition-opacity duration-300'
              )}
              aria-hidden="true"
            />
            <AppLogo size={isMobile ? 'sm' : 'md'} />
          </motion.div>

          {/* Brand name - visible on larger screens with high contrast */}
          {!isMobile && (
            <motion.span
              initial={!prefersReducedMotion ? { opacity: 0, x: -10 } : false}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className={cn(
                'hidden sm:block',
                'text-lg font-bold tracking-tight',
                // Solid high-contrast colors instead of gradients for accessibility
                'text-neutral-900 dark:text-white'
              )}
            >
              RawDrive
            </motion.span>
          )}
        </Link>

        {/* Center Section - Page Title / Breadcrumb */}
        <div className={centerSectionStyles}>
          <PageIndicator title={pageTitle} />
        </div>

        {/* Right Section */}
        <div className={rightSectionStyles}>
          {/* Quick Search - Desktop only */}
          {isDesktop && (
            <motion.button
              initial={!prefersReducedMotion ? { opacity: 0, scale: 0.8 } : false}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.15 }}
              className={cn(
                'flex items-center gap-2',
                'h-9 px-3',
                'rounded-xl',
                // High contrast background
                'bg-neutral-100 dark:bg-neutral-800',
                'border border-neutral-300 dark:border-neutral-600',
                // High contrast text
                'text-sm text-neutral-600 dark:text-neutral-300',
                // Visible hover
                'hover:bg-neutral-200 dark:hover:bg-neutral-700',
                'hover:border-neutral-400 dark:hover:border-neutral-500',
                'hover:text-neutral-900 dark:hover:text-white',
                !prefersReducedMotion && 'transition-all duration-200',
                // Strong focus ring
                'focus-visible:outline-none',
                'focus-visible:ring-2 focus-visible:ring-accent-600 dark:focus-visible:ring-accent-400',
                'focus-visible:ring-offset-2',
                'cursor-pointer'
              )}
              aria-label="Search photos and galleries (⌘K)"
            >
              <LensIcon className="w-4 h-4" />
              <span className="hidden xl:inline font-medium">Search...</span>
              <kbd className={cn(
                'hidden xl:inline-flex items-center gap-0.5',
                'ml-2 px-1.5 py-0.5 rounded',
                'text-[10px] font-semibold',
                // High contrast kbd styling
                'bg-neutral-200 dark:bg-neutral-700',
                'text-neutral-600 dark:text-neutral-300',
                'border border-neutral-300 dark:border-neutral-600'
              )}>
                ⌘K
              </kbd>
            </motion.button>
          )}

          {/* Quick actions - Desktop only */}
          {isDesktop && (
            <motion.div
              initial={!prefersReducedMotion ? { opacity: 0 } : false}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="flex items-center gap-1"
            >
              {/* Grid view toggle */}
              <QuickActionButton
                icon={FocusGridIcon}
                label="Toggle grid view"
                onClick={() => {}}
              />

              {/* AI Features - accent color but still accessible */}
              <QuickActionButton
                icon={SparkleIcon}
                label="AI features"
                onClick={() => {}}
                className={cn(
                  'text-accent-600 dark:text-accent-400',
                  'hover:text-accent-700 dark:hover:text-accent-300',
                  'hover:bg-accent-50 dark:hover:bg-accent-900/30'
                )}
              />

              {/* Notifications */}
              <QuickActionButton
                icon={BellIcon}
                label="Notifications"
                hasNotification={true}
              />
            </motion.div>
          )}

          {/* Divider - Desktop only - more visible */}
          {isDesktop && (
            <div
              className="h-6 w-px bg-neutral-300 dark:bg-neutral-600 mx-1"
              aria-hidden="true"
            />
          )}

          {/* Workspace Switcher - Desktop only */}
          {isDesktop && (
            <motion.div
              initial={!prefersReducedMotion ? { opacity: 0, x: 20 } : false}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.25 }}
            >
              <WorkspaceSwitcher
                currentWorkspace={workspace}
                workspaces={workspaces}
                onSelect={onWorkspaceChange}
              />
            </motion.div>
          )}

          {/* User Profile Menu */}
          <motion.div
            initial={!prefersReducedMotion ? { opacity: 0, scale: 0.8 } : false}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
          >
            <UserProfileMenu />
          </motion.div>
        </div>
      </div>

      {/* Mobile search bar - slides in when tapped */}
      <AnimatePresence>
        {isMobile && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className={cn(
              'hidden', // Hidden by default, shown when search is active
              'px-4 pb-3',
              'border-t border-neutral-200 dark:border-neutral-700'
            )}
          >
            <div className={cn(
              'flex items-center gap-2',
              'h-10 px-3',
              'rounded-xl',
              // High contrast for mobile search
              'bg-neutral-100 dark:bg-neutral-800',
              'border border-neutral-300 dark:border-neutral-600'
            )}>
              <LensIcon className="w-4 h-4 text-neutral-500 dark:text-neutral-400" />
              <input
                type="text"
                placeholder="Search photos..."
                className={cn(
                  'flex-1 bg-transparent',
                  'text-sm font-medium',
                  'text-neutral-900 dark:text-white',
                  'placeholder:text-neutral-500 dark:placeholder:text-neutral-400',
                  'focus:outline-none'
                )}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
};

// ============================================================================
// DISPLAY NAME
// ============================================================================

WorkspaceHeader.displayName = 'WorkspaceHeader';

// ============================================================================
// EXPORTS
// ============================================================================

export { HEADER_HEIGHT_MOBILE, HEADER_HEIGHT_DESKTOP };
export default WorkspaceHeader;
