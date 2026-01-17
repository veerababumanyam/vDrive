/**
 * SidebarNavItem Component
 * Premium navigation item with futuristic hover effects and smooth animations
 * Features neon glows, gradient indicators, and photography-inspired styling
 */

import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { usePrefersReducedMotion, useHaptic } from '../../hooks/useMobile';
import type { NavItem } from '../../types/workspace';
import { ChevronExpandIcon } from './icons/PhotographyIcons';

// ============================================================================
// TYPES
// ============================================================================

export interface SidebarNavItemProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  /** Navigation item data */
  item: NavItem;
  /** Whether this item is active */
  isActive: boolean;
  /** Whether sidebar is collapsed */
  isCollapsed: boolean;
  /** Depth level for nested items */
  depth?: number;
  /** Whether this is a parent with expanded children */
  isExpanded?: boolean;
  /** Click handler for expandable items */
  onToggleExpand?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export const SidebarNavItem = forwardRef<HTMLButtonElement, SidebarNavItemProps>(
  (
    {
      item,
      isActive,
      isCollapsed,
      depth = 0,
      isExpanded,
      onToggleExpand,
      className,
      ...props
    },
    ref
  ) => {
    const location = useLocation();
    const prefersReducedMotion = usePrefersReducedMotion();
    const haptic = useHaptic();
    const Icon = item.icon;

    const hasChildren = item.children && item.children.length > 0;
    const isChildActive =
      hasChildren &&
      item.children?.some((child) =>
        location.pathname.startsWith(child.href)
      );

    // Handle click with haptic feedback
    const handleClick = () => {
      if (haptic.isSupported) {
        haptic.light();
      }
      if (hasChildren && onToggleExpand) {
        onToggleExpand();
      }
    };

    // Base styles - Premium glassmorphism with WCAG 2.1 AA compliant contrast
    const baseStyles = cn(
      // Layout
      'group/navitem relative flex items-center w-full',
      'min-h-[48px]',
      depth === 0 ? 'px-3' : 'px-3 pl-10',
      isCollapsed ? 'justify-center px-3' : 'gap-3',

      // Rounded corners - more pronounced for modern look
      'rounded-2xl',

      // Transitions - smooth and sophisticated
      !prefersReducedMotion && 'transition-all duration-250 ease-out',

      // Default state - WCAG AA compliant: neutral-700 on white = 4.48:1, neutral-300 on dark = 7.21:1
      'text-neutral-700 dark:text-neutral-300',
      'bg-transparent',

      // Hover state - enhanced visibility
      'hover:bg-neutral-200/90 dark:hover:bg-white/[0.12]',
      'hover:text-neutral-900 dark:hover:text-white',
      !prefersReducedMotion && 'hover:translate-x-0.5',

      // Active state - High contrast with clear background
      isActive && [
        'bg-primary-100 dark:bg-primary-500/25',
        'text-primary-700 dark:text-primary-300',
        // Enhanced shadow for visual weight
        'shadow-sm dark:shadow-[0_0_20px_-5px_rgba(14,165,233,0.4)]',
      ],

      // Child active state (parent has active child)
      !isActive &&
        isChildActive && [
          'bg-neutral-100 dark:bg-white/[0.08]',
          'text-neutral-800 dark:text-neutral-200',
        ],

      // Touch feedback - spring-like press
      'active:scale-[0.97] active:bg-neutral-300/80 dark:active:bg-white/[0.15]',

      // Focus ring - accessible glow with high visibility
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600',
      'focus-visible:ring-offset-2 dark:focus-visible:ring-offset-warm-950',

      // Disabled - still readable
      item.disabled && 'opacity-50 pointer-events-none',

      className
    );

    // Icon container styles - with micro-animation
    const iconContainerStyles = cn(
      'relative flex-shrink-0',
      'flex items-center justify-center',
      isCollapsed ? 'w-6 h-6' : 'w-6 h-6',
      // Icon hover effect - subtle scale
      !prefersReducedMotion && 'transition-transform duration-200',
      !prefersReducedMotion && 'group-hover/navitem:scale-110',
      isActive && 'scale-105'
    );

    // Icon styles - WCAG AA compliant: 3:1 minimum for UI components
    const iconStyles = cn(
      'w-5 h-5',
      !prefersReducedMotion && 'transition-colors duration-200',
      isActive
        ? 'text-primary-600 dark:text-primary-300'
        : 'text-neutral-600 dark:text-neutral-400 group-hover/navitem:text-neutral-900 dark:group-hover/navitem:text-white'
    );

    // Label styles - elegant typography with WCAG AA contrast
    const labelStyles = cn(
      'flex-1 text-left text-sm font-medium tracking-wide',
      !prefersReducedMotion && 'transition-all duration-200',
      isCollapsed && 'sr-only',
      isActive && 'text-primary-800 dark:text-primary-200 font-semibold'
    );

    // Badge styles - modern pill with high contrast
    const badgeStyles = cn(
      'flex items-center justify-center',
      'min-w-[22px] h-[22px] px-2',
      'text-xs font-bold',
      'rounded-full',
      // High contrast backgrounds
      isActive
        ? 'bg-primary-600 dark:bg-primary-500 text-white shadow-sm'
        : 'bg-neutral-300 dark:bg-neutral-600 text-neutral-800 dark:text-neutral-100',
      !prefersReducedMotion && 'transition-all duration-200',
      'group-hover/navitem:scale-105'
    );

    // Chevron styles for expandable items - WCAG AA compliant
    const chevronStyles = cn(
      'flex-shrink-0 w-4 h-4',
      'text-neutral-600 dark:text-neutral-400',
      !prefersReducedMotion && 'transition-all duration-200',
      'group-hover/navitem:text-neutral-800 dark:group-hover/navitem:text-neutral-200'
    );

    // Active indicator - Gradient pill on the left
    const activeIndicator = isActive && (
      <span
        className={cn(
          'absolute left-0 top-1/2 -translate-y-1/2',
          'w-1 h-8 rounded-r-full',
          'bg-gradient-to-b from-primary-400 via-primary-500 to-accent-500',
          // Glow effect
          'shadow-[2px_0_8px_rgba(14,165,233,0.4)]',
          !prefersReducedMotion && 'animate-fade-in-scale'
        )}
      />
    );

    // Tooltip for collapsed state - Premium glass
    const tooltip = isCollapsed && (
      <span
        className={cn(
          'absolute left-full ml-3 z-50',
          'px-3 py-2',
          'text-xs font-medium text-white',
          // Glass tooltip
          'bg-neutral-900/95 dark:bg-neutral-800/95',
          'backdrop-blur-lg',
          'border border-white/10',
          'rounded-xl shadow-xl',
          'opacity-0 pointer-events-none translate-x-1',
          'group-hover/navitem:opacity-100 group-hover/navitem:translate-x-0',
          !prefersReducedMotion && 'transition-all duration-200',
          'whitespace-nowrap'
        )}
        role="tooltip"
      >
        {item.label}
        {item.badge !== undefined && (
          <span className="ml-2 px-1.5 py-0.5 bg-primary-500 rounded-full text-[10px]">
            {item.badge}
          </span>
        )}
      </span>
    );

    // Render as Link for navigation items without children
    if (!hasChildren) {
      return (
        <Link
          to={item.href}
          className={baseStyles}
          onClick={handleClick}
          aria-current={isActive ? 'page' : undefined}
          aria-disabled={item.disabled}
        >
          {activeIndicator}
          <span className={iconContainerStyles}>
            <Icon className={iconStyles} />
          </span>
          <span className={labelStyles}>{item.label}</span>
          {item.badge !== undefined && !isCollapsed && (
            <span className={badgeStyles}>{item.badge}</span>
          )}
          {tooltip}
        </Link>
      );
    }

    // Render as button for expandable items
    return (
      <button
        ref={ref}
        type="button"
        className={baseStyles}
        onClick={handleClick}
        aria-expanded={isExpanded}
        aria-controls={`nav-children-${item.id}`}
        aria-disabled={item.disabled}
        {...props}
      >
        {activeIndicator}
        <span className={iconContainerStyles}>
          <Icon className={iconStyles} />
        </span>
        <span className={labelStyles}>{item.label}</span>
        {item.badge !== undefined && !isCollapsed && (
          <span className={badgeStyles}>{item.badge}</span>
        )}
        {hasChildren && !isCollapsed && (
          <ChevronExpandIcon
            className={chevronStyles}
            expanded={isExpanded}
          />
        )}
        {tooltip}
      </button>
    );
  }
);

