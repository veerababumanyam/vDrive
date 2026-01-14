/**
 * Login Page
 * User sign-in page with mobile-first responsive layout
 */

import { useNavigate, useSearchParams } from 'react-router-dom';
import { LoginForm } from '../components/onboarding/LoginForm';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { handleGoogleCallback } from '../components/onboarding/GoogleOAuthButton';
import { useEffect, useState } from 'react';
import { cn } from '../lib/utils';

// ============================================
// Icons
// ============================================

function CameraIcon({ className }: { className?: string }) {
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
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3" />
    </svg>
  );
}

function ShieldCheckIcon({ className }: { className?: string }) {
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
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

function CloudIcon({ className }: { className?: string }) {
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
      <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
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
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

// ============================================
// Features List
// ============================================

const features = [
  {
    icon: ShieldCheckIcon,
    title: 'Secure Access',
    description: 'Enterprise-grade security for your precious work',
  },
  {
    icon: CloudIcon,
    title: 'Cloud Storage',
    description: 'Access your galleries from anywhere, anytime',
  },
  {
    icon: UsersIcon,
    title: 'Team Collaboration',
    description: 'Work seamlessly with clients and team members',
  },
];

// ============================================
// Page Component
// ============================================

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [oauthError, setOauthError] = useState<string | null>(null);
  const [isProcessingOAuth, setIsProcessingOAuth] = useState(false);

  // Handle OAuth callback
  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (code && state) {
      setIsProcessingOAuth(true);
      handleGoogleCallback().then((result) => {
        setIsProcessingOAuth(false);
        if (result.success) {
          // Navigate based on whether it's a new user
          if (result.isNewUser) {
            navigate('/onboarding/workspace');
          } else {
            navigate('/dashboard');
          }
        } else {
          setOauthError(result.error || 'OAuth failed');
        }
      });
    }
  }, [searchParams, navigate]);

  const handleLoginSuccess = () => {
    navigate('/dashboard');
  };

  // Show loading while processing OAuth
  if (isProcessingOAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-950">
        <div className="aurora-bg" />
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/70">Completing sign in...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-neutral-950">
      {/* Aurora Background */}
      <div className="aurora-bg" />

      {/* Theme Toggle (fixed position) */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Left Side - Branding (hidden on mobile) */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-[55%] relative overflow-hidden">
        {/* Background Image */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(/images/login-bg.jpg)',
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-neutral-950 via-neutral-950/80 to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20 max-w-2xl">
          {/* Logo */}
          <a href="/" className="inline-flex items-center gap-2 mb-12">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <CameraIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">vDrive</span>
          </a>

          {/* Headline */}
          <h1 className="text-4xl xl:text-5xl font-bold text-white mb-6 leading-tight">
            Welcome back
            <br />
            <span className="gradient-text">to your studio</span>
          </h1>

          <p className="text-lg text-white/70 mb-12 max-w-lg">
            Your galleries, clients, and creative work are waiting.
            Sign in to continue where you left off.
          </p>

          {/* Features */}
          <div className="space-y-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className={cn(
                  'flex items-start gap-4 animate-fade-up',
                  `animation-delay-${(index + 1) * 100}`
                )}
              >
                <div className="w-10 h-10 rounded-lg bg-white/10 backdrop-blur-sm flex items-center justify-center shrink-0">
                  <feature.icon className="w-5 h-5 text-primary-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{feature.title}</h3>
                  <p className="text-sm text-white/60">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 xl:w-[45%] flex items-center justify-center p-6 sm:p-8 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <CameraIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">vDrive</span>
          </div>

          {/* OAuth Error */}
          {oauthError && (
            <div
              className="mb-6 p-4 rounded-xl bg-error-500/20 border border-error-500/30 text-error-400"
              role="alert"
            >
              <p className="font-medium">Sign in failed</p>
              <p className="text-sm mt-1">{oauthError}</p>
            </div>
          )}

          {/* Login Form */}
          <LoginForm onSuccess={handleLoginSuccess} />
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
