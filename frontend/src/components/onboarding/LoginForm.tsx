/**
 * LoginForm Component
 * Sign-in form with email/password and OAuth options
 */

import { type FormEvent, useState } from 'react';
import { useLogin } from '../../hooks/useLogin';
import { AppButton } from '../ui/AppButton';
import { AppInput } from '../ui/AppInput';
import { AppCard } from '../ui/AppCard';
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

// ============================================
// Component
// ============================================

export interface LoginFormProps {
  /** Callback when login succeeds */
  onSuccess?: () => void;
  /** Additional class names */
  className?: string;
}

/**
 * Complete login form with email/password and OAuth options
 *
 * @example
 * ```tsx
 * <LoginForm onSuccess={() => navigate('/dashboard')} />
 * ```
 */
export function LoginForm({ onSuccess, className }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);

  const {
    formData,
    updateField,
    errors,
    isValid,
    validateField,
    isSubmitting,
    submit,
  } = useLogin({
    onSuccess: () => {
      onSuccess?.();
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await submit();
  };

  return (
    <AppCard variant="glass" padding="lg" className={cn('w-full max-w-md', className)}>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Welcome Back</h1>
        <p className="text-white/60">Sign in to continue to vDrive</p>
      </div>

      {/* OAuth Options */}
      <div className="space-y-3 mb-6">
        <GoogleOAuthButton fullWidth />
      </div>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-neutral-900/80 text-white/50">
            or continue with email
          </span>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Email */}
        <AppInput
          label="Email"
          type="email"
          value={formData.email}
          onChange={(e) => updateField('email', e.target.value)}
          onBlur={() => validateField('email')}
          leftIcon={<MailIcon className="w-5 h-5" />}
          error={errors.email}
          autoComplete="email"
          required
        />

        {/* Password */}
        <div className="space-y-1">
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
                className="p-1 hover:text-white transition-colors"
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
            autoComplete="current-password"
            required
          />

          {/* Forgot Password Link */}
          <div className="flex justify-end">
            <a
              href="/forgot-password"
              className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
            >
              Forgot password?
            </a>
          </div>
        </div>

        {/* General Error */}
        {errors.general && (
          <div
            className="p-3 rounded-lg bg-error-500/20 border border-error-500/30 text-error-400 text-sm"
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
          Sign In
        </AppButton>
      </form>

      {/* Register Link */}
      <div className="mt-6 text-center">
        <span className="text-white/60">Don't have an account? </span>
        <a
          href="/register"
          className="text-primary-400 hover:text-primary-300 font-medium transition-colors"
        >
          Create account
        </a>
      </div>
    </AppCard>
  );
}

export default LoginForm;
