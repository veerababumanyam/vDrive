/**
 * useLogin Hook
 * Handles login form state, validation, and submission
 */

import { useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { login as loginApi } from '../services/onboarding-api';
import { setTokenInMemory } from '../services/authService';
import type { ApiError } from '../types/onboarding';

// ============================================
// Types
// ============================================

export interface LoginFormData {
  email: string;
  password: string;
}

export interface LoginErrors {
  email?: string;
  password?: string;
  general?: string;
}

export interface UseLoginOptions {
  onSuccess?: (response: import('../types/onboarding').LoginResponse) => void;
  onError?: (error: string) => void;
}

export interface UseLoginReturn {
  formData: LoginFormData;
  updateField: (field: keyof LoginFormData, value: string) => void;
  errors: LoginErrors;
  isValid: boolean;
  validateField: (field: keyof LoginFormData) => void;
  isSubmitting: boolean;
  submit: () => Promise<boolean>;
  clearErrors: () => void;
}

// ============================================
// Validation
// ============================================

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateEmail(email: string): string | undefined {
  if (!email.trim()) {
    return 'Email is required';
  }
  if (!EMAIL_REGEX.test(email)) {
    return 'Please enter a valid email address';
  }
  return undefined;
}

function validatePassword(password: string): string | undefined {
  if (!password) {
    return 'Password is required';
  }
  return undefined;
}

// ============================================
// Hook
// ============================================

export function useLogin(options: UseLoginOptions = {}): UseLoginReturn {
  const { onSuccess, onError } = options;
  const { setUser, setAccessToken } = useAuth();

  // Form state
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });

  // Validation errors
  const [errors, setErrors] = useState<LoginErrors>({});

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update a single field
  const updateField = useCallback((field: keyof LoginFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    setErrors((prev) => ({ ...prev, [field]: undefined, general: undefined }));
  }, []);

  // Validate a single field
  const validateField = useCallback((field: keyof LoginFormData) => {
    let error: string | undefined;

    switch (field) {
      case 'email':
        error = validateEmail(formData.email);
        break;
      case 'password':
        error = validatePassword(formData.password);
        break;
    }

    setErrors((prev) => ({ ...prev, [field]: error }));
    return !error;
  }, [formData]);

  // Check if form is valid
  const isValid =
    formData.email.trim() !== '' &&
    formData.password !== '' &&
    !errors.email &&
    !errors.password;

  // Clear all errors
  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  // Submit login
  const submit = useCallback(async (): Promise<boolean> => {
    // Validate all fields first
    const emailError = validateEmail(formData.email);
    const passwordError = validatePassword(formData.password);

    if (emailError || passwordError) {
      setErrors({
        email: emailError,
        password: passwordError,
      });
      return false;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await loginApi({
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
      });


      // Map API response to AuthContext User type
      const user = {
        id: response.user_id,
        email: response.email,
        first_name: response.full_name.split(' ')[0],
        last_name: response.full_name.split(' ').slice(1).join(' ') || '',
        email_verified: response.email_verified,
      };

      // DEBUG: Log login response for troubleshooting
      console.log('[useLogin] Login successful, setting token...');
      console.log('[useLogin] Access token present:', !!response.access_token);

      // SECURITY: Store access token in memory (for axios interceptor)
      setTokenInMemory(response.access_token);

      // Save user to localStorage (for session persistence across page refresh)
      localStorage.setItem('user', JSON.stringify(user));

      // Update global auth state (React context)
      setUser(user);
      setAccessToken(response.access_token);

      console.log('[useLogin] Token set complete');



      onSuccess?.(response);
      return true;
    } catch (err) {
      const apiError = err as ApiError;
      let errorMessage = 'An unexpected error occurred';

      // Handle specific error codes
      if (apiError.error === 'InvalidCredentials' || apiError.error === 'invalid_credentials') {
        errorMessage = 'Invalid email or password';
      } else if (apiError.error === 'EmailNotVerified' || apiError.error === 'email_not_verified') {
        errorMessage = 'Please verify your email before signing in';
      } else if (apiError.error === 'AccountLocked' || apiError.error === 'account_locked') {
        errorMessage = 'Your account has been locked. Please contact support.';
      } else if (apiError.message) {
        errorMessage = apiError.message;
      }

      setErrors({ general: errorMessage });
      onError?.(errorMessage);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, onSuccess, onError]);

  return {
    formData,
    updateField,
    errors,
    isValid,
    validateField,
    isSubmitting,
    submit,
    clearErrors,
  };
}

export default useLogin;
