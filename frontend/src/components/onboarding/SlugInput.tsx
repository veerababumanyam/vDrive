/**
 * SlugInput Component
 * Input with real-time slug availability check and suggestions
 *
 * T088: Create SlugInput component with real-time availability check
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { onboardingApi } from '../../services/onboarding-api';
import { AppInput } from '../ui/AppInput';
import { cn, debounce } from '../../lib/utils';

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

function XIcon({ className }: { className?: string }) {
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
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn('animate-spin', className)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

function LinkIcon({ className }: { className?: string }) {
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
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface SlugInputProps {
  /** Current slug value */
  value: string;
  /** Change handler */
  onChange: (value: string) => void;
  /** Workspace name for generating suggestions */
  workspaceName?: string;
  /** Error message */
  error?: string;
  /** Additional class names */
  className?: string;
}

// ============================================
// Helpers
// ============================================

/**
 * Convert text to URL-safe slug
 */
function toSlug(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove non-word chars
    .replace(/[\s_-]+/g, '-') // Replace spaces and underscores with hyphens
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
}

// ============================================
// Component
// ============================================

/**
 * Slug input with real-time availability check and suggestions
 *
 * @example
 * ```tsx
 * <SlugInput
 *   value={slug}
 *   onChange={setSlug}
 *   workspaceName="My Studio"
 * />
 * ```
 */
export function SlugInput({
  value,
  onChange,
  workspaceName = '',
  error,
  className,
}: SlugInputProps) {
  const [slugToCheck, setSlugToCheck] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Debounced slug check
  const debouncedSetSlugToCheck = useMemo(
    () => debounce((slug: string) => setSlugToCheck(slug), 400),
    []
  );

  // Check slug availability
  const {
    data: checkResult,
    isLoading: isChecking,
  } = useQuery({
    queryKey: ['slugCheck', slugToCheck],
    queryFn: () => onboardingApi.checkSlug(slugToCheck),
    enabled: Boolean(slugToCheck) && slugToCheck.length >= 3,
    staleTime: 30000,
  });

  // Get slug suggestions
  const {
    data: suggestionsResult,
    isLoading: isLoadingSuggestions,
  } = useQuery({
    queryKey: ['slugSuggest', workspaceName],
    queryFn: () => onboardingApi.suggestSlug(workspaceName),
    enabled: Boolean(workspaceName) && workspaceName.length >= 2 && !value,
    staleTime: 60000,
  });

  const isAvailable = checkResult?.available ?? null;
  const suggestions = suggestionsResult?.suggestions ?? checkResult?.suggestions ?? [];

  // Handle input change
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = toSlug(e.target.value);
      onChange(newValue);
      debouncedSetSlugToCheck(newValue);
    },
    [onChange, debouncedSetSlugToCheck]
  );

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    onChange(suggestion);
    setSlugToCheck(suggestion);
    setShowSuggestions(false);
  };

  // Auto-generate slug from workspace name
  useEffect(() => {
    if (!value && workspaceName) {
      const generatedSlug = toSlug(workspaceName);
      if (generatedSlug.length >= 3) {
        onChange(generatedSlug);
        debouncedSetSlugToCheck(generatedSlug);
      }
    }
  }, [workspaceName]);

  // Get status icon
  const getStatusIcon = () => {
    if (!value || value.length < 3) return null;
    if (isChecking) {
      return <LoaderIcon className="w-5 h-5 text-white/50" />;
    }
    if (isAvailable === true) {
      return <CheckIcon className="w-5 h-5 text-success-400" />;
    }
    if (isAvailable === false) {
      return <XIcon className="w-5 h-5 text-error-400" />;
    }
    return null;
  };

  // Determine error message
  const displayError =
    error ||
    (isAvailable === false
      ? 'This URL is already taken'
      : undefined);

  return (
    <div className={cn('space-y-2', className)}>
      {/* Input */}
      <div className="relative">
        <AppInput
          label="Workspace URL"
          value={value}
          onChange={handleChange}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          leftIcon={<LinkIcon className="w-5 h-5" />}
          rightIcon={getStatusIcon()}
          error={displayError}
          helperText={
            !displayError && value
              ? `Your gallery will be at RawDrive.io/${value}`
              : undefined
          }
          autoComplete="off"
          spellCheck={false}
        />
      </div>

      {/* Suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="pt-1">
          <p className="text-xs text-white/50 mb-2">Suggestions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.slice(0, 4).map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => handleSuggestionClick(suggestion)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm',
                  'bg-white/5 border border-white/10',
                  'hover:bg-white/10 hover:border-white/20',
                  'transition-all duration-200',
                  'text-white/70 hover:text-white'
                )}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading suggestions */}
      {isLoadingSuggestions && !suggestions.length && (
        <div className="flex items-center gap-2 text-sm text-white/50">
          <LoaderIcon className="w-4 h-4" />
          <span>Generating suggestions...</span>
        </div>
      )}
    </div>
  );
}

export default SlugInput;
