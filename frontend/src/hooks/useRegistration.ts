/**
 * useRegistration Hook
 * Manages registration form state, validation, and API calls
 *
 * T049: Create useRegistration hook with form state and validation
 */

import { useState, useCallback, useMemo } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { onboardingApi } from '../services/onboarding-api';
import type {
  RegistrationRequest,
  RegistrationResponse,
  EmailCheckResponse,
  ApiError,
} from '../types/onboarding';
import { debounce } from '../lib/utils';

// ============================================
// Types
// ============================================

export interface RegistrationFormData {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
}

export interface RegistrationFormErrors {
  email?: string;
  password?: string;
  confirmPassword?: string;
  fullName?: string;
  turnstile?: string;
  general?: string;
}

export interface PasswordStrength {
  score: number; // 0-4
  label: 'Very Weak' | 'Weak' | 'Fair' | 'Strong' | 'Very Strong';
  color: string;
  feedback: string[];
}

export interface UseRegistrationOptions {
  onSuccess?: (response: RegistrationResponse) => void;
  onError?: (error: ApiError) => void;
}

export interface UseRegistrationReturn {
  // Form data
  formData: RegistrationFormData;
  setFormData: React.Dispatch<React.SetStateAction<RegistrationFormData>>;
  updateField: (field: keyof RegistrationFormData, value: string) => void;

  // Validation
  errors: RegistrationFormErrors;
  isValid: boolean;
  validateField: (field: keyof RegistrationFormData) => boolean;
  validateForm: () => boolean;

  // Password strength
  passwordStrength: PasswordStrength;

  // Email availability
  isCheckingEmail: boolean;
  emailAvailable: boolean | null;

  // Turnstile
  turnstileToken: string | null;
  setTurnstileToken: (token: string | null) => void;

  // Submission
  isSubmitting: boolean;
  submitError: ApiError | null;
  submit: () => Promise<void>;

  // Reset
  reset: () => void;
}

// ============================================
// Validation Helpers
// ============================================

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

/**
 * Calculate password strength score (0-4)
 */
function calculatePasswordStrength(password: string): PasswordStrength {
  const feedback: string[] = [];
  let score = 0;

  if (password.length === 0) {
    return {
      score: 0,
      label: 'Very Weak',
      color: 'bg-neutral-600',
      feedback: ['Enter a password'],
    };
  }

  // Length check
  if (password.length >= MIN_PASSWORD_LENGTH) {
    score += 1;
  } else {
    feedback.push(`At least ${MIN_PASSWORD_LENGTH} characters`);
  }

  // Uppercase check
  if (/[A-Z]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add uppercase letter');
  }

  // Lowercase check
  if (/[a-z]/.test(password)) {
    score += 0.5;
  } else {
    feedback.push('Add lowercase letter');
  }

  // Number check
  if (/[0-9]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add a number');
  }

  // Special character check
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add special character');
  }

  // Length bonus
  if (password.length >= 12) {
    score += 0.5;
  }

  // Round score to 0-4
  const finalScore = Math.min(4, Math.round(score));

  const labels: PasswordStrength['label'][] = [
    'Very Weak',
    'Weak',
    'Fair',
    'Strong',
    'Very Strong',
  ];

  const colors = [
    'bg-error-500',
    'bg-warning-500',
    'bg-warning-500',
    'bg-success-500',
    'bg-primary-500',
  ];

  return {
    score: finalScore,
    label: labels[finalScore],
    color: colors[finalScore],
    feedback: feedback.slice(0, 2), // Show max 2 feedback items
  };
}

/**
 * Validate email format
 */
function validateEmail(email: string): string | undefined {
  if (!email.trim()) {
    return 'Email is required';
  }
  if (!EMAIL_REGEX.test(email)) {
    return 'Enter a valid email address';
  }
  return undefined;
}

/**
 * Validate password
 */
function validatePassword(password: string): string | undefined {
  if (!password) {
    return 'Password is required';
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
  }
  return undefined;
}

/**
 * Validate password confirmation
 */
function validateConfirmPassword(
  password: string,
  confirmPassword: string
): string | undefined {
  if (!confirmPassword) {
    return 'Please confirm your password';
  }
  if (password !== confirmPassword) {
    return 'Passwords do not match';
  }
  return undefined;
}

/**
 * Validate full name
 */
function validateFullName(fullName: string): string | undefined {
  if (!fullName.trim()) {
    return 'Full name is required';
  }
  if (fullName.trim().length < 2) {
    return 'Name is too short';
  }
  return undefined;
}

// ============================================
// Hook Implementation
// ============================================

const initialFormData: RegistrationFormData = {
  email: '',
  password: '',
  confirmPassword: '',
  fullName: '',
};

