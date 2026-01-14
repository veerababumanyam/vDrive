/**
 * WorkspaceSetup Page
 * Workspace creation page with wizard integration
 * Enhanced with mobile-first futuristic design, safe areas, and haptic feedback
 *
 * T091: Create WorkspaceSetup page with wizard integration
 * T117: Add "Continue or Start Fresh" prompt
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { WorkspaceWizard } from '../components/onboarding/WorkspaceWizard';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { AppButton } from '../components/ui/AppButton';
import { AppCard } from '../components/ui/AppCard';
import { useOnboardingState } from '../hooks/useOnboardingState';
import type { WorkspaceResponse } from '../types/onboarding';
import { cn } from '../lib/utils';
import { useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';
import { AppLogo } from '../components/ui/AppLogo';

// ============================================
// Icons
// ============================================

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

function PlayIcon({ className }: { className?: string }) {
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
      <polygon points="5 3 19 12 5 21 5 3" />
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
      {[...Array(15)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-accent-400/25 dark:bg-accent-400/15"
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
// Page Component
// ============================================

export function WorkspaceSetupPage() {
  const navigate = useNavigate();
  const {
    hasExistingProgress,
    workspaceData,
    isLoading,
    resetProgress,
  } = useOnboardingState();

  const [showResumePrompt, setShowResumePrompt] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  // Mobile-first hooks
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();
  const safeArea = useSafeArea();

  // Show resume prompt if there's existing progress (T117)
  useEffect(() => {
    if (!isLoading && hasExistingProgress && workspaceData.name) {
      setShowResumePrompt(true);
    }
  }, [isLoading, hasExistingProgress, workspaceData.name]);

  const handleComplete = useCallback((workspace: WorkspaceResponse) => {
    haptic.success();
    // Store workspace info
    localStorage.setItem('current_workspace_id', workspace.id);
    localStorage.setItem('current_workspace_slug', workspace.slug);

    // Navigate to dashboard
    navigate('/dashboard');
  }, [haptic, navigate]);

  const handleContinue = useCallback(() => {
    haptic.medium();
    setShowResumePrompt(false);
  }, [haptic]);

  const handleStartFresh = useCallback(async () => {
    haptic.light();
    setIsResetting(true);
    await resetProgress();
    setIsResetting(false);
    setShowResumePrompt(false);
  }, [haptic, resetProgress]);

  // Loading state
  if (isLoading) {
    return (
      <div
        className="min-h-screen-dynamic flex items-center justify-center bg-neutral-50 dark:bg-warm-950 transition-colors duration-300 relative overflow-hidden"
        style={{
          paddingTop: safeArea.top,
          paddingBottom: safeArea.bottom,
        }}
      >
        {/* Futuristic background */}
        <div className="auth-bg">
          <div className="aurora-orb" />
          <MorphingBlob className="w-96 h-96 bg-accent-500/15 -top-48 -right-48" />
          <MorphingBlob className="w-64 h-64 bg-primary-500/15 bottom-20 left-10" />
        </div>
        <ParticleEffect />

        <div className="text-center relative z-10">
          {/* Neon glow spinner */}
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className={cn(
              "absolute inset-0 rounded-full bg-accent-500/20",
              !prefersReducedMotion && "animate-pulse"
            )} style={{ filter: 'blur(12px)' }} />
            <div className="relative w-16 h-16 border-4 border-accent-500/30 border-t-accent-500 rounded-full animate-spin" />
          </div>
          <p className="text-neutral-600 dark:text-white/70 text-lg">Loading your progress...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen-dynamic flex items-center justify-center bg-neutral-50 dark:bg-warm-950 transition-colors duration-300 relative overflow-hidden px-4 sm:px-6"
      style={{
        paddingTop: `calc(1.5rem + ${safeArea.top}px)`,
        paddingBottom: `calc(5rem + ${safeArea.bottom}px)`,
      }}
    >
      {/* Theme-Aware Background with Futuristic Effects */}
      <div className="auth-bg">
        <div className="aurora-orb" />
        <MorphingBlob className="w-[500px] h-[500px] bg-gradient-to-br from-accent-500/15 to-primary-500/15 -top-64 -right-64" />
        <MorphingBlob className="w-80 h-80 bg-primary-500/10 bottom-20 left-10" />
        {!prefersReducedMotion && (
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.02),transparent_70%)]" />
        )}
      </div>
      <ParticleEffect />

      {/* Theme Toggle */}
      <div
        className="fixed right-4 sm:right-6 z-50 touch-target"
        style={{ top: `calc(1rem + ${safeArea.top}px)` }}
      >
        <ThemeToggle />
      </div>

      {/* Logo */}
      <div
        className="fixed left-4 sm:left-6 z-50"
        style={{ top: `calc(1rem + ${safeArea.top}px)` }}
      >
        <a
          href="/"
          className={cn(
            "inline-flex items-center gap-3 group touch-target",
            !prefersReducedMotion && "animate-fade-in-down"
          )}
        >
          <AppLogo size="md" className="w-10 h-10 sm:w-11 sm:h-11" />
          <span className="text-lg sm:text-xl font-bold text-neutral-900 dark:text-white hidden sm:block">vDrive</span>
        </a>
      </div>

      {/* Resume Prompt (T117) */}
      {showResumePrompt && (
        <AppCard
          variant="glass"
          padding="lg"
          className={cn(
            'w-full max-w-md text-center relative z-10',
            !prefersReducedMotion && 'animate-fade-in-scale'
          )}
        >
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className={cn(
              "absolute inset-0 rounded-full bg-primary-500/20",
              !prefersReducedMotion && "animate-pulse"
            )} />
            <div className="absolute inset-2 rounded-full bg-primary-500/10 flex items-center justify-center">
              <RefreshIcon className="w-10 h-10 text-primary-500 dark:text-primary-400" />
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white mb-3">
            Welcome back!
          </h1>
          <p className="text-neutral-600 dark:text-white/60 mb-6">
            Looks like you were setting up{' '}
            <span className="inline-block mt-2 px-4 py-2 rounded-xl bg-neutral-100 dark:bg-white/[0.08] text-neutral-900 dark:text-white font-medium">
              "{workspaceData.name}"
            </span>
          </p>
          <p className="text-sm text-neutral-500 dark:text-white/50 mb-6">
            Would you like to continue where you left off?
          </p>

          <div className="space-y-3">
            <AppButton
              variant="accent"
              fullWidth
              onClick={handleContinue}
              leftIcon={<PlayIcon className="w-4 h-4" />}
              className="touch-target min-h-touch"
            >
              Continue Setup
            </AppButton>

            <AppButton
              variant="outline"
              fullWidth
              onClick={handleStartFresh}
              isLoading={isResetting}
              leftIcon={<RefreshIcon className="w-4 h-4" />}
              className="touch-target min-h-touch"
            >
              Start Fresh
            </AppButton>
          </div>
        </AppCard>
      )}

      {/* Workspace Wizard */}
      {!showResumePrompt && (
        <div className={cn(
          "w-full max-w-2xl relative z-10",
          !prefersReducedMotion && "animate-fade-in-scale"
        )}>
          <WorkspaceWizard onComplete={handleComplete} />
        </div>
      )}

      {/* Progress Indicator */}
      <div
        className={cn(
          "fixed left-1/2 -translate-x-1/2 z-40",
          !prefersReducedMotion && "animate-fade-in-up"
        )}
        style={{ bottom: `calc(1.5rem + ${safeArea.bottom}px)` }}
      >
        <div className={cn(
          "flex items-center gap-3 px-5 py-3 rounded-full",
          "bg-white/80 dark:bg-white/[0.08] backdrop-blur-xl",
          "border border-neutral-200/50 dark:border-white/10",
          "shadow-lg shadow-neutral-200/50 dark:shadow-none"
        )}>
          {/* Step indicators */}
          <div className="flex items-center gap-1.5">
            {[1, 2, 3, 4].map((step) => (
              <div
                key={step}
                className={cn(
                  "w-2 h-2 rounded-full transition-all duration-300",
                  step < 3 && "bg-accent-500",
                  step === 3 && "w-6 bg-gradient-to-r from-accent-500 to-primary-500",
                  step > 3 && "bg-neutral-300 dark:bg-white/20"
                )}
              />
            ))}
          </div>

          <div className="w-px h-4 bg-neutral-200 dark:bg-white/10" />

          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium text-neutral-900 dark:text-white">Step 3</span>
            <span className="text-neutral-500 dark:text-white/50">of 4</span>
            <span className="text-neutral-300 dark:text-white/30 hidden sm:inline">•</span>
            <span className="text-neutral-500 dark:text-white/50 hidden sm:inline">Workspace Setup</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WorkspaceSetupPage;
