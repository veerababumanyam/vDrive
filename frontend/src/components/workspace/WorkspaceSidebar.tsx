/**
 * WorkspaceSidebar Component
 * Premium, futuristic desktop sidebar with glassmorphism and smooth animations
 * Mobile-first responsive design with photography-specific aesthetics
 */

import { useState, useCallback, type FC } from 'react';
import { cn } from '../../lib/utils';
import { usePrefersReducedMotion } from '../../hooks/useMobile';
import { useNavigation } from '../../hooks/useWorkspace';
import { SidebarNavItem, ChildNavItem } from './SidebarNavItem';
import { CollapseLeftIcon, CollapseRightIcon } from './icons/PhotographyIcons';
import type { WorkspaceSidebarProps } from '../../types/workspace';

// ============================================================================
// CONSTANTS
// ============================================================================

const SIDEBAR_WIDTH_EXPANDED = 260;
const SIDEBAR_WIDTH_COLLAPSED = 76;

// ============================================================================
// COMPONENT
// ============================================================================

export const WorkspaceSidebar: FC<WorkspaceSidebarProps> = ({
  currentPage,
  isCollapsed,
  onToggleCollapse,
  userRole: _userRole,
  settingsExpanded: _settingsExpanded,
  onToggleSettings: _onToggleSettings,
  className,
}) => {
  const prefersReducedMotion = usePrefersReducedMotion();
  const { navItems, isNavItemActive } = useNavigation();

  // Track which parent items are expanded (for items with children)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(() => {
    // Auto-expand settings if a child is active
    if (
      currentPage?.startsWith('settings-') ||
      currentPage === 'settings'
    ) {
      return new Set(['settings']);
    }
    return new Set();
  });

  // Toggle expansion of a nav item
  const toggleItemExpanded = useCallback((itemId: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  }, []);

  // Sidebar container styles - Premium glassmorphism
  const sidebarStyles = cn(
    // Positioning
    'fixed left-0 top-16 bottom-0 z-40',
    'hidden lg:flex flex-col',

    // Width transition
    !prefersReducedMotion && 'transition-all duration-300 ease-out',

    // Multi-layer glass effect
    'bg-gradient-to-b from-white/95 via-white/90 to-white/85',
    'dark:from-warm-950/95 dark:via-warm-950/90 dark:to-warm-950/85',
    'backdrop-blur-2xl',
    '[backdrop-filter:blur(40px)_saturate(180%)]',
    '[-webkit-backdrop-filter:blur(40px)_saturate(180%)]',

    // Premium border with gradient
    'border-r border-neutral-200/60 dark:border-white/[0.08]',

    // Sophisticated shadow system
    'shadow-[1px_0_20px_-5px_rgba(0,0,0,0.08)]',
    'dark:shadow-[1px_0_30px_-5px_rgba(0,0,0,0.4),inset_1px_0_0_rgba(255,255,255,0.03)]',

    className
  );

  // Logo/brand accent at top
  const brandAccentStyles = cn(
    'flex-shrink-0',
    'h-1 mx-4 mt-0 mb-2',
    'rounded-full',
    'bg-gradient-to-r from-primary-500/40 via-accent-500/60 to-primary-500/40',
    'dark:from-primary-500/30 dark:via-accent-500/50 dark:to-primary-500/30',
    !prefersReducedMotion && 'animate-pulse-slow'
  );

  // Nav section styles
  const navSectionStyles = cn(
    'flex-1 overflow-y-auto overflow-x-hidden',
    'py-3 px-3',
    // Premium scrollbar
    'scrollbar-thin scrollbar-thumb-neutral-300/50 dark:scrollbar-thumb-white/10',
    'scrollbar-track-transparent',
    'hover:scrollbar-thumb-neutral-400/50 dark:hover:scrollbar-thumb-white/20'
  );

  // Footer section styles (collapse toggle)
  const footerStyles = cn(
    'flex-shrink-0',
    'p-3',
    'border-t border-neutral-200/40 dark:border-white/[0.06]'
  );

  // Collapse button styles - WCAG AA compliant
  const collapseButtonStyles = cn(
    'group/collapse',
    'flex items-center justify-center gap-2',
    'w-full min-h-[48px]',
    'rounded-xl',

    // Base state - WCAG AA compliant contrast
    'text-neutral-700 dark:text-neutral-300',
    'bg-transparent',

    // Hover state - enhanced visibility
    'hover:bg-neutral-200/90 dark:hover:bg-white/[0.12]',
    'hover:text-neutral-900 dark:hover:text-white',

    // Active/pressed state
    'active:scale-[0.98] active:bg-neutral-300/80 dark:active:bg-white/[0.15]',

    // Transitions
    !prefersReducedMotion && 'transition-all duration-200 ease-out',

    // Focus ring - high visibility
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-offset-2',
    'dark:focus-visible:ring-offset-warm-950'
  );

  // Collapse icon container with rotation - WCAG enhanced
  const iconContainerStyles = cn(
    'flex items-center justify-center',
    'w-8 h-8 rounded-lg',
    'bg-transparent',
    'group-hover/collapse:bg-neutral-300/60 dark:group-hover/collapse:bg-white/[0.12]',
    !prefersReducedMotion && 'transition-all duration-200'
  );

  return (
    <aside
      style={{
        width: isCollapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED,
      }}
      className={sidebarStyles}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Brand accent line */}
      <div className={brandAccentStyles} />

      {/* Navigation Items */}
      <nav className={navSectionStyles}>
        <ul className="space-y-1.5" role="list">
          {navItems.map((item, index) => {
            const isActive = isNavItemActive(item);
            const isExpanded = expandedItems.has(item.id);
            const hasChildren = item.children && item.children.length > 0;

            return (
              <li
                key={item.id}
                className={cn(
                  !prefersReducedMotion && 'animate-fade-in-up',
                )}
                style={
                  !prefersReducedMotion
                    ? { animationDelay: `${index * 50}ms` }
                    : undefined
                }
              >
                <SidebarNavItem
                  item={item}
                  isActive={isActive && !hasChildren}
                  isCollapsed={isCollapsed}
                  isExpanded={isExpanded}
                  onToggleExpand={
                    hasChildren
                      ? () => toggleItemExpanded(item.id)
                      : undefined
                  }
                />

                {/* Render children if expanded and not collapsed */}
                {hasChildren && isExpanded && !isCollapsed && (
                  <ul
                    id={`nav-children-${item.id}`}
                    className={cn(
                      'mt-1 ml-3 space-y-0.5',
                      'border-l-2 border-neutral-200/50 dark:border-white/[0.08]',
                      'pl-2',
                      !prefersReducedMotion && 'animate-fade-in-up'
                    )}
                    role="list"
                  >
                    {item.children!.map((child, childIndex) => (
                      <li
                        key={child.id}
                        style={
                          !prefersReducedMotion
                            ? { animationDelay: `${childIndex * 30}ms` }
                            : undefined
                        }
                      >
                        <ChildNavItem
                          item={child}
                          isActive={child.id === currentPage}
                        />
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Collapse Toggle Footer */}
      <div className={footerStyles}>
        <button
          type="button"
          onClick={onToggleCollapse}
          className={collapseButtonStyles}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!isCollapsed}
        >
          <span className={iconContainerStyles}>
            {isCollapsed ? (
              <CollapseRightIcon className="w-4 h-4" />
            ) : (
              <CollapseLeftIcon className="w-4 h-4" />
            )}
          </span>
          {!isCollapsed && (
            <span className={cn(
              'text-sm font-medium',
              // Removed low opacity for WCAG AA compliance
              !prefersReducedMotion && 'transition-opacity duration-200'
            )}>
              Collapse
            </span>
          )}
        </button>
      </div>
    </aside>
  );
};

// ============================================================================
// DISPLAY NAME
// ============================================================================

WorkspaceSidebar.displayName = 'WorkspaceSidebar';

// ============================================================================
// EXPORTS
// ============================================================================

export { SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED };
export default WorkspaceSidebar;
