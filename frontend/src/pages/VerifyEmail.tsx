/**
 * VerifyEmail Page
 * Email verification page with resend functionality
 *
 * T053: Create VerifyEmail page for verification link handling
 * T100: Add resend button to VerifyEmail page
 * T101: Add expired link UI with resend option
 */

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { onboardingApi } from '../services/onboarding-api';
import { AppButton } from '../components/ui/AppButton';
import { AppCard } from '../components/ui/AppCard';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { cn } from '../lib/utils';

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

  // Verify email token
  const verifyMutation = useMutation({
    mutationFn: () => onboardingApi.verifyEmail(token!),
    onSuccess: (data) => {
      if (data.success) {
        setStatus('success');
        // Redirect to workspace setup after delay
        setTimeout(() => {
          navigate('/onboarding/workspace');
        }, 2000);
      } else {
        setStatus('error');
        setErrorMessage(data.message);
      }
    },
    onError: (error: { message?: string; error?: string }) => {
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
      // Start cooldown timer (60 seconds)
      setResendCooldown(60);
    },
    onError: (error: { message?: string }) => {
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

  const handleResend = () => {
    if (!email || resendCooldown > 0) return;
    resendMutation.mutate();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-950 p-6">
      {/* Aurora Background */}
      <div className="aurora-bg" />

      {/* Theme Toggle */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <AppCard variant="glass" padding="lg" className="w-full max-w-md text-center">
        {/* Pending State - Waiting for user to check email */}
        {status === 'pending' && (
          <>
            <div className="w-16 h-16 rounded-full bg-primary-500/20 flex items-center justify-center mx-auto mb-6">
              <MailIcon className="w-8 h-8 text-primary-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Check your email</h1>
            <p className="text-white/60 mb-6">
              We've sent a verification link to
              {email && (
                <span className="block text-white font-medium mt-1">{email}</span>
              )}
            </p>

            <div className="space-y-4">
              <p className="text-sm text-white/50">
                Click the link in the email to verify your account.
              </p>

              {/* Resend Button */}
              <div className="pt-4 border-t border-white/10">
                <p className="text-sm text-white/50 mb-3">
                  Didn't receive the email?
                </p>
                <AppButton
                  variant="outline"
                  onClick={handleResend}
                  isLoading={resendMutation.isPending}
                  disabled={resendCooldown > 0 || !email}
                  leftIcon={<RefreshIcon className="w-4 h-4" />}
                >
                  {resendCooldown > 0
                    ? `Resend in ${resendCooldown}s`
                    : 'Resend email'}
                </AppButton>
                {resendMutation.isSuccess && (
                  <p className="text-sm text-success-400 mt-2">
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
            <div className="w-16 h-16 rounded-full bg-primary-500/20 flex items-center justify-center mx-auto mb-6">
              <div className="w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Verifying...</h1>
            <p className="text-white/60">Please wait while we verify your email.</p>
          </>
        )}

        {/* Success State */}
        {status === 'success' && (
          <>
            <div
              className={cn(
                'w-16 h-16 rounded-full bg-success-500/20 flex items-center justify-center mx-auto mb-6',
                'animate-fade-up'
              )}
            >
              <CheckCircleIcon className="w-8 h-8 text-success-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Email verified!</h1>
            <p className="text-white/60 mb-6">
              Your email has been successfully verified.
            </p>
            <p className="text-sm text-white/50">
              Redirecting to workspace setup...
            </p>
          </>
        )}

        {/* Expired State (T101) */}
        {status === 'expired' && (
          <>
            <div className="w-16 h-16 rounded-full bg-warning-500/20 flex items-center justify-center mx-auto mb-6">
              <ClockIcon className="w-8 h-8 text-warning-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Link expired</h1>
            <p className="text-white/60 mb-6">
              This verification link has expired. Request a new one below.
            </p>

            <div className="space-y-4">
              <AppButton
                variant="accent"
                fullWidth
                onClick={handleResend}
                isLoading={resendMutation.isPending}
                disabled={resendCooldown > 0 || !email}
                leftIcon={<RefreshIcon className="w-4 h-4" />}
              >
                {resendCooldown > 0
                  ? `Resend in ${resendCooldown}s`
                  : 'Send new verification email'}
              </AppButton>

              {resendMutation.isSuccess && (
                <p className="text-sm text-success-400">
                  New email sent! Check your inbox.
                </p>
              )}

              <AppButton
                variant="ghost"
                fullWidth
                onClick={() => navigate('/register')}
              >
                Back to registration
              </AppButton>
            </div>
          </>
        )}

        {/* Error State */}
        {status === 'error' && (
          <>
            <div className="w-16 h-16 rounded-full bg-error-500/20 flex items-center justify-center mx-auto mb-6">
              <XCircleIcon className="w-8 h-8 text-error-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Verification failed</h1>
            <p className="text-white/60 mb-6">
              {errorMessage || 'We couldn\'t verify your email. Please try again.'}
            </p>

            <div className="space-y-4">
              <AppButton
                variant="outline"
                fullWidth
                onClick={handleResend}
                isLoading={resendMutation.isPending}
                disabled={resendCooldown > 0 || !email}
                leftIcon={<RefreshIcon className="w-4 h-4" />}
              >
                {resendCooldown > 0
                  ? `Resend in ${resendCooldown}s`
                  : 'Request new verification email'}
              </AppButton>

              <AppButton
                variant="ghost"
                fullWidth
                onClick={() => navigate('/register')}
              >
                Back to registration
              </AppButton>
            </div>
          </>
        )}

        {/* Error message from resend */}
        {resendMutation.isError && (
          <p className="text-sm text-error-400 mt-4">
            {errorMessage || 'Failed to send email. Please try again.'}
          </p>
        )}
      </AppCard>
    </div>
  );
}

export default VerifyEmailPage;