SidebarNavItem.displayName = 'SidebarNavItem';

// ============================================================================
// CHILD NAV ITEM - For nested navigation
// ============================================================================

export interface ChildNavItemProps {
  item: NavItem;
  isActive: boolean;
}

export function ChildNavItem({ item, isActive }: ChildNavItemProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();
  const Icon = item.icon;

  const handleClick = () => {
    if (haptic.isSupported) {
      haptic.light();
    }
  };

  return (
    <Link
      to={item.href}
      onClick={handleClick}
      className={cn(
        // Layout
        'group/childnav relative flex items-center gap-3 w-full',
        'min-h-[42px] pl-3 pr-3',
        'rounded-xl',

        // Transitions
        !prefersReducedMotion && 'transition-all duration-200 ease-out',

        // Default state - WCAG AA compliant
        'text-neutral-700 dark:text-neutral-300',

        // Hover state - enhanced visibility
        'hover:bg-neutral-200/80 dark:hover:bg-white/[0.10]',
        'hover:text-neutral-900 dark:hover:text-white',
        !prefersReducedMotion && 'hover:translate-x-0.5',

        // Active state - high contrast
        isActive && [
          'bg-primary-100 dark:bg-primary-500/20',
          'text-primary-700 dark:text-primary-300',
        ],

        // Touch feedback
        'active:scale-[0.98]',

        // Focus - high visibility
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600',

        // Disabled
        item.disabled && 'opacity-50 pointer-events-none'
      )}
      aria-current={isActive ? 'page' : undefined}
    >
      {/* Active dot indicator */}
      {isActive && (
        <span
          className={cn(
            'absolute left-0 top-1/2 -translate-y-1/2',
            'w-1.5 h-1.5 rounded-full',
            'bg-gradient-to-br from-primary-400 to-accent-500',
            'shadow-[0_0_6px_rgba(14,165,233,0.5)]',
            !prefersReducedMotion && 'animate-fade-in-scale'
          )}
        />
      )}

      {/* Icon - WCAG AA compliant */}
      <span className={cn(
        'flex-shrink-0',
        !prefersReducedMotion && 'transition-transform duration-200',
        'group-hover/childnav:scale-110'
      )}>
        <Icon
          className={cn(
            'w-4 h-4',
            !prefersReducedMotion && 'transition-colors duration-200',
            isActive
              ? 'text-primary-600 dark:text-primary-300'
              : 'text-neutral-600 dark:text-neutral-400 group-hover/childnav:text-neutral-800 dark:group-hover/childnav:text-neutral-200'
          )}
        />
      </span>

      {/* Label - WCAG AA compliant */}
      <span
        className={cn(
          'flex-1 text-sm font-medium',
          isActive && 'text-primary-800 dark:text-primary-200 font-semibold'
        )}
      >
        {item.label}
      </span>
    </Link>
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export default SidebarNavItem;
