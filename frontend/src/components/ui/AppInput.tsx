import {
  forwardRef,
  useState,
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
  /** Icon to display on the left */
  leftIcon?: ReactNode;
  /** Icon to display on the right */
  rightIcon?: ReactNode;
  /** Input size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Full width input */
  fullWidth?: boolean;
}

const sizes = {
  sm: 'px-3 py-2 text-sm',
  md: 'px-4 py-3 text-base',
  lg: 'px-5 py-4 text-lg',
};

const iconSizes = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

/**
 * Glass-styled input component with floating label support
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
      leftIcon,
      rightIcon,
      size = 'md',
      fullWidth = true,
      type = 'text',
      id,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const inputId = id || `input-${Math.random().toString(36).substring(2, 9)}`;
    const hasError = Boolean(error);
    const hasValue = Boolean(props.value || props.defaultValue);

    return (
      <div className={cn('relative', fullWidth && 'w-full')}>
        {/* Input container */}
        <div className="relative">
          {/* Left icon */}
          {leftIcon && (
            <div
              className={cn(
                'absolute left-4 top-1/2 -translate-y-1/2 text-white/50',
                iconSizes[size],
                isFocused && 'text-primary-400',
                hasError && 'text-error-400'
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
              'w-full rounded-xl border bg-white/5 backdrop-blur-sm',
              'text-white placeholder-white/40',
              'transition-all duration-200',
              // Focus styles
              'focus:outline-none focus:ring-2',
              // Default border
              'border-white/20',
              // Focus state
              !hasError && 'focus:border-primary-500 focus:ring-primary-500/20',
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
                'text-white/60',
                leftIcon && 'left-12',
                // Floating state
                (isFocused || hasValue)
                  ? 'top-2 text-xs'
                  : 'top-1/2 -translate-y-1/2 text-base',
                isFocused && 'text-primary-400',
                hasError && isFocused && 'text-error-400'
              )}
            >
              {label}
            </label>
          )}

          {/* Right icon */}
          {rightIcon && (
            <div
              className={cn(
                'absolute right-4 top-1/2 -translate-y-1/2 text-white/50',
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
            className="mt-2 text-sm text-error-400 flex items-center gap-1.5"
          >
            <ErrorIcon className="w-4 h-4 shrink-0" />
            {error}
          </p>
        )}

        {/* Helper text */}
        {helperText && !hasError && (
          <p
            id={`${inputId}-helper`}
            className="mt-2 text-sm text-white/50"
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

export default AppInput;
