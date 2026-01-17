/**
 * Login Page
 * User sign-in page with mobile-first responsive layout
 */

import { useNavigate, useSearchParams } from 'react-router-dom';
import { LoginForm } from '../components/onboarding/LoginForm';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { handleGoogleCallback } from '../services/google-oauth';
import { useEffect, useState } from 'react';
import { cn } from '../lib/utils';
import { AppLogo } from '../components/ui/AppLogo';

// ============================================
// Icons
// ============================================

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
      // Use requestAnimationFrame to avoid sync setState in effect
      const frame = requestAnimationFrame(() => {
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
      });

      return () => cancelAnimationFrame(frame);
    }
  }, [searchParams, navigate]);

  const handleLoginSuccess = () => {
    // Always navigate to dashboard after successful login
    // The backend will handle workspace creation if needed
    navigate('/dashboard');
  };

  // Show loading while processing OAuth
  if (isProcessingOAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-warm-950 transition-colors duration-300">
        <div className="auth-bg">
          <div className="aurora-orb" />
        </div>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-neutral-600 dark:text-white/70">Completing sign in...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-neutral-50 dark:bg-warm-950 transition-colors duration-300">
      {/* Theme-Aware Background */}
      <div className="auth-bg">
        <div className="aurora-orb" />
      </div>

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
          {/* Light mode: softer gradient, Dark mode: dramatic gradient */}
          <div className="absolute inset-0 bg-gradient-to-r from-white via-white/90 to-white/70 dark:from-neutral-950 dark:via-neutral-950/80 dark:to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20 max-w-2xl">
          {/* Logo - with entrance animation */}
          <a href="/" className="inline-flex items-center gap-3 mb-12 animate-fade-in-scale">
            <AppLogo size="md" />
            <span className="text-2xl font-bold text-neutral-900 dark:text-white">RawDrive</span>
          </a>

          {/* Headline - with staggered entrance */}
          <h1 className="text-4xl xl:text-5xl font-bold text-neutral-900 dark:text-white mb-6 leading-tight animate-fade-in-up stagger-1">
            Welcome back
            <br />
            <span className="gradient-text">to your studio</span>
          </h1>

          <p className="text-lg text-neutral-600 dark:text-white/70 mb-12 max-w-lg animate-fade-in-up stagger-2">
            Your galleries, clients, and creative work are waiting.
            Sign in to continue where you left off.
          </p>

          {/* Features - with staggered entrance */}
          <div className="space-y-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className={cn(
                  'flex items-start gap-4 animate-fade-in-up'
                )}
                style={{ animationDelay: `${200 + index * 100}ms` }}
              >
                <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-white/10 backdrop-blur-sm flex items-center justify-center shrink-0">
                  <feature.icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-neutral-900 dark:text-white">{feature.title}</h3>
                  <p className="text-sm text-neutral-500 dark:text-white/60">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Side - Login Form with slide-in animation */}
      <div className="w-full lg:w-1/2 xl:w-[45%] flex items-center justify-center p-6 sm:p-8 lg:p-12">
        <div className="w-full max-w-md animate-slide-in-right lg:animate-fade-in-scale" style={{ animationDelay: '150ms' }}>
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <AppLogo size="md" />
            <span className="text-2xl font-bold text-neutral-900 dark:text-white">RawDrive</span>
          </div>

          {/* OAuth Error */}
          {oauthError && (
            <div
              className="mb-6 p-4 rounded-xl bg-error-500/10 dark:bg-error-500/20 border border-error-500/30 text-error-600 dark:text-error-400"
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
