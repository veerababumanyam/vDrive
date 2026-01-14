/**
 * WorkspaceWizard Component
 * Multi-step workspace creation wizard
 *
 * T090: Create WorkspaceWizard multi-step component
 * T116: Add state restoration logic to WorkspaceWizard
 */

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { onboardingApi } from '../../services/onboarding-api';
import { useOnboardingState } from '../../hooks/useOnboardingState';
import { AppButton } from '../ui/AppButton';
import { AppInput } from '../ui/AppInput';
import { AppCard } from '../ui/AppCard';
import { SlugInput } from './SlugInput';
import type { BusinessType, WorkspaceResponse } from '../../types/onboarding';
import { cn } from '../../lib/utils';

// ============================================
// Icons
// ============================================

function BuildingIcon({ className }: { className?: string }) {
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
      <rect width="16" height="20" x="4" y="2" rx="2" ry="2" />
      <path d="M9 22v-4h6v4" />
      <path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m12 19-7-7 7-7" />
      <path d="M19 12H5" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface WorkspaceWizardProps {
  /** Callback when workspace is created */
  onComplete?: (workspace: WorkspaceResponse) => void;
  /** Additional class names */
  className?: string;
}

type WizardStep = 'name' | 'url' | 'type';

// ============================================
// Business Type Options
// ============================================

const businessTypes: { value: BusinessType; label: string; description: string }[] = [
  { value: 'wedding', label: 'Wedding', description: 'Wedding & engagement photography' },
  { value: 'portrait', label: 'Portrait', description: 'Personal & professional portraits' },
  { value: 'event', label: 'Events', description: 'Corporate & social events' },
  { value: 'family', label: 'Family', description: 'Family & lifestyle photography' },
  { value: 'newborn', label: 'Newborn', description: 'Newborn & maternity sessions' },
  { value: 'commercial', label: 'Commercial', description: 'Brand & product photography' },
  { value: 'real_estate', label: 'Real Estate', description: 'Property & architecture' },
  { value: 'product', label: 'Product', description: 'E-commerce & catalog' },
  { value: 'other', label: 'Other', description: 'Other photography types' },
];

// ============================================
// Step Indicator
// ============================================

interface StepIndicatorProps {
  steps: { id: WizardStep; label: string }[];
  currentStep: WizardStep;
  completedSteps: WizardStep[];
}

function StepIndicator({ steps, currentStep, completedSteps }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {steps.map((step, index) => {
        const isCompleted = completedSteps.includes(step.id);
        const isCurrent = step.id === currentStep;
        const stepNumber = index + 1;

        return (
          <div key={step.id} className="flex items-center">
            {/* Step circle */}
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center',
                'border-2 transition-all duration-300',
                isCompleted && 'bg-primary-500 border-primary-500',
                isCurrent && !isCompleted && 'border-primary-500 text-primary-400',
                !isCurrent && !isCompleted && 'border-white/20 text-white/40'
              )}
            >
              {isCompleted ? (
                <CheckIcon className="w-4 h-4 text-white" />
              ) : (
                <span className="text-sm font-medium">{stepNumber}</span>
              )}
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  'w-8 h-0.5 mx-1 transition-colors duration-300',
                  isCompleted ? 'bg-primary-500' : 'bg-white/20'
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ============================================
// Component
// ============================================

const wizardSteps: { id: WizardStep; label: string }[] = [
  { id: 'name', label: 'Name' },
  { id: 'url', label: 'URL' },
  { id: 'type', label: 'Type' },
];

export function WorkspaceWizard({ onComplete, className }: WorkspaceWizardProps) {
  const {
    workspaceData,
    updateWorkspaceData,
    markStepCompleted,
    saveProgress,
    isSaving,
  } = useOnboardingState();

  const [step, setStep] = useState<WizardStep>('name');
  const [completedSteps, setCompletedSteps] = useState<WizardStep[]>([]);

  // Create workspace mutation
  const createMutation = useMutation({
    mutationFn: () =>
      onboardingApi.createWorkspace({
        name: workspaceData.name!,
        slug: workspaceData.slug!,
        business_type: workspaceData.businessType!,
      }),
    onSuccess: (workspace) => {
      markStepCompleted('workspace_setup');
      onComplete?.(workspace);
    },
  });

  // Navigation
  const goNext = useCallback(() => {
    const currentIndex = wizardSteps.findIndex((s) => s.id === step);
    if (currentIndex < wizardSteps.length - 1) {
      setCompletedSteps((prev) => [...new Set([...prev, step])]);
      setStep(wizardSteps[currentIndex + 1].id);
      saveProgress();
    }
  }, [step, saveProgress]);

  const goBack = useCallback(() => {
    const currentIndex = wizardSteps.findIndex((s) => s.id === step);
    if (currentIndex > 0) {
      setStep(wizardSteps[currentIndex - 1].id);
    }
  }, [step]);

  // Submit
  const handleSubmit = async () => {
    await createMutation.mutateAsync();
  };

  // Validation
  const isNameValid = Boolean(workspaceData.name && workspaceData.name.length >= 2);
  const isSlugValid = Boolean(workspaceData.slug && workspaceData.slug.length >= 3);
  const isTypeValid = Boolean(workspaceData.businessType);

  const canProceed =
    (step === 'name' && isNameValid) ||
    (step === 'url' && isSlugValid) ||
    (step === 'type' && isTypeValid);

  return (
    <AppCard variant="glass" padding="lg" className={cn('w-full max-w-lg', className)}>
      {/* Header */}
      <div className="text-center mb-6">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mx-auto mb-4">
          <BuildingIcon className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Create Your Workspace</h1>
        <p className="text-white/60">Set up your photography business on vDrive</p>
      </div>

      {/* Step Indicator */}
      <StepIndicator
        steps={wizardSteps}
        currentStep={step}
        completedSteps={completedSteps}
      />

      {/* Step Content */}
      <div className="min-h-[200px]">
        {/* Step 1: Name */}
        {step === 'name' && (
          <div className="space-y-6 animate-fade-up">
            <div>
              <h2 className="text-lg font-semibold text-white mb-2">
                What's your business name?
              </h2>
              <p className="text-sm text-white/60">
                This is how clients will see your studio.
              </p>
            </div>
            <AppInput
              label="Business Name"
              value={workspaceData.name || ''}
              onChange={(e) => updateWorkspaceData({ name: e.target.value })}
              placeholder="e.g., Sarah's Photography"
              leftIcon={<BuildingIcon className="w-5 h-5" />}
              autoFocus
            />
          </div>
        )}

        {/* Step 2: URL */}
        {step === 'url' && (
          <div className="space-y-6 animate-fade-up">
            <div>
              <h2 className="text-lg font-semibold text-white mb-2">
                Choose your gallery URL
              </h2>
              <p className="text-sm text-white/60">
                This will be your unique link for sharing galleries.
              </p>
            </div>
            <SlugInput
              value={workspaceData.slug || ''}
              onChange={(slug) => updateWorkspaceData({ slug })}
              workspaceName={workspaceData.name}
            />
          </div>
        )}

        {/* Step 3: Business Type */}
        {step === 'type' && (
          <div className="space-y-6 animate-fade-up">
            <div>
              <h2 className="text-lg font-semibold text-white mb-2">
                What type of photography?
              </h2>
              <p className="text-sm text-white/60">
                This helps us customize your experience.
              </p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {businessTypes.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => updateWorkspaceData({ businessType: type.value })}
                  className={cn(
                    'p-3 rounded-xl border text-left transition-all duration-200',
                    workspaceData.businessType === type.value
                      ? 'bg-primary-500/20 border-primary-500/50 ring-2 ring-primary-500/30'
                      : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                  )}
                >
                  <p className="font-medium text-white text-sm">{type.label}</p>
                  <p className="text-xs text-white/50 mt-0.5 line-clamp-1">
                    {type.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {createMutation.isError && (
        <div
          className="mt-4 p-3 rounded-lg bg-error-500/20 border border-error-500/30 text-error-400 text-sm"
          role="alert"
        >
          {(createMutation.error as { message?: string })?.message ||
            'Failed to create workspace'}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between mt-8 pt-6 border-t border-white/10">
        {step !== 'name' ? (
          <AppButton
            variant="ghost"
            onClick={goBack}
            leftIcon={<ArrowLeftIcon className="w-4 h-4" />}
          >
            Back
          </AppButton>
        ) : (
          <div />
        )}

        {step !== 'type' ? (
          <AppButton
            variant="primary"
            onClick={goNext}
            disabled={!canProceed}
            rightIcon={<ArrowRightIcon className="w-4 h-4" />}
          >
            Continue
          </AppButton>
        ) : (
          <AppButton
            variant="accent"
            onClick={handleSubmit}
            disabled={!canProceed}
            isLoading={createMutation.isPending || isSaving}
          >
            Create Workspace
          </AppButton>
        )}
      </div>
    </AppCard>
  );
}

export default WorkspaceWizard;
