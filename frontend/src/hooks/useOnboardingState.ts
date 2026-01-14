/**
 * useOnboardingState Hook
 * Manages onboarding wizard state with API persistence
 *
 * T089: Create useOnboardingState hook for wizard state
 * T115: Extend useOnboardingState hook with API persistence
 */

import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { onboardingApi } from '../services/onboarding-api';
import type {
  OnboardingStateResponse,
  OnboardingStep,
  WorkspaceCreateRequest,
} from '../types/onboarding';

// ============================================
// Types
// ============================================

export interface WorkspaceFormData {
  name: string;
  slug: string;
  businessType: WorkspaceCreateRequest['business_type'];
}

export interface UseOnboardingStateReturn {
  // Current step
  currentStep: OnboardingStep;
  setCurrentStep: (step: OnboardingStep) => void;

  // Completed steps
  completedSteps: OnboardingStep[];
  isStepCompleted: (step: OnboardingStep) => boolean;
  markStepCompleted: (step: OnboardingStep) => void;

  // Workspace data
  workspaceData: Partial<WorkspaceFormData>;
  updateWorkspaceData: (data: Partial<WorkspaceFormData>) => void;

  // Progress
  progress: number; // 0-100
  canProceed: boolean;

  // API state
  isLoading: boolean;
  isSaving: boolean;
  hasExistingProgress: boolean;

  // Actions
  saveProgress: () => Promise<void>;
  resetProgress: () => Promise<void>;
  completeOnboarding: () => Promise<void>;
}

// ============================================
// Constants
// ============================================

const STEPS: OnboardingStep[] = [
  'registration',
  'email_verification',
  'workspace_setup',
  'profile_setup',
  'completed',
];

const STORAGE_KEY = 'vdrive-onboarding-state';

// ============================================
// Local Storage Helpers
// ============================================

interface LocalState {
  currentStep: OnboardingStep;
  completedSteps: OnboardingStep[];
  workspaceData: Partial<WorkspaceFormData>;
}

function getLocalState(): LocalState | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function setLocalState(state: LocalState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage errors
  }
}

function clearLocalState(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore storage errors
  }
}

// ============================================
// Hook Implementation
// ============================================

export function useOnboardingState(): UseOnboardingStateReturn {
  const queryClient = useQueryClient();

  // Local state
  const [currentStep, setCurrentStepInternal] = useState<OnboardingStep>('workspace_setup');
  const [completedSteps, setCompletedSteps] = useState<OnboardingStep[]>([
    'registration',
    'email_verification',
  ]);
  const [workspaceData, setWorkspaceData] = useState<Partial<WorkspaceFormData>>({});
  const [isInitialized, setIsInitialized] = useState(false);

  // Fetch remote state
  const {
    data: remoteState,
    isLoading: isFetching,
    isSuccess: hasFetched,
  } = useQuery<OnboardingStateResponse>({
    queryKey: ['onboardingState'],
    queryFn: onboardingApi.getOnboardingState,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // Save state mutation
  const saveMutation = useMutation({
    mutationFn: () =>
      onboardingApi.updateOnboardingState({
        current_step: currentStep,
        completed_steps: completedSteps,
        workspace_data: workspaceData as Partial<WorkspaceCreateRequest>,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(['onboardingState'], data);
    },
  });

  // Reset state mutation
  const resetMutation = useMutation({
    mutationFn: onboardingApi.resetOnboardingState,
    onSuccess: () => {
      setCurrentStepInternal('workspace_setup');
      setCompletedSteps(['registration', 'email_verification']);
      setWorkspaceData({});
      clearLocalState();
      queryClient.invalidateQueries({ queryKey: ['onboardingState'] });
    },
  });

  // Complete onboarding mutation
  const completeMutation = useMutation({
    mutationFn: onboardingApi.completeOnboarding,
    onSuccess: () => {
      clearLocalState();
      queryClient.invalidateQueries({ queryKey: ['onboardingState'] });
    },
  });

  // Initialize from remote or local state
  useEffect(() => {
    if (isInitialized) return;

    // Try remote state first
    if (hasFetched && remoteState) {
      setCurrentStepInternal(remoteState.current_step);
      setCompletedSteps(remoteState.completed_steps);
      if (remoteState.workspace_data) {
        setWorkspaceData({
          name: remoteState.workspace_data.name,
          slug: remoteState.workspace_data.slug,
          businessType: remoteState.workspace_data.business_type,
        });
      }
      setIsInitialized(true);
      return;
    }

    // Fall back to local state
    if (!isFetching) {
      const localState = getLocalState();
      if (localState) {
        setCurrentStepInternal(localState.currentStep);
        setCompletedSteps(localState.completedSteps);
        setWorkspaceData(localState.workspaceData);
      }
      setIsInitialized(true);
    }
  }, [hasFetched, remoteState, isFetching, isInitialized]);

  // Persist to local storage on changes
  useEffect(() => {
    if (!isInitialized) return;

    setLocalState({
      currentStep,
      completedSteps,
      workspaceData,
    });
  }, [currentStep, completedSteps, workspaceData, isInitialized]);

  // Set current step
  const setCurrentStep = useCallback((step: OnboardingStep) => {
    setCurrentStepInternal(step);
  }, []);

  // Check if step is completed
  const isStepCompleted = useCallback(
    (step: OnboardingStep) => completedSteps.includes(step),
    [completedSteps]
  );

  // Mark step as completed
  const markStepCompleted = useCallback((step: OnboardingStep) => {
    setCompletedSteps((prev) => {
      if (prev.includes(step)) return prev;
      return [...prev, step];
    });
  }, []);

  // Update workspace data
  const updateWorkspaceData = useCallback((data: Partial<WorkspaceFormData>) => {
    setWorkspaceData((prev) => ({ ...prev, ...data }));
  }, []);

  // Calculate progress
  const progress = Math.round(
    (completedSteps.length / (STEPS.length - 1)) * 100
  );

  // Check if can proceed (workspace data is complete)
  const canProceed =
    Boolean(workspaceData.name) &&
    Boolean(workspaceData.slug) &&
    Boolean(workspaceData.businessType);

  // Save progress to API
  const saveProgress = useCallback(async () => {
    await saveMutation.mutateAsync();
  }, [saveMutation]);

  // Reset progress
  const resetProgress = useCallback(async () => {
    await resetMutation.mutateAsync();
  }, [resetMutation]);

  // Complete onboarding
  const completeOnboarding = useCallback(async () => {
    await completeMutation.mutateAsync();
  }, [completeMutation]);

  return {
    // Current step
    currentStep,
    setCurrentStep,

    // Completed steps
    completedSteps,
    isStepCompleted,
    markStepCompleted,

    // Workspace data
    workspaceData,
    updateWorkspaceData,

    // Progress
    progress,
    canProceed,

    // API state
    isLoading: isFetching,
    isSaving: saveMutation.isPending,
    hasExistingProgress: Boolean(remoteState || getLocalState()),

    // Actions
    saveProgress,
    resetProgress,
    completeOnboarding,
  };
}

export default useOnboardingState;
