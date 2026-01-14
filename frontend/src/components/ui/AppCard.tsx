import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface AppCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Card visual variant */
  variant?: 'default' | 'elevated' | 'glass' | 'outline';
  /** Enable hover effects */
  hoverable?: boolean;
  /** Card padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Header content */
  header?: ReactNode;
  /** Footer content */
  footer?: ReactNode;
}

const variants = {
  default: cn(
    // Light mode
    'bg-neutral-50 border border-neutral-200 rounded-2xl',
    'shadow-sm',
    // Dark mode
    'dark:bg-white/5 dark:border-white/10',
    'dark:backdrop-blur-sm dark:shadow-none'
  ),
  elevated: cn(
    // Light mode
    'bg-white border border-neutral-200 rounded-2xl',
    'shadow-lg shadow-neutral-200/60',
    // Dark mode
    'dark:bg-white/10 dark:border-white/20',
    'dark:backdrop-blur-xl dark:shadow-glass'
  ),
  glass: cn(
    // Light mode - clean white card with soft shadow
    'bg-white/95 border border-neutral-200/80 rounded-2xl',
    'shadow-xl shadow-neutral-300/40',
    // Dark mode - Apple iOS glass effect
    'dark:bg-white/[0.12] dark:border-white/25',
    'dark:shadow-[0_8px_40px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.1)]',
    // Common
    'backdrop-blur-xl transition-colors duration-300'
  ),
  outline: cn(
    // Light mode
    'bg-transparent border border-neutral-300 rounded-2xl',
    // Dark mode
    'dark:border-white/20'
  ),
};

const paddings = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

const hoverStyles = cn(
  'transition-all duration-300 ease-out',
  'hover:shadow-float hover:-translate-y-1',
  // Light mode
  'hover:border-neutral-300 hover:shadow-xl',
  // Dark mode
  'dark:hover:border-white/30'
);

/**
 * Glass-styled card component with multiple variants
 *
 * @example
 * ```tsx
 * <AppCard variant="glass" hoverable padding="lg">
 *   <h3>Card Title</h3>
 *   <p>Card content goes here</p>
 * </AppCard>
 * ```
 */
export const AppCard = forwardRef<HTMLDivElement, AppCardProps>(
  (
    {
      className,
      variant = 'default',
      hoverable = false,
      padding = 'md',
      header,
      footer,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          variants[variant],
          hoverable && hoverStyles,
          !header && !footer && paddings[padding],
          className
        )}
        {...props}
      >
        {/* Header */}
        {header && (
          <div
            className={cn(
              'border-b border-neutral-200 dark:border-white/10',
              padding !== 'none' && paddings[padding]
            )}
          >
            {header}
          </div>
        )}

        {/* Body */}
        <div className={cn((header || footer) && paddings[padding])}>
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div
            className={cn(
              'border-t border-neutral-200 dark:border-white/10',
              padding !== 'none' && paddings[padding]
            )}
          >
            {footer}
          </div>
        )}
      </div>
    );
  }
);

AppCard.displayName = 'AppCard';

/**
 * Glass card with gradient border glow effect
 */
export const GlassCard = forwardRef<
  HTMLDivElement,
  Omit<AppCardProps, 'variant'>
>(({ className, children, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        'relative p-[1px] rounded-2xl',
        // Light mode - subtle gradient border
        'bg-gradient-to-br from-neutral-300/50 via-neutral-200/30 to-transparent',
        // Dark mode - brighter gradient border
        'dark:from-white/30 dark:via-white/10 dark:to-transparent',
        className
      )}
      {...props}
    >
      <div
        className={cn(
          // Light mode
          'bg-white/95 backdrop-blur-xl rounded-2xl',
          // Dark mode
          'dark:bg-neutral-900/80',
          props.padding !== 'none' && paddings[props.padding || 'md']
        )}
      >
        {children}
      </div>
    </div>
  );
});

GlassCard.displayName = 'GlassCard';

/**
 * Floating glass panel - typically used for tooltips, dropdowns
 */
export const FloatingPanel = forwardRef<HTMLDivElement, AppCardProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          // Light mode
          'bg-white/95 backdrop-blur-xl border border-neutral-200',
          'shadow-2xl shadow-neutral-300/30',
          // Dark mode
          'dark:bg-white/10 dark:border-white/20',
          'dark:shadow-black/20',
          // Common
          'rounded-2xl animate-fade-up',
          paddings[props.padding || 'md'],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

FloatingPanel.displayName = 'FloatingPanel';

export default AppCard;
