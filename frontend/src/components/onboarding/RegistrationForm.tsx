/**
 * RegistrationForm Component
 * Complete registration form with validation and Turnstile integration
 *
 * T051: Create RegistrationForm component with Turnstile integration
 */

import { type FormEvent, useState } from 'react';
import { useRegistration } from '../../hooks/useRegistration';
import { AppButton } from '../ui/AppButton';
import { AppInput } from '../ui/AppInput';
import { AppCard } from '../ui/AppCard';
import { PasswordStrengthMeter } from './PasswordStrengthMeter';
import { GoogleOAuthButton } from './GoogleOAuthButton';
import { cn } from '../../lib/utils';

// ============================================
// Icons
// ============================================

function MailIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  );
}

function LockIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function UserIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
      <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
      <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
      <line x1="2" x2="22" y1="2" y2="22" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn('animate-spin', className)}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

// ============================================
// Component
// ============================================

export interface RegistrationFormProps {
  /** Callback when registration succeeds */
  onSuccess?: () => void;
  /** Additional class names */
  className?: string;
}

/**
 * Complete registration form with validation, password strength, and Turnstile
 *
 * @example
 * ```tsx
 * <RegistrationForm onSuccess={() => navigate('/verify-email')} />
 * ```
 */
export function RegistrationForm({
  onSuccess,
  className,
}: RegistrationFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    formData,
    updateField,
    errors,
    isValid,
    validateField,
    isCheckingEmail,
    emailAvailable,
    setTurnstileToken,
    isSubmitting,
    submit,
  } = useRegistration({
    onSuccess: () => {
      onSuccess?.();
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await submit();
  };

  // Email status indicator
  const getEmailStatus = () => {
    if (!formData.email) return null;
    if (errors.email) return null;
    if (isCheckingEmail) {
      return <LoaderIcon className="w-5 h-5 text-white/50" />;
    }
    if (emailAvailable === true) {
      return <CheckCircleIcon className="w-5 h-5 text-success-400" />;
    }
    return null;
  };

  return (
    <AppCard variant="glass" padding="lg" className={cn('w-full max-w-md', className)}>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-white mb-2">Create Account</h1>
        <p className="text-neutral-500 dark:text-white/60">
          Start your photography journey with RawDrive
        </p>
      </div>

      {/* OAuth Options */}
      <div className="space-y-3 mb-6">
        <GoogleOAuthButton fullWidth />
      </div>

      {/* Divider */}
      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-neutral-200 dark:border-white/10" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-white dark:bg-neutral-900/80 text-neutral-500 dark:text-white/50">
            or continue with email
          </span>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Full Name */}
        <AppInput
          label="Full Name"
          type="text"
          value={formData.fullName}
          onChange={(e) => updateField('fullName', e.target.value)}
          onBlur={() => validateField('fullName')}
          leftIcon={<UserIcon className="w-5 h-5" />}
          error={errors.fullName}
          autoComplete="name"
          required
        />

        {/* Email */}
        <AppInput
          label="Email"
          type="email"
          value={formData.email}
          onChange={(e) => updateField('email', e.target.value)}
          onBlur={() => validateField('email')}
          leftIcon={<MailIcon className="w-5 h-5" />}
          rightIcon={getEmailStatus()}
          error={errors.email}
          autoComplete="email"
          required
        />

        {/* Password */}
        <div className="space-y-2">
          <AppInput
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={formData.password}
            onChange={(e) => updateField('password', e.target.value)}
            onBlur={() => validateField('password')}
            leftIcon={<LockIcon className="w-5 h-5" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="p-1 hover:text-neutral-900 dark:hover:text-white transition-colors"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOffIcon className="w-5 h-5" />
                ) : (
                  <EyeIcon className="w-5 h-5" />
                )}
              </button>
            }
            error={errors.password}
            autoComplete="new-password"
            required
          />
          <PasswordStrengthMeter password={formData.password} compact />
        </div>

        {/* Confirm Password */}
        <AppInput
          label="Confirm Password"
          type={showConfirmPassword ? 'text' : 'password'}
          value={formData.confirmPassword}
          onChange={(e) => updateField('confirmPassword', e.target.value)}
          onBlur={() => validateField('confirmPassword')}
          leftIcon={<LockIcon className="w-5 h-5" />}
          rightIcon={
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="p-1 hover:text-neutral-900 dark:hover:text-white transition-colors"
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
            >
              {showConfirmPassword ? (
                <EyeOffIcon className="w-5 h-5" />
              ) : (
                <EyeIcon className="w-5 h-5" />
              )}
            </button>
          }
          error={errors.confirmPassword}
          autoComplete="new-password"
          required
        />

        {/* Turnstile Placeholder */}
        <TurnstileWidget
          siteKey={import.meta.env.VITE_TURNSTILE_SITE_KEY || ''}
          onVerify={setTurnstileToken}
          error={errors.turnstile}
        />

        {/* General Error */}
        {errors.general && (
          <div
            className="p-3 rounded-lg bg-error-500/10 dark:bg-error-500/20 border border-error-500/30 text-error-600 dark:text-error-400 text-sm"
            role="alert"
          >
            {errors.general}
          </div>
        )}

        {/* Submit Button */}
        <AppButton
          type="submit"
          variant="accent"
          size="lg"
          fullWidth
          isLoading={isSubmitting}
          disabled={!isValid || isSubmitting}
        >
          Create Account
        </AppButton>

        {/* Terms */}
        <p className="text-center text-xs text-neutral-400 dark:text-white/40">
          By creating an account, you agree to our{' '}
          <a href="/terms" className="text-primary-600 dark:text-primary-400 hover:underline">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="/privacy" className="text-primary-600 dark:text-primary-400 hover:underline">
            Privacy Policy
          </a>
        </p>
      </form>

      {/* Sign In Link */}
      <div className="mt-6 text-center">
        <span className="text-neutral-500 dark:text-white/60">Already have an account? </span>
        <a
          href="/login"
          className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors"
        >
          Sign in
        </a>
      </div>
    </AppCard>
  );
}