export function useRegistration(
  options: UseRegistrationOptions = {}
): UseRegistrationReturn {
  const { onSuccess, onError } = options;

  // Form state
  const [formData, setFormData] = useState<RegistrationFormData>(initialFormData);
  const [errors, setErrors] = useState<RegistrationFormErrors>({});
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [emailToCheck, setEmailToCheck] = useState<string>('');

  // Debounced email check
  const debouncedSetEmailToCheck = useMemo(
    () => debounce((email: string) => setEmailToCheck(email), 500),
    []
  );

  // Email availability check
  const {
    data: emailCheckData,
    isLoading: isCheckingEmail,
  } = useQuery<EmailCheckResponse>({
    queryKey: ['emailCheck', emailToCheck],
    queryFn: () => onboardingApi.checkEmail(emailToCheck),
    enabled: Boolean(emailToCheck) && EMAIL_REGEX.test(emailToCheck),
    staleTime: 30000, // Cache for 30 seconds
  });

  const emailAvailable = emailCheckData?.available ?? null;

  // Registration mutation
  const registrationMutation = useMutation<
    RegistrationResponse,
    ApiError,
    RegistrationRequest
  >({
    mutationFn: onboardingApi.register,
    onSuccess: (response) => {
      onSuccess?.(response);
    },
    onError: (error) => {
      setErrors((prev) => ({
        ...prev,
        general: error.message,
      }));
      onError?.(error);
    },
  });

  // Password strength
  const passwordStrength = useMemo(
    () => calculatePasswordStrength(formData.password),
    [formData.password]
  );

  // Update a single field
  const updateField = useCallback(
    (field: keyof RegistrationFormData, value: string) => {
      setFormData((prev) => ({ ...prev, [field]: value }));

      // Clear field error on change
      setErrors((prev) => ({ ...prev, [field]: undefined }));

      // Trigger email availability check
      if (field === 'email' && EMAIL_REGEX.test(value)) {
        debouncedSetEmailToCheck(value);
      }
    },
    [debouncedSetEmailToCheck]
  );

  // Validate a single field
  const validateField = useCallback(
    (field: keyof RegistrationFormData): boolean => {
      let error: string | undefined;

      switch (field) {
        case 'email':
          error = validateEmail(formData.email);
          if (!error && emailAvailable === false) {
            error = 'This email is already registered';
          }
          break;
        case 'password':
          error = validatePassword(formData.password);
          break;
        case 'confirmPassword':
          error = validateConfirmPassword(
            formData.password,
            formData.confirmPassword
          );
          break;
        case 'fullName':
          error = validateFullName(formData.fullName);
          break;
      }

      setErrors((prev) => ({ ...prev, [field]: error }));
      return !error;
    },
    [formData, emailAvailable]
  );

  // Validate entire form
  const validateForm = useCallback((): boolean => {
    const emailError = validateEmail(formData.email);
    const passwordError = validatePassword(formData.password);
    const confirmPasswordError = validateConfirmPassword(
      formData.password,
      formData.confirmPassword
    );
    const fullNameError = validateFullName(formData.fullName);
    const turnstileError = !turnstileToken ? 'Please complete the captcha' : undefined;

    const newErrors: RegistrationFormErrors = {
      email:
        emailError || (emailAvailable === false ? 'Email already registered' : undefined),
      password: passwordError,
      confirmPassword: confirmPasswordError,
      fullName: fullNameError,
      turnstile: turnstileError,
    };

    setErrors(newErrors);

    return !Object.values(newErrors).some(Boolean);
  }, [formData, emailAvailable, turnstileToken]);

  // Check if form is valid (for button state)
  const isValid = useMemo(() => {
    return (
      Boolean(formData.email) &&
      Boolean(formData.password) &&
      Boolean(formData.confirmPassword) &&
      Boolean(formData.fullName) &&
      Boolean(turnstileToken) &&
      formData.password === formData.confirmPassword &&
      passwordStrength.score >= 2 &&
      emailAvailable !== false
    );
  }, [formData, turnstileToken, passwordStrength.score, emailAvailable]);

  // Submit form
  const submit = useCallback(async () => {
    if (!validateForm()) {
      return;
    }

    if (!turnstileToken) {
      setErrors((prev) => ({ ...prev, turnstile: 'Please complete the captcha' }));
      return;
    }

    await registrationMutation.mutateAsync({
      email: formData.email.trim(),
      password: formData.password,
      full_name: formData.fullName.trim(),
      turnstile_token: turnstileToken,
    });
  }, [formData, turnstileToken, validateForm, registrationMutation]);

  // Reset form
  const reset = useCallback(() => {
    setFormData(initialFormData);
    setErrors({});
    setTurnstileToken(null);
    setEmailToCheck('');
    registrationMutation.reset();
  }, [registrationMutation]);

  return {
    // Form data
    formData,
    setFormData,
    updateField,

    // Validation
    errors,
    isValid,
    validateField,
    validateForm,

    // Password strength
    passwordStrength,

    // Email availability
    isCheckingEmail,
    emailAvailable,

    // Turnstile
    turnstileToken,
    setTurnstileToken,

    // Submission
    isSubmitting: registrationMutation.isPending,
    submitError: registrationMutation.error ?? null,
    submit,

    // Reset
    reset,
  };
}

export default useRegistration;
