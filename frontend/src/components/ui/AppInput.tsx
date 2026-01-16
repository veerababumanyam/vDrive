import {
  forwardRef,
  useState,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
} from 'react';
import { cn } from '../../lib/utils';

export interface AppInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Label text for the input */
  label?: string;
  /** Helper text shown below the input */
  helperText?: string;
  /** Error message - shows error state when provided */
  error?: string;
  /** Success message - shows success state when provided */
  success?: string;
  /** Icon to display on the left */
  leftIcon?: ReactNode;
  /** Icon to display on the right */
  rightIcon?: ReactNode;
  /** Input size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Full width input */
  fullWidth?: boolean;
  /** Enable neon glow effect on focus */
  glowOnFocus?: boolean;
}

const sizes = {
  sm: 'px-3 py-2 text-sm min-h-[40px]',
  md: 'px-4 py-3 text-base min-h-[48px]', // 48px for comfortable touch target
  lg: 'px-5 py-4 text-lg min-h-[56px]',
};

const iconSizes = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

/**
 * Glass-styled input component with floating label support
 * Enhanced with mobile-first design and touch-friendly sizing
 *
 * @example
 * ```tsx
 * <AppInput
 *   label="Email"
 *   type="email"
 *   placeholder="you@example.com"
 *   leftIcon={<Mail />}
 *   error={errors.email}
 * />
 * ```
 */
export const AppInput = forwardRef<HTMLInputElement, AppInputProps>(
  (
    {
      className,
      label,
      helperText,
      error,
      success,
      leftIcon,
      rightIcon,
      size = 'md',
      fullWidth = true,
      glowOnFocus = false,
      type = 'text',
      id,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const generatedId = useId();
    const inputId = id || generatedId;
    const hasError = Boolean(error);
    const hasSuccess = Boolean(success);
    const hasValue = Boolean(props.value || props.defaultValue);

    return (
      <div className={cn('relative', fullWidth && 'w-full')}>
        {/* Input container */}
        <div className="relative">
          {/* Left icon */}
          {leftIcon && (
            <div
              className={cn(
                'absolute left-4 top-1/2 -translate-y-1/2',
                // Light mode
                'text-neutral-400',
                // Dark mode
                'dark:text-white/60',
                iconSizes[size],
                // Focus state
                isFocused && 'text-primary-500 dark:text-primary-400',
                // Error state
                hasError && 'text-error-500 dark:text-error-400'
              )}
              aria-hidden="true"
            >
              {leftIcon}
            </div>
          )}

          {/* Input element */}
          <input
            ref={ref}
            id={inputId}
            type={type}
            className={cn(
              // Base styles
              'w-full rounded-xl sm:rounded-2xl border transition-all duration-200',
              // Touch-friendly
              'touch-manipulation',
              // Light mode
              'bg-white text-neutral-900 placeholder-neutral-400',
              'border-neutral-300',
              // Dark mode - Apple iOS glass effect
              'dark:bg-white/[0.06] dark:backdrop-blur-xl',
              'dark:text-white dark:placeholder-white/40',
              'dark:border-white/20',
              'dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]',
              // Focus styles
              'focus:outline-none focus:ring-2',
              // Focus state (theme-aware)
              !hasError && !hasSuccess && 'focus:border-primary-500 focus:ring-primary-500/20',
              !hasError && !hasSuccess && glowOnFocus && 'dark:focus:shadow-glow-sm',
              // Success state
              hasSuccess && !hasError && 'border-success-500 focus:border-success-500 focus:ring-success-500/20',
              // Error state
              hasError && 'border-error-500 focus:border-error-500 focus:ring-error-500/20',
              // Size
              sizes[size],
              // Icon padding
              leftIcon && 'pl-12',
              rightIcon && 'pr-12',
              // Floating label padding
              label && 'pt-6 pb-2',
              className
            )}
            onFocus={(e) => {
              setIsFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              props.onBlur?.(e);
            }}
            aria-invalid={hasError}
            aria-describedby={
              hasError
                ? `${inputId}-error`
                : helperText
                ? `${inputId}-helper`
                : undefined
            }
            {...props}
          />

          {/* Floating label */}
          {label && (
            <label
              htmlFor={inputId}
              className={cn(
                'absolute left-4 transition-all duration-200 pointer-events-none',
                // Light mode
                'text-neutral-500',
                // Dark mode
                'dark:text-white/70',
                leftIcon && 'left-12',
                // Floating state
                (isFocused || hasValue)
                  ? 'top-2 text-xs'
                  : 'top-1/2 -translate-y-1/2 text-base',
                // Focus state (theme-aware)
                isFocused && 'text-primary-600 dark:text-primary-400',
                // Error state
                hasError && isFocused && 'text-error-500 dark:text-error-400'
              )}
            >
              {label}
            </label>
          )}

          {/* Right icon */}
          {rightIcon && (
            <div
              className={cn(
                'absolute right-4 top-1/2 -translate-y-1/2',
                // Light mode
                'text-neutral-400',
                // Dark mode
                'dark:text-white/60',
                iconSizes[size]
              )}
              aria-hidden="true"
            >
              {rightIcon}
            </div>
          )}
        </div>

        {/* Error message */}
        {hasError && (
          <p
            id={`${inputId}-error`}
            role="alert"
            className="mt-2 text-sm text-error-500 dark:text-error-400 flex items-center gap-1.5 animate-fade-in"
          >
            <ErrorIcon className="w-4 h-4 shrink-0" />
            {error}
          </p>
        )}

        {/* Success message */}
        {hasSuccess && !hasError && (
          <p
            className="mt-2 text-sm text-success-500 dark:text-success-400 flex items-center gap-1.5 animate-fade-in"
          >
            <SuccessIcon className="w-4 h-4 shrink-0" />
            {success}
          </p>
        )}

        {/* Helper text */}
        {helperText && !hasError && !hasSuccess && (
          <p
            id={`${inputId}-helper`}
            className="mt-2 text-sm text-neutral-500 dark:text-white/50"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

AppInput.displayName = 'AppInput';

/** Error icon SVG */
function ErrorIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/** Success icon SVG */
function SuccessIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export default AppInput;
