/**
 * Register Page
 * User registration page with mobile-first futuristic responsive layout
 * Enhanced with safe areas, touch targets, haptic feedback, and modern effects
 *
 * T052: Create Register page with mobile-first responsive layout
 */

import { useNavigate, useSearchParams } from 'react-router-dom';
import { RegistrationForm } from '../components/onboarding/RegistrationForm';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { handleGoogleCallback } from '../components/onboarding/GoogleOAuthButton';
import { useEffect, useState, useCallback } from 'react';
import { cn } from '../lib/utils';
import { useBreakpoint, useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';
import { AppLogo } from '../components/ui/AppLogo';

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
      <polyline points="22,4 12,14.01 9,11.01" />
    </svg>
  );
}

// Futuristic particle effect component
function ParticleEffect() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) return null;

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(25)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-accent-400/30 dark:bg-accent-400/20"
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

// Morphing blob background
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
    icon: CheckCircleIcon,
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

  // Mobile-first hooks
  const { isMobile } = useBreakpoint();
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();
  const safeArea = useSafeArea();

  // Handle OAuth callback (T070)
  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (code && state) {
      setIsProcessingOAuth(true);
      handleGoogleCallback().then((result) => {
        setIsProcessingOAuth(false);
        if (result.success) {
          haptic.success();
          // Navigate based on whether it's a new user
          if (result.isNewUser) {
            navigate('/onboarding/workspace');
          } else {
            navigate('/dashboard');
          }
        } else {
          haptic.error();
          setOauthError(result.error || 'OAuth failed');
        }
      });
    }
  }, [searchParams, navigate, haptic]);

  const handleRegistrationSuccess = useCallback(() => {
    haptic.success();
    navigate('/verify-email');
  }, [haptic, navigate]);

  // Show loading while processing OAuth
  if (isProcessingOAuth) {
    return (
      <div className="min-h-screen-dynamic flex items-center justify-center bg-neutral-50 dark:bg-warm-950 transition-colors duration-300 pt-safe pb-safe">
        {/* Futuristic background */}
        <div className="auth-bg">
          <div className="aurora-orb" />
          <MorphingBlob className="w-96 h-96 bg-accent-500/20 -top-48 -right-48" />
          <MorphingBlob className="w-64 h-64 bg-primary-500/20 bottom-20 left-10" />
        </div>
        <ParticleEffect />

        <div className="text-center relative z-10">
          {/* Neon glow spinner */}
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full bg-accent-500/20 animate-pulse blur-xl" />
            <div className="relative w-16 h-16 border-4 border-accent-500/30 border-t-accent-500 rounded-full animate-spin" />
          </div>
          <p className="text-neutral-600 dark:text-white/70 text-lg">Creating your account...</p>
          <p className="text-neutral-400 dark:text-white/40 text-sm mt-2">Setting up your creative workspace</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen-dynamic flex bg-neutral-50 dark:bg-warm-950 transition-colors duration-300">
      {/* Theme-Aware Background with Futuristic Effects */}
      <div className="auth-bg">
        <div className="aurora-orb" />
        <MorphingBlob className="w-[500px] h-[500px] bg-gradient-to-br from-accent-500/20 to-primary-500/20 -top-64 -right-64" />
        <MorphingBlob className="w-80 h-80 bg-primary-500/15 bottom-10 left-20 hidden lg:block" />
        {!prefersReducedMotion && (
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.03),transparent_70%)]" />
        )}
      </div>
      <ParticleEffect />

      {/* Theme Toggle (fixed position with safe area) */}
      <div
        className="fixed top-6 right-6 z-50 touch-target"
        style={{ top: `calc(1.5rem + ${safeArea.top}px)` }}
      >
        <ThemeToggle />
      </div>

      {/* Left Side - Branding (hidden on mobile/tablet) */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-[55%] relative overflow-hidden">
        {/* Background Image with enhanced gradient */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(/images/register-bg.jpg)',
          }}
        >
          {/* Light mode: softer gradient, Dark mode: dramatic gradient with neon accent */}
          <div className="absolute inset-0 bg-gradient-to-r from-white via-white/90 to-white/70 dark:from-warm-950 dark:via-warm-950/80 dark:to-transparent" />
          {/* Subtle neon line accent */}
          <div className="absolute right-0 top-1/4 bottom-1/4 w-px bg-gradient-to-b from-transparent via-accent-500/50 to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20 max-w-2xl">
          {/* Logo - with entrance animation and hover effect */}
          <a
            href="/"
            className={cn(
              "inline-flex items-center gap-3 mb-12 group",
              !prefersReducedMotion && "animate-fade-in-scale"
            )}
          >
            <AppLogo size="md" />
            <span className="text-2xl font-bold text-neutral-900 dark:text-white">vDrive</span>
          </a>

          {/* Headline - with staggered entrance and gradient text */}
          <h1
            className={cn(
              "text-4xl xl:text-5xl font-bold text-neutral-900 dark:text-white mb-6 leading-tight",
              !prefersReducedMotion && "animate-fade-in-up stagger-1"
            )}
          >
            Your photography
            <br />
            <span className="gradient-text bg-gradient-to-r from-accent-500 via-primary-500 to-accent-600 bg-clip-text text-transparent">
              deserves better
            </span>
          </h1>

          <p
            className={cn(
              "text-lg text-neutral-600 dark:text-white/70 mb-12 max-w-lg",
              !prefersReducedMotion && "animate-fade-in-up stagger-2"
            )}
          >
            Join thousands of photographers who use vDrive to manage, showcase,
            and deliver their work with stunning galleries.
          </p>

          {/* Features - with staggered entrance and glass cards */}
          <div className="space-y-4">
            {features.map((feature, index) => (
              <div
                key={index}
                className={cn(
                  'flex items-start gap-4 p-4 rounded-2xl',
                  'bg-white/50 dark:bg-white/[0.06] backdrop-blur-sm',
                  'border border-neutral-200/50 dark:border-white/10',
                  'hover:bg-white/70 dark:hover:bg-white/[0.08] transition-all duration-300',
                  'group',
                  !prefersReducedMotion && 'animate-fade-in-up'
                )}
                style={{ animationDelay: prefersReducedMotion ? '0ms' : `${200 + index * 100}ms` }}
              >
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-accent-500/10 to-primary-500/10 dark:from-accent-500/20 dark:to-primary-500/20 flex items-center justify-center shrink-0 group-hover:shadow-glow-sm transition-shadow">
                  <feature.icon className="w-5 h-5 text-accent-600 dark:text-accent-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-neutral-900 dark:text-white">{feature.title}</h3>
                  <p className="text-sm text-neutral-500 dark:text-white/60">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Social proof */}
          <div className={cn(
            "mt-12 pt-8 border-t border-neutral-200/50 dark:border-white/10",
            !prefersReducedMotion && "animate-fade-in-up stagger-6"
          )}>
            <div className="flex items-center gap-4">
              <div className="flex -space-x-3">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="w-10 h-10 rounded-full bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-warm-700 dark:to-warm-800 border-2 border-white dark:border-warm-950"
                  />
                ))}
              </div>
              <div>
                <p className="text-sm font-medium text-neutral-900 dark:text-white">10,000+ photographers</p>
                <p className="text-xs text-neutral-500 dark:text-white/50">have joined vDrive this month</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Registration Form with mobile-first design */}
      <div
        className={cn(
          "w-full lg:w-1/2 xl:w-[45%] flex items-center justify-center",
          "px-4 py-8 sm:p-8 lg:p-12",
          "pt-safe pb-safe" // Safe area for notch/dynamic island
        )}
      >
        <div
          className={cn(
            "w-full max-w-md",
            !prefersReducedMotion && (isMobile ? "animate-slide-up-mobile" : "animate-fade-in-scale")
          )}
          style={{ animationDelay: prefersReducedMotion ? '0ms' : '150ms' }}
        >
          {/* Mobile Logo with enhanced styling */}
          <div className="lg:hidden flex flex-col items-center gap-3 mb-10">
            <AppLogo size="lg" />
            <span className="text-2xl font-bold text-neutral-900 dark:text-white mt-2">vDrive</span>
            <p className="text-neutral-500 dark:text-white/60 text-center text-sm">
              Start your creative journey
            </p>
          </div>

          {/* OAuth Error with enhanced styling */}
          {oauthError && (
            <div
              className={cn(
                "mb-6 p-4 rounded-2xl",
                "bg-error-500/10 dark:bg-error-500/15",
                "border border-error-500/30 dark:border-error-500/40",
                "shadow-neon-error/20",
                !prefersReducedMotion && "animate-fade-in"
              )}
              role="alert"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-error-500/20 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5 text-error-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="font-semibold text-error-600 dark:text-error-400">Registration failed</p>
                  <p className="text-sm mt-1 text-error-500/80 dark:text-error-400/80">{oauthError}</p>
                </div>
              </div>
            </div>
          )}

          {/* Glass card container for form on mobile */}
          <div className={cn(
            "lg:bg-transparent lg:p-0 lg:border-0 lg:shadow-none lg:backdrop-blur-none",
            "bg-white/80 dark:bg-white/[0.06] backdrop-blur-xl",
            "p-6 sm:p-8 rounded-3xl",
            "border border-neutral-200/50 dark:border-white/10",
            "shadow-glass dark:shadow-none"
          )}>
            {/* Registration Form */}
            <RegistrationForm onSuccess={handleRegistrationSuccess} />
          </div>

          {/* Trust badges for mobile */}
          <div className="lg:hidden flex items-center justify-center gap-6 mt-8 text-neutral-400 dark:text-white/40">
            <div className="flex items-center gap-2 text-xs">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
              </svg>
              <span>Free to start</span>
            </div>
            <div className="w-px h-4 bg-neutral-300 dark:bg-white/20" />
            <div className="flex items-center gap-2 text-xs">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>No credit card</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
