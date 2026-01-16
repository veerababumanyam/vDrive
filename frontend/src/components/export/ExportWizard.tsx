/**
 * ExportWizard Component
 * Multi-step export wizard for creating export jobs
 *
 * Subtask-4-2: Create export wizard component
 */

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { createExportJob } from '../../services/export-api';
import type { ExportType, ExportOptions as ExportOptionsType, ExportResponse } from '../../services/export-api';
import { AppButton } from '../ui/AppButton';
import { AppCard } from '../ui/AppCard';
import { ExportOptions } from './ExportOptions';
import { cn } from '../../lib/utils';

// ============================================
// Icons
// ============================================

function DownloadIcon({ className }: { className?: string }) {
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
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" x2="12" y1="15" y2="3" />
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

export interface ExportWizardProps {
  /** Callback when export is created */
  onComplete?: (exportJob: ExportResponse) => void;
  /** Additional class names */
  className?: string;
}

type WizardStep = 'configure' | 'confirm';

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
  { id: 'configure', label: 'Configure' },
  { id: 'confirm', label: 'Confirm' },
];

export function ExportWizard({ onComplete, className }: ExportWizardProps) {
  const [step, setStep] = useState<WizardStep>('configure');
  const [completedSteps, setCompletedSteps] = useState<WizardStep[]>([]);

  // Export configuration
  const [exportType, setExportType] = useState<ExportType | null>(null);
  const [options, setOptions] = useState<ExportOptionsType>({
    include_metadata: true,
    include_thumbnails: false,
  });

  // Create export mutation
  const createMutation = useMutation({
    mutationFn: () => {
      if (!exportType) {
        throw new Error('Export type is required');
      }
      return createExportJob({
        export_type: exportType,
        options,
      });
    },
    onSuccess: (exportJob) => {
      onComplete?.(exportJob);
    },
  });

  // Navigation
  const goNext = useCallback(() => {
    if (step === 'configure') {
      setCompletedSteps((prev) => [...new Set([...prev, step])]);
      setStep('confirm');
    }
  }, [step]);

  const goBack = useCallback(() => {
    if (step === 'confirm') {
      setStep('configure');
    }
  }, [step]);

  // Submit
  const handleSubmit = async () => {
    await createMutation.mutateAsync();
  };

  // Validation
  const canProceed = exportType !== null;

  // Get export type label
  const getExportTypeLabel = () => {
    switch (exportType) {
      case 'workspace':
        return 'Full Workspace';
      case 'gallery':
        return 'Specific Galleries';
      case 'selection':
        return 'Selected Photos';
      default:
        return '';
    }
  };

  return (
    <AppCard variant="glass" padding="lg" className={cn('w-full max-w-2xl', className)}>
      {/* Header */}
      <div className="text-center mb-6">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mx-auto mb-4">
          <DownloadIcon className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Export Your Photos</h1>
        <p className="text-white/60">Download your photos and data in bulk</p>
      </div>

      {/* Step Indicator */}
      <StepIndicator
        steps={wizardSteps}
        currentStep={step}
        completedSteps={completedSteps}
      />

      {/* Step Content */}
      <div className="min-h-[300px]">
        {/* Step 1: Configure */}
        {step === 'configure' && (
          <div className="animate-fade-up">
            <ExportOptions
              exportType={exportType}
              options={options}
              onExportTypeChange={setExportType}
              onOptionsChange={setOptions}
            />
          </div>
        )}

        {/* Step 2: Confirm */}
        {step === 'confirm' && (
          <div className="space-y-6 animate-fade-up">
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                Review your export
              </h2>
              <p className="text-sm text-white/60 mb-6">
                Please confirm the details before creating your export job.
              </p>
            </div>

            {/* Summary */}
            <div className="space-y-4">
              {/* Export Type */}
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-white/50 mb-1">Export Type</p>
                <p className="text-white font-medium">{getExportTypeLabel()}</p>
              </div>

              {/* Options */}
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-white/50 mb-2">Options</p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <div className={cn(
                      'w-4 h-4 rounded flex items-center justify-center',
                      options.include_metadata
                        ? 'bg-primary-500 text-white'
                        : 'bg-white/10 text-white/40'
                    )}>
                      {options.include_metadata && <CheckIcon className="w-3 h-3" />}
                    </div>
                    <span className="text-white/70">Include metadata</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className={cn(
                      'w-4 h-4 rounded flex items-center justify-center',
                      options.include_thumbnails
                        ? 'bg-primary-500 text-white'
                        : 'bg-white/10 text-white/40'
                    )}>
                      {options.include_thumbnails && <CheckIcon className="w-3 h-3" />}
                    </div>
                    <span className="text-white/70">Include thumbnails</span>
                  </div>
                </div>
              </div>

              {/* Info */}
              <div className="p-4 rounded-xl bg-accent-500/10 border border-accent-500/20">
                <p className="text-sm text-white/70">
                  <span className="font-medium text-white">Note:</span> Large exports may take several minutes to process.
                  You'll be able to download the ZIP file once processing is complete.
                </p>
              </div>
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
            'Failed to create export job'}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between mt-8 pt-6 border-t border-white/10">
        {step !== 'configure' ? (
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

        {step !== 'confirm' ? (
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
            isLoading={createMutation.isPending}
          >
            Create Export
          </AppButton>
        )}
      </div>
    </AppCard>
  );
}

export default ExportWizard;
