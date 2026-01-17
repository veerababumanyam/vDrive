/**
 * MagicLinkAccess Page
 *
 * Entry point for public gallery access via Magic Link.
 * Handles:
 * - Link verification
 * - Password entry (if required)
 * - Email registration (if required)
 * - Redirect to GalleryViewer on success
 */

import { useState, useEffect, useCallback, type FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { AppCard } from '../components/ui/AppCard';
import { AppButton } from '../components/ui/AppButton';
import { AppInput } from '../components/ui/AppInput';
import { EmailRegistrationModal } from '../components/gallery';
import {
  verifyMagicLink,
  registerVisitor,
} from '../services/gallery-api';
import type { MagicLinkAccessResponse, VisitorCreate } from '../types/gallery';

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
 * Lock icon for password state
 */
function LockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
    </svg>
  );
}

/**
 * Error icon
 */
function ErrorIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
    </svg>
  );
}

type AccessState =
  | 'loading'
  | 'password_required'
  | 'email_required'
  | 'success'
  | 'expired'
  | 'error';

export function MagicLinkAccessPage() {
  const { linkId } = useParams<{ linkId: string }>();
  const navigate = useNavigate();

  // State
  const [accessState, setAccessState] = useState<AccessState>('loading');
  const [accessData, setAccessData] = useState<MagicLinkAccessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Password form state
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Email registration state
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationError, setRegistrationError] = useState<string | null>(null);

  // Verify link on mount
  useEffect(() => {
    if (!linkId) {
      setAccessState('error');
      setError('Invalid link');
      return;
    }

    const verifyLink = async () => {
      try {
        const result = await verifyMagicLink({ link_id: linkId });

        if (result.success) {
          if (result.email_registration_required) {
            setAccessState('email_required');
          } else {
            setAccessState('success');
          }
          setAccessData(result);
        }
      } catch (err: unknown) {
        const apiError = err as { error?: string; message?: string };
        if (apiError.error === 'PasswordRequired') {
          setAccessState('password_required');
        } else if (apiError.error === 'LinkExpired' || apiError.error === 'LinkRevoked') {
          setAccessState('expired');
          setError(apiError.message || 'This link is no longer valid');
        } else {
          setAccessState('error');
          setError(apiError.message || 'Failed to verify link');
        }
      }
    };

    verifyLink();
  }, [linkId]);

  // Handle password submission
  const handlePasswordSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();

      if (!linkId || !password.trim()) {
        setPasswordError('Please enter the password');
        return;
      }

      setIsSubmitting(true);
      setPasswordError(null);

      try {
        const result = await verifyMagicLink({
          link_id: linkId,
          password: password.trim(),
        });

        if (result.success) {
          if (result.email_registration_required) {
            setAccessState('email_required');
          } else {
            setAccessState('success');
          }
          setAccessData(result);
        }
      } catch (err: unknown) {
        const apiError = err as { error?: string; message?: string };
        if (apiError.error === 'InvalidPassword') {
          setPasswordError('Incorrect password. Please try again.');
        } else if (apiError.error === 'TooManyAttempts') {
          setPasswordError('Too many attempts. Please try again later.');
        } else {
          setPasswordError(apiError.message || 'Failed to verify password');
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [linkId, password]
  );

  // Handle email registration
  const handleEmailRegistration = useCallback(
    async (data: VisitorCreate) => {
      if (!accessData?.gallery_id) return;

      setIsRegistering(true);
      setRegistrationError(null);

      try {
        await registerVisitor(accessData.gallery_id, data);
        setAccessState('success');
      } catch (err: unknown) {
        const apiError = err as { message?: string };
        setRegistrationError(apiError.message || 'Failed to register. Please try again.');
      } finally {
        setIsRegistering(false);
      }
    },
    [accessData?.gallery_id]
  );

  // Navigate to gallery on success
  useEffect(() => {
    if (accessState === 'success' && accessData?.gallery_id) {
      // Store session and navigate
      navigate(`/g/${accessData.gallery_id}`, { replace: true });
    }
  }, [accessState, accessData, navigate]);

  // Loading state
  if (accessState === 'loading') {
    return (
      <div
        className={cn(
          'min-h-screen flex items-center justify-center',
          'bg-neutral-50 dark:bg-neutral-900',
          'p-4'
        )}
      >
        <div className="text-center">
          <div
            className={cn(
              'w-12 h-12 mx-auto mb-4 rounded-full border-2',
              'border-primary-500/30 border-t-primary-500',
              'animate-spin'
            )}
          />
          <p className="text-neutral-600 dark:text-neutral-400">
            Loading gallery...
          </p>
        </div>
      </div>
    );
  }

  // Expired state
  if (accessState === 'expired') {
    return (
      <div
        className={cn(
          'min-h-screen flex items-center justify-center',
          'bg-neutral-50 dark:bg-neutral-900',
          'p-4'
        )}
      >
        <AppCard variant="glass" padding="lg" className="max-w-md text-center">
          <div
            className={cn(
              'w-16 h-16 mx-auto mb-4 rounded-full',
              'bg-amber-100 dark:bg-amber-500/20',
              'flex items-center justify-center'
            )}
          >
            <ErrorIcon className="w-8 h-8 text-amber-600 dark:text-amber-400" />
          </div>
          <h2 className="text-xl font-semibold text-neutral-800 dark:text-white mb-2">
            Link Expired
          </h2>
          <p className="text-neutral-600 dark:text-neutral-300 mb-4">{error}</p>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            Please contact your photographer for a new link.
          </p>
        </AppCard>
      </div>
    );
  }

  // Error state
  if (accessState === 'error') {
    return (
      <div
        className={cn(
          'min-h-screen flex items-center justify-center',
          'bg-neutral-50 dark:bg-neutral-900',
          'p-4'
        )}
      >
        <AppCard variant="glass" padding="lg" className="max-w-md text-center">
          <div
            className={cn(
              'w-16 h-16 mx-auto mb-4 rounded-full',
              'bg-red-100 dark:bg-red-500/20',
              'flex items-center justify-center'
            )}
          >
            <ErrorIcon className="w-8 h-8 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-neutral-800 dark:text-white mb-2">
            Unable to Access Gallery
          </h2>
          <p className="text-neutral-600 dark:text-neutral-300">{error}</p>
        </AppCard>
      </div>
    );
  }

  // Password required state
  if (accessState === 'password_required') {
    return (
      <div
        className={cn(
          'min-h-screen flex items-center justify-center',
          'bg-neutral-50 dark:bg-neutral-900',
          'p-4'
        )}
      >
        <AppCard variant="premiumGlass" padding="lg" className="w-full max-w-md">
          <div className="text-center mb-6">
            <div
              className={cn(
                'w-16 h-16 mx-auto mb-4 rounded-full',
                'bg-primary-100 dark:bg-primary-500/20',
                'flex items-center justify-center'
              )}
            >
              <LockIcon className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h2 className="text-xl sm:text-2xl font-semibold text-neutral-800 dark:text-white mb-2">
              Password Protected
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              Enter the password to view this gallery
            </p>
          </div>

          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <AppInput
              type="password"
              label="Gallery Password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={passwordError || undefined}
              autoFocus
            />

            <AppButton
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isSubmitting}
              glowOnHover
            >
              Access Gallery
            </AppButton>
          </form>
        </AppCard>
      </div>
    );
  }

  // Email registration required
  if (accessState === 'email_required') {
    return (
      <div
        className={cn(
          'min-h-screen flex items-center justify-center',
          'bg-neutral-50 dark:bg-neutral-900',
          'p-4'
        )}
      >
        <EmailRegistrationModal
          isOpen={true}
          galleryTitle={accessData?.gallery_title || 'Gallery'}
          isLoading={isRegistering}
          error={registrationError}
          onSubmit={handleEmailRegistration}
          showAdditionalFields={true}
        />
      </div>
    );
  }

  // Success - will redirect
  return (
    <div
      className={cn(
        'min-h-screen flex items-center justify-center',
        'bg-neutral-50 dark:bg-neutral-900',
        'p-4'
      )}
    >
      <div className="text-center">
        <div
          className={cn(
            'w-12 h-12 mx-auto mb-4 rounded-full',
            'bg-emerald-100 dark:bg-emerald-500/20',
            'flex items-center justify-center'
          )}
        >
          <GalleryIcon className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
        </div>
        <p className="text-neutral-600 dark:text-neutral-400">
          Opening gallery...
        </p>
      </div>
    </div>
  );
}

export default MagicLinkAccessPage;
