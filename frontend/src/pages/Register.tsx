/**
 * Register Page
 * User registration page with mobile-first responsive layout
 *
 * T052: Create Register page with mobile-first responsive layout
 */

import { useNavigate, useSearchParams } from 'react-router-dom';
import { RegistrationForm } from '../components/onboarding/RegistrationForm';
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

function SparklesIcon({ className }: { className?: string }) {
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
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}

// ============================================
// Features List
// ============================================

const features = [
  {
    icon: CameraIcon,
    title: 'Stunning Galleries',
    description: 'Showcase your work in beautiful, customizable galleries',
  },
  {
    icon: SparklesIcon,
    title: 'AI-Powered',
    description: 'Smart organization and editing suggestions',
  },
  {
    icon: CameraIcon,
    title: 'Client Proofing',
    description: 'Let clients select and approve photos seamlessly',
  },
];

// ============================================
// Page Component
// ============================================

export function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [oauthError, setOauthError] = useState<string | null>(null);
  const [isProcessingOAuth, setIsProcessingOAuth] = useState(false);

  // Handle OAuth callback (T070)
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

  const handleRegistrationSuccess = () => {
    navigate('/verify-email');
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
            backgroundImage: 'url(/images/register-bg.jpg)',
          }}
        >
          {/* Light mode: softer gradient, Dark mode: dramatic gradient */}
          <div className="absolute inset-0 bg-gradient-to-r from-white via-white/90 to-white/70 dark:from-neutral-950 dark:via-neutral-950/80 dark:to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20 max-w-2xl">
          {/* Logo - with entrance animation */}
          <a href="/" className="inline-flex items-center gap-2 mb-12 animate-fade-in-scale">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <CameraIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-neutral-900 dark:text-white">vDrive</span>
          </a>

          {/* Headline - with staggered entrance */}
          <h1 className="text-4xl xl:text-5xl font-bold text-neutral-900 dark:text-white mb-6 leading-tight animate-fade-in-up stagger-1">
            Your photography
            <br />
            <span className="gradient-text">deserves better</span>
          </h1>

          <p className="text-lg text-neutral-600 dark:text-white/70 mb-12 max-w-lg animate-fade-in-up stagger-2">
            Join thousands of photographers who use vDrive to manage, showcase,
            and deliver their work with stunning galleries.
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

      {/* Right Side - Registration Form with slide-in animation */}
      <div className="w-full lg:w-1/2 xl:w-[45%] flex items-center justify-center p-6 sm:p-8 lg:p-12">
        <div className="w-full max-w-md animate-slide-in-right lg:animate-fade-in-scale" style={{ animationDelay: '150ms' }}>
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <CameraIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-neutral-900 dark:text-white">vDrive</span>
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

          {/* Registration Form */}
          <RegistrationForm onSuccess={handleRegistrationSuccess} />
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
