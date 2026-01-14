import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface AppCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Card visual variant */
  variant?: 'default' | 'elevated' | 'glass' | 'premiumGlass' | 'outline' | 'neon';
  /** Enable hover effects */
  hoverable?: boolean;
  /** Card padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  /** Header content */
  header?: ReactNode;
  /** Footer content */
  footer?: ReactNode;
  /** Enable gradient border */
  gradientBorder?: boolean;
  /** Glow color for neon variant */
  glowColor?: 'primary' | 'accent' | 'success' | 'warning' | 'error';
}

const variants = {
  default: cn(
    // Light mode
    'bg-neutral-50 border border-neutral-200 rounded-2xl',
    'shadow-sm',
    // Dark mode
    'dark:bg-white/[0.06] dark:border-white/10',
    'dark:backdrop-blur-sm dark:shadow-none'
  ),
  elevated: cn(
    // Light mode
    'bg-white border border-neutral-200 rounded-2xl',
    'shadow-lg shadow-neutral-200/60',
    // Dark mode
    'dark:bg-white/[0.08] dark:border-white/15',
    'dark:backdrop-blur-xl dark:shadow-glass'
  ),
  glass: cn(
    // Light mode - clean white card with soft shadow
    'bg-white/90 border border-neutral-200/80 rounded-2xl sm:rounded-3xl',
    'shadow-xl shadow-neutral-300/40',
    // Dark mode - Apple iOS glass effect
    'dark:bg-white/[0.08] dark:border-white/20',
    'dark:shadow-[0_8px_40px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.08)]',
    // Common
    'backdrop-blur-xl transition-colors duration-300'
  ),
  premiumGlass: cn(
    // Light mode - higher opacity with iOS-style multi-layer shadows
    'bg-white/90 border border-neutral-200 rounded-2xl sm:rounded-3xl',
    'shadow-[0_2px_4px_rgba(0,0,0,0.1),0_8px_16px_rgba(0,0,0,0.2),0_16px_32px_rgba(0,0,0,0.15)]',
    'shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]',
    // Dark mode - enhanced glass with higher opacity (20%) and multi-layer shadows
    'dark:bg-white/[0.20] dark:border-white/[0.30]',
    'dark:shadow-[0_2px_4px_rgba(0,0,0,0.3),0_8px_20px_rgba(0,0,0,0.4),0_16px_40px_rgba(0,0,0,0.3)]',
    'dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]',
    // Common
    'backdrop-blur-xl transition-all duration-300'
  ),
  outline: cn(
    // Light mode
    'bg-transparent border border-neutral-300 rounded-2xl',
    // Dark mode
    'dark:border-white/20'
  ),
  neon: cn(
    // Light mode
    'bg-white/95 border border-primary-200 rounded-2xl sm:rounded-3xl',
    'shadow-glow-sm',
    // Dark mode - neon glow effect
    'dark:bg-white/[0.06] dark:border-primary-500/30',
    'dark:shadow-neon-primary',
    // Common
    'backdrop-blur-xl transition-all duration-300'
  ),
};

const paddings = {
  none: '',
  sm: 'p-3 sm:p-4',
  md: 'p-4 sm:p-6',
  lg: 'p-5 sm:p-8',
  xl: 'p-6 sm:p-10',
};

const hoverStyles = cn(
  'transition-all duration-300 ease-out',
  'hover:shadow-float hover:-translate-y-1',
  // Light mode
  'hover:border-neutral-300 hover:shadow-xl',
  // Dark mode
  'dark:hover:border-white/25 dark:hover:bg-white/[0.1]'
);

const glowColors = {
  primary: 'dark:hover:shadow-neon-primary',
  accent: 'dark:hover:shadow-neon-accent',
  success: 'dark:hover:shadow-neon-success',
  warning: 'dark:hover:shadow-neon-warning',
  error: 'dark:hover:shadow-neon-error',
};

/**
 * Glass-styled card component with multiple variants
 * Enhanced with mobile-first design and futuristic effects
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
      gradientBorder = false,
      glowColor,
      children,
      ...props
    },
    ref
  ) => {
    const cardContent = (
      <div
        ref={gradientBorder ? undefined : ref}
        className={cn(
          variants[variant],
          hoverable && hoverStyles,
          hoverable && glowColor && glowColors[glowColor],
          !header && !footer && paddings[padding],
          gradientBorder && 'rounded-[calc(1rem-1px)] sm:rounded-[calc(1.5rem-1px)]',
          className
        )}
        {...props}
      >
        {/* Header */}
        {header && (
          <div
            className={cn(
              'border-b border-neutral-200/80 dark:border-white/10',
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
              'border-t border-neutral-200/80 dark:border-white/10',
              padding !== 'none' && paddings[padding]
            )}
          >
            {footer}
          </div>
        )}
      </div>
    );

    // Wrap in gradient border if enabled
    if (gradientBorder) {
      return (
        <div
          ref={ref}
          className={cn(
            'relative p-[1px] rounded-2xl sm:rounded-3xl',
            // Light mode - subtle gradient border
            'bg-gradient-to-br from-neutral-300/60 via-neutral-200/40 to-transparent',
            // Dark mode - neon gradient border
            'dark:from-primary-500/40 dark:via-accent-500/20 dark:to-transparent'
          )}
        >
          {cardContent}
        </div>
      );
    }

    return cardContent;
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
