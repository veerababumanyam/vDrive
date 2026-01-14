/**
 * VerifyEmail Page
 * Email verification page with resend functionality
 * Enhanced with mobile-first futuristic design, safe areas, and haptic feedback
 *
 * T053: Create VerifyEmail page for verification link handling
 * T100: Add resend button to VerifyEmail page
 * T101: Add expired link UI with resend option
 */

import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { onboardingApi } from '../services/onboarding-api';
import { AppButton } from '../components/ui/AppButton';
import { AppCard } from '../components/ui/AppCard';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { cn } from '../lib/utils';
import { useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';
import { AppLogo } from '../components/ui/AppLogo';

// ============================================
// Icons
// ============================================

function MailIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function XCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="m15 9-6 6" />
      <path d="m9 9 6 6" />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 21h5v-5" />
    </svg>
  );
}


// ============================================
// Futuristic Background Components
// ============================================

function MorphingBlob({ className }: { className?: string }) {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        'absolute rounded-full blur-3xl opacity-30',
        !prefersReducedMotion && 'animate-morph',
        className
      )}
    />
  );
}

function ParticleEffect() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) return null;

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-primary-400/25 dark:bg-primary-400/15"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `float ${6 + Math.random() * 4}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 5}s`,
          }}
        />
      ))}
    </div>
  );
}

// ============================================
// Types
// ============================================

type VerificationStatus = 'pending' | 'verifying' | 'success' | 'expired' | 'error';

// ============================================
// Page Component
// ============================================

