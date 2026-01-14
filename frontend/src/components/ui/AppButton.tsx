import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface AppButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button visual variant */
  variant?: 'primary' | 'accent' | 'outline' | 'ghost' | 'destructive' | 'neon';
  /** Button size */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** Icon to display before text */
  leftIcon?: ReactNode;
  /** Icon to display after text */
  rightIcon?: ReactNode;
  /** Show loading spinner */
  isLoading?: boolean;
  /** Full width button */
  fullWidth?: boolean;
  /** Enable neon glow effect on hover */
  glowOnHover?: boolean;
}

const variants = {
  primary: cn(
    // Light mode
    'bg-primary-500 text-white hover:bg-primary-600',
    // Dark mode
    'dark:bg-primary-500 dark:hover:bg-primary-600',
    'focus-visible:ring-primary-500 focus-visible:ring-offset-neutral-50 dark:focus-visible:ring-offset-warm-950',
    'shadow-lg shadow-primary-500/20 hover:shadow-primary-500/30 dark:shadow-glow dark:hover:shadow-glow-lg'
  ),
  accent: cn(
    // Light mode
    'bg-accent-500 text-white hover:bg-accent-600',
    // Dark mode
    'dark:bg-accent-500 dark:hover:bg-accent-600',
    'focus-visible:ring-accent-500 focus-visible:ring-offset-neutral-50 dark:focus-visible:ring-offset-warm-950',
    'shadow-lg shadow-accent-500/20 hover:shadow-accent-500/40'
  ),
  outline: cn(
    // Light mode
    'bg-transparent border border-neutral-300 text-neutral-700',
    'hover:bg-neutral-100 hover:border-neutral-400',
    // Dark mode
    'dark:border-white/20 dark:text-white',
    'dark:hover:bg-white/10 dark:hover:border-white/30',
    'focus-visible:ring-neutral-500 dark:focus-visible:ring-white/50'
  ),
  ghost: cn(
    // Light mode
    'bg-transparent text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100',
    // Dark mode
    'dark:text-white/70 dark:hover:text-white dark:hover:bg-white/10'
  ),
  destructive: cn(
    'bg-error-500 text-white hover:bg-error-600',
    'focus-visible:ring-error-500 focus-visible:ring-offset-neutral-50 dark:focus-visible:ring-offset-warm-950',
    'shadow-lg shadow-error-500/20 hover:shadow-error-500/40'
  ),
  neon: cn(
    // Light mode - gradient
    'bg-gradient-to-r from-primary-500 to-accent-500 text-white',
    'hover:from-primary-600 hover:to-accent-600',
    // Shadow and glow
    'shadow-neon-primary hover:shadow-neon-accent',
    'focus-visible:ring-primary-500 focus-visible:ring-offset-neutral-50 dark:focus-visible:ring-offset-warm-950'
  ),
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm gap-1.5 min-h-[36px]',
  md: 'px-4 py-2.5 text-base gap-2 min-h-[44px]', // 44px for touch target
  lg: 'px-6 py-3 text-lg gap-2.5 min-h-[48px]',
  xl: 'px-8 py-4 text-lg gap-3 min-h-[56px]',
};

/**
 * Primary button component with Futuristic Glass styling
 * Enhanced with mobile-first design, touch targets, and haptic-ready states
 *
 * @example
 * ```tsx
 * <AppButton variant="accent" size="lg" leftIcon={<Sparkles />}>
 *   Get Started
 * </AppButton>
 * ```
 */
export const AppButton = forwardRef<HTMLButtonElement, AppButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      leftIcon,
      rightIcon,
      isLoading = false,
      fullWidth = false,
      glowOnHover = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center rounded-xl font-medium',
          'transition-all duration-200 ease-out',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
          // Active state with haptic-ready feedback
          'active:scale-[0.97]',
          // Touch-friendly - prevent text selection and highlight
          'select-none touch-manipulation',
          '-webkit-tap-highlight-color-transparent',
          // Variant
          variants[variant],
          // Size
          sizes[size],
          // Full width
          fullWidth && 'w-full',
          // Glow on hover effect
          glowOnHover && 'hover:shadow-neon-primary',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <LoadingSpinner className="w-5 h-5 animate-spin" />
            <span className="ml-2">Loading...</span>
          </>
        ) : (
          <>
            {leftIcon && (
              <span className="shrink-0" aria-hidden="true">
                {leftIcon}
              </span>
            )}
            {children}
            {rightIcon && (
              <span className="shrink-0" aria-hidden="true">
                {rightIcon}
              </span>
            )}
          </>
        )}
      </button>
    );
  }
);

AppButton.displayName = 'AppButton';

/** Loading spinner SVG */
function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

export default AppButton;
