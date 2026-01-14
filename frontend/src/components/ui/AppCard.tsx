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
    'bg-white/5 border border-white/10 rounded-2xl',
    'backdrop-blur-sm'
  ),
  elevated: cn(
    'bg-white/10 border border-white/20 rounded-2xl',
    'backdrop-blur-xl',
    'shadow-glass'
  ),
  glass: cn(
    'bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl',
    'shadow-[0_8px_32px_rgba(0,0,0,0.12)]'
  ),
  outline: cn(
    'bg-transparent border border-white/20 rounded-2xl'
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
  'hover:border-white/30'
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
              'border-b border-white/10',
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
              'border-t border-white/10',
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
        'bg-gradient-to-br from-white/30 via-white/10 to-transparent',
        className
      )}
      {...props}
    >
      <div
        className={cn(
          'bg-neutral-900/80 backdrop-blur-xl rounded-2xl',
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
          'bg-white/10 backdrop-blur-xl border border-white/20',
          'rounded-2xl shadow-2xl shadow-black/20',
          'animate-fade-up',
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