export function VerifyEmailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const email = searchParams.get('email') || localStorage.getItem('pending_email') || '';

  const [status, setStatus] = useState<VerificationStatus>(token ? 'verifying' : 'pending');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [resendCooldown, setResendCooldown] = useState(0);

  // Mobile-first hooks
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();
  const safeArea = useSafeArea();

  // Verify email token
  const verifyMutation = useMutation({
    mutationFn: () => onboardingApi.verifyEmail(token!),
    onSuccess: (data) => {
      if (data.success) {
        haptic.success();
        setStatus('success');
        // Redirect to workspace setup after delay
        setTimeout(() => {
          navigate('/onboarding/workspace');
        }, 2000);
      } else {
        haptic.error();
        setStatus('error');
        setErrorMessage(data.message);
      }
    },
    onError: (error: { message?: string; error?: string }) => {
      haptic.error();
      const message = error.message || 'Verification failed';
      if (message.toLowerCase().includes('expired')) {
        setStatus('expired');
      } else {
        setStatus('error');
      }
      setErrorMessage(message);
    },
  });

  // Resend verification email
  const resendMutation = useMutation({
    mutationFn: () => onboardingApi.resendVerification(email),
    onSuccess: () => {
      haptic.success();
      // Start cooldown timer (60 seconds)
      setResendCooldown(60);
    },
    onError: (error: { message?: string }) => {
      haptic.error();
      setErrorMessage(error.message || 'Failed to resend email');
    },
  });

  // Verify on mount if token present
  useEffect(() => {
    if (token && status === 'verifying') {
      verifyMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Only run on mount when token is present
  }, [token, status]);

  // Cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleResend = useCallback(() => {
    if (!email || resendCooldown > 0) return;
    haptic.medium();
    resendMutation.mutate();
  }, [email, resendCooldown, haptic, resendMutation]);

  const handleBackToRegister = useCallback(() => {
    haptic.light();
    navigate('/register');
  }, [haptic, navigate]);

  return (
    <div
      className="min-h-screen-dynamic flex flex-col items-center justify-center bg-neutral-50 dark:bg-warm-950 transition-colors duration-300 relative overflow-hidden px-4 sm:px-6"
      style={{
        paddingTop: `calc(1.5rem + ${safeArea.top}px)`,
        paddingBottom: `calc(1.5rem + ${safeArea.bottom}px)`,
      }}
    >
      {/* Theme-Aware Background with Futuristic Effects */}
      <div className="auth-bg">
        <div className="aurora-orb" />
        <MorphingBlob className="w-[500px] h-[500px] bg-gradient-to-br from-primary-500/15 to-accent-500/15 -top-64 -left-64" />
        <MorphingBlob className="w-80 h-80 bg-accent-500/10 bottom-20 right-10" />
      </div>
      <ParticleEffect />

      {/* Theme Toggle */}
      <div
        className="fixed right-6 z-50 touch-target"
        style={{ top: `calc(1.5rem + ${safeArea.top}px)` }}
      >
        <ThemeToggle />
      </div>

      {/* Logo */}
      <a
        href="/"
        className={cn(
          "flex items-center gap-3 mb-8 group",
          !prefersReducedMotion && "animate-fade-in-down"
        )}
      >
        <AppLogo size="md" />
        <span className="text-2xl font-bold text-neutral-900 dark:text-white">vDrive</span>
      </a>

      <AppCard
        variant="glass"
        padding="lg"
        className={cn(
          "w-full max-w-md text-center relative z-10",
          !prefersReducedMotion && "animate-fade-in-scale"
        )}
      >
        {/* Pending State - Waiting for user to check email */}
        {status === 'pending' && (
          <>
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className={cn(
                "absolute inset-0 rounded-full bg-primary-500/20",
                !prefersReducedMotion && "animate-pulse"
              )} />
              <div className="absolute inset-2 rounded-full bg-primary-500/10 flex items-center justify-center">
                <MailIcon className="w-10 h-10 text-primary-500 dark:text-primary-400" />
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white mb-3">Check your email</h1>
            <p className="text-neutral-600 dark:text-white/60 mb-6">
              We've sent a verification link to
              {email && (
                <span className="block text-neutral-900 dark:text-white font-medium mt-2 px-4 py-2 rounded-xl bg-neutral-100 dark:bg-white/[0.08] text-sm break-all">
                  {email}
                </span>
              )}
            </p>

            <div className="space-y-4">
              <p className="text-sm text-neutral-500 dark:text-white/50">
                Click the link in the email to verify your account.
              </p>

              {/* Resend Button */}
              <div className="pt-4 border-t border-neutral-200 dark:border-white/10">
                <p className="text-sm text-neutral-500 dark:text-white/50 mb-4">
                  Didn't receive the email?
                </p>
                <AppButton
                  variant="outline"
                  onClick={handleResend}
                  isLoading={resendMutation.isPending}
                  disabled={resendCooldown > 0 || !email}
                  leftIcon={<RefreshIcon className="w-4 h-4" />}
                  fullWidth
                  className="touch-target min-h-touch"
                >
                  {resendCooldown > 0
                    ? `Resend in ${resendCooldown}s`
                    : 'Resend email'}
                </AppButton>
                {resendMutation.isSuccess && (
                  <p className={cn(
                    "text-sm text-success-500 dark:text-success-400 mt-3",
                    !prefersReducedMotion && "animate-fade-in"
                  )}>
                    Email sent! Check your inbox.
                  </p>
                )}
              </div>
            </div>
          </>
        )}

        {/* Verifying State */}
        {status === 'verifying' && (
          <>
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className={cn(
                "absolute inset-0 rounded-full bg-primary-500/20",
                !prefersReducedMotion && "animate-pulse"
              )} />
              <div className="absolute inset-2 rounded-full flex items-center justify-center">
                <div className="w-10 h-10 border-4 border-primary-500/30 dark:border-primary-400/30 border-t-primary-500 dark:border-t-primary-400 rounded-full animate-spin" />
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white mb-3">Verifying...</h1>
            <p className="text-neutral-600 dark:text-white/60">Please wait while we verify your email.</p>
          </>
        )}

        {/* Success State */}
        {status === 'success' && (
          <>
            <div
              className={cn(
                'relative w-20 h-20 mx-auto mb-6',
                !prefersReducedMotion && 'animate-fade-in-up'
              )}
            >
              <div className="absolute inset-0 rounded-full bg-success-500/20" />
              <div className="absolute inset-2 rounded-full bg-success-500/10 flex items-center justify-center">
                <CheckCircleIcon className="w-10 h-10 text-success-500 dark:text-success-400" />
              </div>
              {/* Success glow effect */}
              <div className="absolute inset-0 rounded-full bg-success-500/30 blur-xl animate-pulse" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white mb-3">Email verified!</h1>
            <p className="text-neutral-600 dark:text-white/60 mb-6">
              Your email has been successfully verified.
            </p>
            <div className="flex items-center justify-center gap-2 text-sm text-neutral-500 dark:text-white/50">
              <div className="w-4 h-4 border-2 border-neutral-400 dark:border-white/40 border-t-transparent rounded-full animate-spin" />
              <span>Redirecting to workspace setup...</span>
            </div>
          </>
        )}

        {/* Expired State (T101) */}
        {status === 'expired' && (
          <>
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full bg-warning-500/20" />
              <div className="absolute inset-2 rounded-full bg-warning-500/10 flex items-center justify-center">
                <ClockIcon className="w-10 h-10 text-warning-500 dark:text-warning-400" />
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white mb-3">Link expired</h1>
            <p className="text-neutral-600 dark:text-white/60 mb-6">
              This verification link has expired. Request a new one below.
            </p>

            <div className="space-y-3">
              <AppButton
                variant="accent"
                fullWidth
                onClick={handleResend}
                isLoading={resendMutation.isPending}
                disabled={resendCooldown > 0 || !email}
                leftIcon={<RefreshIcon className="w-4 h-4" />}
                className="touch-target min-h-touch"
              >
                {resendCooldown > 0
                  ? `Resend in ${resendCooldown}s`
                  : 'Send new verification email'}
              </AppButton>

              {resendMutation.isSuccess && (
                <p className={cn(
                  "text-sm text-success-500 dark:text-success-400",
                  !prefersReducedMotion && "animate-fade-in"
                )}>
                  New email sent! Check your inbox.
                </p>
              )}

              <AppButton
                variant="ghost"
                fullWidth
                onClick={handleBackToRegister}
                className="touch-target min-h-touch"
              >
                Back to registration
              </AppButton>
            </div>
          </>
        )}

        {/* Error State */}
        {status === 'error' && (
          <>
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full bg-error-500/20" />
              <div className="absolute inset-2 rounded-full bg-error-500/10 flex items-center justify-center">
                <XCircleIcon className="w-10 h-10 text-error-500 dark:text-error-400" />
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white mb-3">Verification failed</h1>
            <p className="text-neutral-600 dark:text-white/60 mb-6">
              {errorMessage || 'We couldn\'t verify your email. Please try again.'}
            </p>

            <div className="space-y-3">
              <AppButton
                variant="outline"
                fullWidth
                onClick={handleResend}
                isLoading={resendMutation.isPending}
                disabled={resendCooldown > 0 || !email}
                leftIcon={<RefreshIcon className="w-4 h-4" />}
                className="touch-target min-h-touch"
              >
                {resendCooldown > 0
                  ? `Resend in ${resendCooldown}s`
                  : 'Request new verification email'}
              </AppButton>

              <AppButton
                variant="ghost"
                fullWidth
                onClick={handleBackToRegister}
                className="touch-target min-h-touch"
              >
                Back to registration
              </AppButton>
            </div>
          </>
        )}

        {/* Error message from resend */}
        {resendMutation.isError && (
          <p className={cn(
            "text-sm text-error-500 dark:text-error-400 mt-4",
            !prefersReducedMotion && "animate-fade-in"
          )}>
            {errorMessage || 'Failed to send email. Please try again.'}
          </p>
        )}
      </AppCard>

      {/* Help text */}
      <p className={cn(
        "mt-8 text-sm text-neutral-500 dark:text-white/40 text-center max-w-sm",
        !prefersReducedMotion && "animate-fade-in-up"
      )} style={{ animationDelay: '300ms' }}>
        Having trouble? Contact us at{' '}
        <a href="mailto:support@vdrive.app" className="text-primary-500 dark:text-primary-400 hover:underline">
          support@vdrive.app
        </a>
      </p>
    </div>
  );
}

export default VerifyEmailPage;
