/**
 * EmailRegistrationModal Component
 *
 * Lead capture modal shown before gallery access when email registration
 * is required. Collects visitor information for CRM workflows.
 *
 * Features:
 * - Email validation (RFC 5322)
 * - Optional name, phone, address fields
 * - Privacy policy link
 * - Loading state
 * - Error handling
 */

import {
  forwardRef,
  useState,
  useCallback,
  type FormEvent,
  type HTMLAttributes,
} from 'react';
import { cn } from '../../lib/utils';
import { AppButton } from '../ui/AppButton';
import { AppInput } from '../ui/AppInput';
import { AppCard } from '../ui/AppCard';
import type { VisitorCreate } from '../../types/gallery';

export interface EmailRegistrationModalProps
  extends Omit<HTMLAttributes<HTMLDivElement>, 'onSubmit'> {
  /** Gallery title to display */
  galleryTitle: string;
  /** Photographer/workspace name */
  photographerName?: string;
  /** Is modal open */
  isOpen: boolean;
  /** Loading state */
  isLoading?: boolean;
  /** Error message */
  error?: string | null;
  /** Submit handler */
  onSubmit: (data: VisitorCreate) => void;
  /** Skip handler (if registration is optional) */
  onSkip?: () => void;
  /** Show additional fields (name, phone, address) */
  showAdditionalFields?: boolean;
}

/**
 * Close icon
 */
function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

/**
 * Gallery icon
 */
function GalleryIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M22 16V4c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2zm-11-4l2.03 2.71L16 11l4 5H8l3-4zM2 6v14c0 1.1.9 2 2 2h14v-2H4V6H2z" />
    </svg>
  );
}

/**
 * Validate email format (basic RFC 5322)
 */
function isValidEmail(email: string): boolean {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
}

export const EmailRegistrationModal = forwardRef<
  HTMLDivElement,
  EmailRegistrationModalProps
>(
  (
    {
      galleryTitle,
      photographerName,
      isOpen,
      isLoading = false,
      error,
      onSubmit,
      onSkip,
      showAdditionalFields = false,
      className,
      ...props
    },
    ref
  ) => {
    const [email, setEmail] = useState('');
    const [name, setName] = useState('');
    const [phone, setPhone] = useState('');
    const [emailError, setEmailError] = useState<string | null>(null);

    // Validate and submit
    const handleSubmit = useCallback(
      (e: FormEvent) => {
        e.preventDefault();

        // Validate email
        if (!email.trim()) {
          setEmailError('Email is required');
          return;
        }

        if (!isValidEmail(email)) {
          setEmailError('Please enter a valid email address');
          return;
        }

        setEmailError(null);

        onSubmit({
          email: email.trim(),
          name: name.trim() || undefined,
          phone: phone.trim() || undefined,
        });
      },
      [email, name, phone, onSubmit]
    );

    // Clear email error on change
    const handleEmailChange = useCallback((value: string) => {
      setEmail(value);
      if (value && emailError) {
        setEmailError(null);
      }
    }, [emailError]);

    if (!isOpen) return null;

    return (
      <div
        ref={ref}
        className={cn(
          'fixed inset-0 z-50',
          'flex items-center justify-center',
          'bg-black/60 backdrop-blur-sm',
          'p-4',
          'animate-fade-in',
          className
        )}
        {...props}
      >
        <AppCard
          variant="premiumGlass"
          padding="lg"
          className={cn(
            'w-full max-w-md',
            'animate-scale-up',
            'relative'
          )}
        >
          {/* Skip button (if optional) */}
          {onSkip && (
            <button
              onClick={onSkip}
              className={cn(
                'absolute top-4 right-4',
                'p-2 rounded-full',
                'text-neutral-500 hover:text-neutral-700',
                'dark:text-neutral-400 dark:hover:text-neutral-200',
                'transition-colors'
              )}
              aria-label="Skip registration"
            >
              <CloseIcon className="w-5 h-5" />
            </button>
          )}

          {/* Header */}
          <div className="text-center mb-6">
            <div
              className={cn(
                'w-16 h-16 mx-auto mb-4 rounded-full',
                'bg-primary-100 dark:bg-primary-500/20',
                'flex items-center justify-center'
              )}
            >
              <GalleryIcon className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>

            <h2 className="text-xl sm:text-2xl font-semibold text-neutral-800 dark:text-white mb-2">
              Welcome to Your Gallery
            </h2>

            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              Enter your email to access <strong>{galleryTitle}</strong>
              {photographerName && (
                <>
                  <br />
                  <span className="text-neutral-500 dark:text-neutral-400">
                    by {photographerName}
                  </span>
                </>
              )}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email (required) */}
            <AppInput
              type="email"
              label="Email Address"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => handleEmailChange(e.target.value)}
              error={emailError || undefined}
              required
              autoFocus
              autoComplete="email"
            />

            {/* Additional fields */}
            {showAdditionalFields && (
              <>
                <AppInput
                  type="text"
                  label="Your Name"
                  placeholder="Optional"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                />

                <AppInput
                  type="tel"
                  label="Phone Number"
                  placeholder="Optional"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  autoComplete="tel"
                />
              </>
            )}

            {/* Error message */}
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-sm">
                {error}
              </div>
            )}

            {/* Submit button */}
            <AppButton
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isLoading}
              glowOnHover
            >
              Access Gallery
            </AppButton>

            {/* Privacy note */}
            <p className="text-xs text-center text-neutral-500 dark:text-neutral-400">
              Your information is kept private and never shared.
              <br />
              <a
                href="/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-primary-500"
              >
                Privacy Policy
              </a>
            </p>
          </form>
        </AppCard>
      </div>
    );
  }
);

EmailRegistrationModal.displayName = 'EmailRegistrationModal';

export default EmailRegistrationModal;
