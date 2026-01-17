/**
 * MigrationWizard Component
 * Multi-step migration wizard for importing from external platforms
 *
 * Subtask-5-4: Create migration wizard UI component
 */

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { createMigrationJob, type MigrationPlatform, type MigrationCredentials, type MigrationResponse } from '../../services/migration-api';
import { AppButton } from '../ui/AppButton';
import { AppCard } from '../ui/AppCard';
import { PlatformSelector } from './PlatformSelector';
import { CredentialsForm } from './CredentialsForm';
import { cn } from '../../lib/utils';

// ============================================
// Icons
// ============================================

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

function UploadIcon({ className }: { className?: string }) {
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
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" x2="12" y1="3" y2="15" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface MigrationWizardProps {
  /** Callback when migration is created */
  onComplete?: (migration: MigrationResponse) => void;
  /** Additional class names */
  className?: string;
}

type WizardStep = 'platform' | 'credentials' | 'confirm';

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
  { id: 'platform', label: 'Platform' },
  { id: 'credentials', label: 'Credentials' },
  { id: 'confirm', label: 'Confirm' },
];

export function MigrationWizard({ onComplete, className }: MigrationWizardProps) {
  const [step, setStep] = useState<WizardStep>('platform');
  const [completedSteps, setCompletedSteps] = useState<WizardStep[]>([]);

  // Migration configuration
  const [platform, setPlatform] = useState<MigrationPlatform | null>(null);
  const [credentials, setCredentials] = useState<Partial<MigrationCredentials>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Create migration mutation
  const createMutation = useMutation({
    mutationFn: () => {
      if (!platform) {
        throw new Error('Platform is required');
      }
      return createMigrationJob({
        credentials: {
          platform,
          ...credentials,
        } as MigrationCredentials,
        options: {
          include_metadata: true,
          preserve_structure: true,
        },
      });
    },
    onSuccess: (migration) => {
      onComplete?.(migration);
    },
  });

  // Validate credentials based on platform
  const validateCredentials = useCallback(() => {
    const errors: Record<string, string> = {};

    if (!platform) {
      return errors;
    }

    switch (platform) {
      case 'pixieset':
        if (!credentials.api_key?.trim()) {
          errors.api_key = 'API key is required';
        }
        break;

      case 'pictime':
        if (!credentials.username?.trim()) {
          errors.username = 'Username is required';
        }
        if (!credentials.password?.trim()) {
          errors.password = 'Password is required';
        }
        break;

      case 'shootproof':
      case 'zenfolio':
        if (!credentials.api_key?.trim()) {
          errors.api_key = 'API key is required';
        }
        if (!credentials.api_secret?.trim()) {
          errors.api_secret = 'API secret is required';
        }
        break;

      case 'smugmug':
        if (!credentials.access_token?.trim()) {
          errors.access_token = 'Access token is required';
        }
        break;
    }

    return errors;
  }, [platform, credentials]);

  // Navigation
  const goNext = useCallback(() => {
    if (step === 'platform') {
      if (!platform) {
        return;
      }
      setCompletedSteps((prev) => [...new Set([...prev, step])]);
      setStep('credentials');
    } else if (step === 'credentials') {
      const errors = validateCredentials();
      if (Object.keys(errors).length > 0) {
        setValidationErrors(errors);
        return;
      }
      setValidationErrors({});
      setCompletedSteps((prev) => [...new Set([...prev, step])]);
      setStep('confirm');
    }
  }, [step, platform, validateCredentials]);

  const goBack = useCallback(() => {
    if (step === 'credentials') {
      setStep('platform');
    } else if (step === 'confirm') {
      setStep('credentials');
    }
  }, [step]);

  const handleSubmit = useCallback(() => {
    createMutation.mutate();
  }, [createMutation]);

  // Check if can proceed to next step
  const canProceed = useCallback(() => {
    if (step === 'platform') {
      return platform !== null;
    }
    if (step === 'credentials') {
      return Object.keys(validateCredentials()).length === 0;
    }
    return true;
  }, [step, platform, validateCredentials]);

  return (
    <AppCard className={cn('max-w-3xl mx-auto', className)}>
      <div className="p-6 sm:p-8">
        {/* Step Indicator */}
        <StepIndicator
          steps={wizardSteps}
          currentStep={step}
          completedSteps={completedSteps}
        />

        {/* Step Content */}
        <div className="min-h-[400px]">
          {step === 'platform' && (
            <PlatformSelector
              selectedPlatform={platform}
              onPlatformChange={setPlatform}
            />
          )}

          {step === 'credentials' && platform && (
            <CredentialsForm
              platform={platform}
              credentials={credentials}
              onCredentialsChange={setCredentials}
              errors={validationErrors}
            />
          )}

          {step === 'confirm' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">
                  Ready to start migration
                </h3>
                <p className="text-white/60 mb-6">
                  We'll connect to your account and import all galleries and photos. This process may take
                  some time depending on the amount of data.
                </p>
              </div>

              <div className="p-6 rounded-xl bg-white/5 border border-white/10 space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center shrink-0">
                    <UploadIcon className="w-5 h-5 text-primary-400" />
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Migration Summary</p>
                    <ul className="space-y-2 text-sm text-white/60">
                      <li>• Platform: {platform}</li>
                      <li>• Include metadata: Yes</li>
                      <li>• Preserve structure: Yes</li>
                      <li>• All galleries will be imported</li>
                    </ul>
                  </div>
                </div>
              </div>

              {createMutation.isError && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                  <p className="text-sm text-red-400">
                    <span className="font-medium">Error:</span>{' '}
                    {createMutation.error instanceof Error
                      ? createMutation.error.message
                      : 'Failed to start migration. Please check your credentials and try again.'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/10">
          <AppButton
            variant="ghost"
            onClick={goBack}
            disabled={step === 'platform' || createMutation.isPending}
          >
            <ArrowLeftIcon className="w-4 h-4 mr-2" />
            Back
          </AppButton>

          {step !== 'confirm' ? (
            <AppButton
              onClick={goNext}
              disabled={!canProceed()}
            >
              Next
              <ArrowRightIcon className="w-4 h-4 ml-2" />
            </AppButton>
          ) : (
            <AppButton
              onClick={handleSubmit}
              disabled={createMutation.isPending}
              loading={createMutation.isPending}
            >
              Start Migration
              <ArrowRightIcon className="w-4 h-4 ml-2" />
            </AppButton>
          )}
        </div>
      </div>
    </AppCard>
  );
}

export default MigrationWizard;
