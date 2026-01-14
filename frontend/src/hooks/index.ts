// Custom Hooks
export {
  useTheme,
  ThemeProvider,
  usePrefersReducedMotion,
  type Theme,
  type ResolvedTheme,
  type ThemeContextValue,
  type ThemeProviderProps,
} from './useTheme';

export {
  useRegistration,
  type RegistrationFormData,
  type RegistrationFormErrors,
  type PasswordStrength,
  type UseRegistrationOptions,
  type UseRegistrationReturn,
} from './useRegistration';

export {
  useOnboardingState,
  type WorkspaceFormData,
  type UseOnboardingStateReturn,
} from './useOnboardingState';
