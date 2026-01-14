/**
 * WorkspaceSetup Page
 * Workspace creation page with wizard integration
 *
 * T091: Create WorkspaceSetup page with wizard integration
 * T117: Add "Continue or Start Fresh" prompt
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { WorkspaceWizard } from '../components/onboarding/WorkspaceWizard';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { AppButton } from '../components/ui/AppButton';
import { AppCard } from '../components/ui/AppCard';
import { useOnboardingState } from '../hooks/useOnboardingState';
import type { WorkspaceResponse } from '../types/onboarding';
import { cn } from '../lib/utils';

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

  // Show resume prompt if there's existing progress (T117)
  useEffect(() => {
    if (!isLoading && hasExistingProgress && workspaceData.name) {
      setShowResumePrompt(true);
    }
  }, [isLoading, hasExistingProgress, workspaceData.name]);

  const handleComplete = (workspace: WorkspaceResponse) => {
    // Store workspace info
    localStorage.setItem('current_workspace_id', workspace.id);
    localStorage.setItem('current_workspace_slug', workspace.slug);

    // Navigate to dashboard
    navigate('/dashboard');
  };

  const handleContinue = () => {
    setShowResumePrompt(false);
  };

  const handleStartFresh = async () => {
    setIsResetting(true);
    await resetProgress();
    setIsResetting(false);
    setShowResumePrompt(false);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-950">
        <div className="aurora-bg" />
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/70">Loading your progress...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-950 p-6">
      {/* Aurora Background */}
      <div className="aurora-bg" />

      {/* Theme Toggle */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Logo */}
      <div className="fixed top-6 left-6 z-50">
        <a href="/" className="inline-flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <CameraIcon className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white">vDrive</span>
        </a>
      </div>

      {/* Resume Prompt (T117) */}
      {showResumePrompt && (
        <AppCard
          variant="glass"
          padding="lg"
          className={cn(
            'w-full max-w-md text-center',
            'animate-fade-up'
          )}
        >
          <div className="w-16 h-16 rounded-full bg-primary-500/20 flex items-center justify-center mx-auto mb-6">
            <RefreshIcon className="w-8 h-8 text-primary-400" />
          </div>

          <h1 className="text-2xl font-bold text-white mb-2">
            Welcome back!
          </h1>
          <p className="text-white/60 mb-6">
            Looks like you were setting up{' '}
            <span className="text-white font-medium">"{workspaceData.name}"</span>.
            Would you like to continue?
          </p>

          <div className="space-y-3">
            <AppButton
              variant="accent"
              fullWidth
              onClick={handleContinue}
              leftIcon={<PlayIcon className="w-4 h-4" />}
            >
              Continue Setup
            </AppButton>

            <AppButton
              variant="outline"
              fullWidth
              onClick={handleStartFresh}
              isLoading={isResetting}
              leftIcon={<RefreshIcon className="w-4 h-4" />}
            >
              Start Fresh
            </AppButton>
          </div>
        </AppCard>
      )}

      {/* Workspace Wizard */}
      {!showResumePrompt && (
        <WorkspaceWizard onComplete={handleComplete} />
      )}

      {/* Progress Indicator */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2">
        <div className="flex items-center gap-2 text-sm text-white/50">
          <span>Step 3 of 4</span>
          <span className="text-white/30">•</span>
          <span>Workspace Setup</span>
        </div>
      </div>
    </div>
  );
}

export default WorkspaceSetupPage;
