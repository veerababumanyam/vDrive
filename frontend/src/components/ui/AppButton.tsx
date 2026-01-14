import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface AppButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button visual variant */
  variant?: 'primary' | 'accent' | 'outline' | 'ghost' | 'destructive';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Icon to display before text */
  leftIcon?: ReactNode;
  /** Icon to display after text */
  rightIcon?: ReactNode;
  /** Show loading spinner */
  isLoading?: boolean;
  /** Full width button */
  fullWidth?: boolean;
}

const variants = {
  primary: cn(
    'bg-primary-500 text-white hover:bg-primary-600',
    'focus-visible:ring-primary-500 focus-visible:ring-offset-neutral-950',
    'shadow-glow hover:shadow-glow-lg'
  ),
  accent: cn(
    'bg-accent-500 text-white hover:bg-accent-600',
    'focus-visible:ring-accent-500 focus-visible:ring-offset-neutral-950',
    'shadow-glow-accent hover:shadow-[0_0_50px_rgba(217,70,239,0.5)]'
  ),
  outline: cn(
    'bg-transparent border border-white/20 text-white',
    'hover:bg-white/10 hover:border-white/30',
    'focus-visible:ring-white/50'
  ),
  ghost: cn(
    'bg-transparent text-white/70 hover:text-white hover:bg-white/10'
  ),
  destructive: cn(
    'bg-error-500 text-white hover:bg-error-600',
    'focus-visible:ring-error-500 focus-visible:ring-offset-neutral-950'
  ),
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2.5 text-base gap-2',
  lg: 'px-6 py-3 text-lg gap-2.5',
};

/**
 * Primary button component with Futuristic Glass styling
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
          // Active state
          'active:scale-[0.98]',
          // Variant
          variants[variant],
          // Size
          sizes[size],
          // Full width
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <LoadingSpinner className="w-4 h-4 animate-spin" />
            <span>Loading...</span>
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