// ============================================
// Turnstile Widget (Placeholder)
// ============================================

interface TurnstileWidgetProps {
  siteKey: string;
  onVerify: (token: string | null) => void;
  error?: string;
}

/**
 * Cloudflare Turnstile widget
 * In production, this would use the actual Turnstile SDK
 */
function TurnstileWidget({ siteKey, onVerify, error }: TurnstileWidgetProps) {
  const [verified, setVerified] = useState(false);

  // In development without a site key, auto-verify
  const isDev = !siteKey || siteKey === 'development';

  const handleClick = () => {
    if (isDev) {
      setVerified(true);
      onVerify('dev-token');
    }
  };

  if (isDev) {
    return (
      <div className="space-y-2">
        <button
          type="button"
          onClick={handleClick}
          className={cn(
            'w-full p-4 rounded-xl border-2 border-dashed transition-all duration-200',
            verified
              ? 'border-success-500/50 bg-success-500/10'
              : 'border-neutral-300 dark:border-white/20 hover:border-neutral-400 dark:hover:border-white/30 bg-neutral-50 dark:bg-white/5'
          )}
        >
          <div className="flex items-center justify-center gap-2">
            {verified ? (
              <>
                <CheckCircleIcon className="w-5 h-5 text-success-500 dark:text-success-400" />
                <span className="text-success-600 dark:text-success-400 font-medium">Verified (Dev Mode)</span>
              </>
            ) : (
              <span className="text-neutral-500 dark:text-white/60">Click to verify (Dev Mode)</span>
            )}
          </div>
        </button>
        {error && (
          <p className="text-sm text-error-500 dark:text-error-400">{error}</p>
        )}
      </div>
    );
  }

  // Production Turnstile widget would be rendered here
  // using @cloudflare/turnstile-react or similar
  return (
    <div className="space-y-2">
      <div
        id="turnstile-widget"
        className="flex justify-center"
        data-sitekey={siteKey}
      >
        {/* Turnstile widget renders here */}
      </div>
      {error && (
        <p className="text-sm text-error-500 dark:text-error-400 text-center">{error}</p>
      )}
    </div>
  );
}

export default RegistrationForm;
