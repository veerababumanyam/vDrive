/**
 * PasswordStrengthMeter Component
 * Real-time password strength indicator with feedback
 *
 * T050: Create PasswordStrengthMeter component with real-time feedback
 */

import { useMemo } from 'react';
import { cn } from '../../lib/utils';

// ============================================
// Types
// ============================================

export interface PasswordStrength {
  score: number; // 0-4
  label: 'Very Weak' | 'Weak' | 'Fair' | 'Strong' | 'Very Strong';
  color: string;
  feedback: string[];
}

export interface PasswordStrengthMeterProps {
  /** The password to analyze */
  password: string;
  /** Additional class names */
  className?: string;
  /** Show feedback text (default: true) */
  showFeedback?: boolean;
  /** Show strength label (default: true) */
  showLabel?: boolean;
  /** Compact mode - less vertical space */
  compact?: boolean;
}

// ============================================
// Strength Calculation
// ============================================

const MIN_PASSWORD_LENGTH = 8;

function calculateStrength(password: string): PasswordStrength {
  const feedback: string[] = [];
  let score = 0;

  if (password.length === 0) {
    return {
      score: 0,
      label: 'Very Weak',
      color: 'bg-neutral-600',
      feedback: [],
    };
  }

  // Length check
  if (password.length >= MIN_PASSWORD_LENGTH) {
    score += 1;
  } else {
    feedback.push(`Use ${MIN_PASSWORD_LENGTH}+ characters`);
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
  if (/[!@#$%^&*(),.?":{}|<>_\-+=[\]\\;'`~]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add special character');
  }

  // Length bonus for longer passwords
  if (password.length >= 12) {
    score += 0.5;
  }

  // Penalty for common patterns
  const commonPatterns = [
    /^123/,
    /password/i,
    /qwerty/i,
    /abc123/i,
    /111111/,
    /^(.)\1+$/, // Repeated characters
  ];

  for (const pattern of commonPatterns) {
    if (pattern.test(password)) {
      score = Math.max(0, score - 1);
      feedback.unshift('Avoid common patterns');
      break;
    }
  }

  // Round score to 0-4
  const finalScore = Math.min(4, Math.max(0, Math.round(score)));

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
    feedback: feedback.slice(0, 3), // Show max 3 feedback items
  };
}

// ============================================
// Component
// ============================================

/**
 * Password strength meter with visual indicator and feedback
 *
 * @example
 * ```tsx
 * <PasswordStrengthMeter password={password} />
 * ```
 */
export function PasswordStrengthMeter({
  password,
  className,
  showFeedback = true,
  showLabel = true,
  compact = false,
}: PasswordStrengthMeterProps) {
  const strength = useMemo(() => calculateStrength(password), [password]);

  // Don't render anything if no password
  if (!password) {
    return null;
  }

  return (
    <div className={cn('space-y-2', compact && 'space-y-1', className)}>
      {/* Strength bars */}
      <div className="flex gap-1.5">
        {[0, 1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className={cn(
              'h-1 flex-1 rounded-full transition-all duration-300',
              index <= strength.score ? strength.color : 'bg-white/10'
            )}
            aria-hidden="true"
          />
        ))}
      </div>

      {/* Label and feedback */}
      <div
        className={cn(
          'flex items-start justify-between gap-4',
          compact && 'text-xs'
        )}
      >
        {/* Strength label */}
        {showLabel && (
          <span
            className={cn(
              'text-sm font-medium transition-colors duration-300',
              strength.score === 0 && 'text-neutral-400',
              strength.score === 1 && 'text-error-400',
              strength.score === 2 && 'text-warning-400',
              strength.score === 3 && 'text-success-400',
              strength.score === 4 && 'text-primary-400'
            )}
            role="status"
            aria-live="polite"
          >
            {strength.label}
          </span>
        )}

        {/* Feedback */}
        {showFeedback && strength.feedback.length > 0 && (
          <div className="flex flex-wrap gap-x-2 gap-y-1 justify-end">
            {strength.feedback.map((item, index) => (
              <span
                key={index}
                className="text-xs text-white/50"
              >
                {item}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default PasswordStrengthMeter;
