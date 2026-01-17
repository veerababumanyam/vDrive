/**
 * MobileBottomNav Component
 * Premium iOS-style bottom tab bar with glassmorphism and haptic feedback
 * Features smooth animations, gradient active states, and photography aesthetics
 */

import { type FC } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { usePrefersReducedMotion, useHaptic, useSafeArea } from '../../hooks/useMobile';
import { useNavigation } from '../../hooks/useWorkspace';
import { MoreDotsIcon } from './icons/PhotographyIcons';
import type { MobileBottomNavProps, NavItemId } from '../../types/workspace';

// ============================================================================
// CONSTANTS
// ============================================================================

const TAB_BAR_HEIGHT = 56; // Slightly taller for better touch targets

// ============================================================================
// COMPONENT
// ============================================================================

export const MobileBottomNav: FC<MobileBottomNavProps> = ({
  currentPage,
  onNavigate,
  onOpenDrawer,
  className,
}) => {
  const navigate = useNavigate();
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();
  const safeArea = useSafeArea();
  const { mobileNavItems } = useNavigation();

  // Handle tab press
  const handleTabPress = (item: { id: NavItemId; href: string }) => {
    if (haptic.isSupported) {
      haptic.light();
    }
    navigate(item.href);
    onNavigate(item.id);
  };

  // Handle more button press
  const handleMorePress = () => {
    if (haptic.isSupported) {
      haptic.medium();
    }
    onOpenDrawer();
  };

  // Container styles - Premium glassmorphism
  const containerStyles = cn(
    // Positioning
    'fixed bottom-0 inset-x-0 z-50',
    'lg:hidden',

    // Multi-layer glass effect
    'bg-gradient-to-t from-white/98 via-white/95 to-white/90',
    'dark:from-warm-950/98 dark:via-warm-950/95 dark:to-warm-950/90',
    'backdrop-blur-2xl',
    '[backdrop-filter:blur(40px)_saturate(200%)]',
    '[-webkit-backdrop-filter:blur(40px)_saturate(200%)]',

    // Border with subtle glow
    'border-t border-neutral-200/60 dark:border-white/[0.08]',

    // Premium shadow - upward glow effect
    'shadow-[0_-4px_30px_-5px_rgba(0,0,0,0.08)]',
    'dark:shadow-[0_-4px_40px_-5px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.03)]',

    className
  );

  // Tab bar inner styles
  const tabBarStyles = cn(
    'flex items-center justify-around',
    'px-2'
  );

  // Tab item styles
  const getTabStyles = (isActive: boolean) =>
    cn(
      'group/tab relative flex flex-col items-center justify-center',
      'flex-1 h-full',
      'min-w-[56px] max-w-[90px]',
      'py-1.5',
      'rounded-2xl',

      // Touch feedback - spring press
      'active:scale-[0.90]',

      // Transitions
      !prefersReducedMotion && 'transition-all duration-200 ease-out',

      // Hover/focus states (for accessibility)
      'focus-visible:outline-none focus-visible:bg-neutral-100/80 dark:focus-visible:bg-white/[0.08]',

      // Active state background - subtle gradient
      isActive && [
        'bg-gradient-to-b from-primary-500/10 to-transparent',
        'dark:from-primary-500/15 dark:to-transparent',
      ]
    );

  // Icon container with active state animation - WCAG enhanced
  const getIconContainerStyles = (isActive: boolean) =>
    cn(
      'relative flex items-center justify-center',
      'w-8 h-8 rounded-xl',
      !prefersReducedMotion && 'transition-all duration-200',
      // Scale up on active
      isActive && 'scale-110',
      // Enhanced background on active for visibility
      isActive && 'bg-primary-100 dark:bg-primary-500/25'
    );

  // Icon styles - WCAG AA compliant: 3:1 for UI components
  const getIconStyles = (isActive: boolean) =>
    cn(
      'w-6 h-6',
      !prefersReducedMotion && 'transition-all duration-200',
      isActive
        ? 'text-primary-600 dark:text-primary-300'
        : 'text-neutral-600 dark:text-neutral-400 group-hover/tab:text-neutral-800 dark:group-hover/tab:text-neutral-200'
    );

  // Label styles - WCAG AA compliant: 4.5:1 for text
  const getLabelStyles = (isActive: boolean) =>
    cn(
      'text-[10px] font-semibold mt-1 tracking-wide',
      !prefersReducedMotion && 'transition-colors duration-200',
      isActive
        ? 'text-primary-700 dark:text-primary-300'
        : 'text-neutral-700 dark:text-neutral-300'
    );

  // Active indicator dot - Premium neon glow
  const ActiveIndicator = () => (
    <span
      className={cn(
        'absolute -top-1 left-1/2 -translate-x-1/2',
        'w-5 h-1 rounded-full',
        'bg-gradient-to-r from-primary-400 via-primary-500 to-accent-500',
        // Neon glow
        'shadow-[0_2px_8px_rgba(14,165,233,0.5)]',
        !prefersReducedMotion && 'animate-fade-in-scale'
      )}
    />
  );

  return (
    <nav
      className={containerStyles}
      style={{
        paddingBottom: safeArea.bottom,
        height: TAB_BAR_HEIGHT + safeArea.bottom,
      }}
      role="navigation"
      aria-label="Mobile navigation"
    >
      <div className={tabBarStyles} style={{ height: TAB_BAR_HEIGHT }}>
        {/* Nav Items */}
        {mobileNavItems.slice(0, 4).map((item) => {
          const isActive = item.id === currentPage;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => handleTabPress(item)}
              className={getTabStyles(isActive)}
              aria-current={isActive ? 'page' : undefined}
              aria-label={item.label}
            >
              {/* Active indicator */}
              {isActive && <ActiveIndicator />}

              {/* Icon container */}
              <div className={getIconContainerStyles(isActive)}>
                <Icon className={getIconStyles(isActive)} />

                {/* Badge */}
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    className={cn(
                      'absolute -top-1 -right-1',
                      'flex items-center justify-center',
                      'min-w-[18px] h-[18px] px-1',
                      'text-[10px] font-bold text-white',
                      // Gradient badge
                      'bg-gradient-to-br from-rose-500 to-rose-600',
                      'rounded-full',
                      'shadow-lg shadow-rose-500/30',
                      // Pulse animation for new notifications
                      !prefersReducedMotion && item.badge > 0 && 'animate-pulse'
                    )}
                  >
                    {item.badge > 99 ? '99+' : item.badge}
                  </span>
                )}
              </div>

              {/* Label */}
              <span className={getLabelStyles(isActive)}>{item.label}</span>
            </button>
          );
        })}

        {/* More Button */}
        <button
          type="button"
          onClick={handleMorePress}
          className={getTabStyles(false)}
          aria-label="More options"
          aria-haspopup="dialog"
        >
          <div className={getIconContainerStyles(false)}>
            <MoreDotsIcon className={getIconStyles(false)} />
          </div>
          <span className={getLabelStyles(false)}>More</span>
        </button>
      </div>
    </nav>
  );
};

// ============================================================================
// DISPLAY NAME
// ============================================================================

MobileBottomNav.displayName = 'MobileBottomNav';

// ============================================================================
// EXPORTS
// ============================================================================

export { TAB_BAR_HEIGHT };
export default MobileBottomNav;
