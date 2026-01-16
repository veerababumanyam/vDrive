/**
 * PinEntryModal Component
 *
 * Modal for entering PIN to unlock private photos.
 * Features rate limiting feedback and progressive delay warnings.
 *
 * Features:
 * - 4-6 digit PIN input
 * - Auto-submit on complete
 * - Rate limit feedback
 * - Lockout countdown timer
 * - Error states with animations
 */

import {
  forwardRef,
  useState,
  useEffect,
  useRef,
  useCallback,
  type HTMLAttributes,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react';
import { cn } from '../../lib/utils';
import { useHaptic } from '../../hooks';
import { AppButton } from '../ui/AppButton';
import { AppCard } from '../ui/AppCard';

export interface PinEntryModalProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onSubmit'> {
  /** Is modal open */
  isOpen: boolean;
  /** Close handler */
  onClose: () => void;
  /** PIN submit handler */
  onSubmit: (pin: string) => void;
  /** Loading state */
  isLoading?: boolean;
  /** Error message */
  error?: string | null;
  /** Remaining attempts before lockout */
  remainingAttempts?: number;
  /** Lockout timestamp (if locked) */
  lockedUntil?: Date | null;
  /** Photo title being unlocked */
  photoTitle?: string;
}

/**
 * Lock icon
 */
function LockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
    </svg>
  );
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

const PIN_LENGTH = 4;

export const PinEntryModal = forwardRef<HTMLDivElement, PinEntryModalProps>(
  (
    {
      isOpen,
      onClose,
      onSubmit,
      isLoading = false,
      error,
      remainingAttempts,
      lockedUntil,
      photoTitle,
      className,
      ...props
    },
    ref
  ) => {
    const [pin, setPin] = useState<string[]>(Array(PIN_LENGTH).fill(''));
    const [shake, setShake] = useState(false);
    const [lockoutRemaining, setLockoutRemaining] = useState<number>(() => {
      if (!lockedUntil) return 0;
      return Math.max(0, Math.ceil((lockedUntil.getTime() - Date.now()) / 1000));
    });
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
    const haptic = useHaptic();
    const prevIsOpenRef = useRef(isOpen);
    const prevErrorRef = useRef(error);

    // Update lockout remaining time via interval
    useEffect(() => {
      if (!lockedUntil) {
        // Reset lockout when lockedUntil becomes null
        // eslint-disable-next-line react-hooks/set-state-in-effect -- Synchronizing with external prop
        setLockoutRemaining(0);
        return;
      }

      const interval = setInterval(() => {
        const remaining = Math.max(
          0,
          Math.ceil((lockedUntil.getTime() - Date.now()) / 1000)
        );
        setLockoutRemaining(remaining);
      }, 1000);

      return () => clearInterval(interval);
    }, [lockedUntil]);

    // Reset PIN when modal opens (transition from closed to open)
    useEffect(() => {
      if (isOpen && !prevIsOpenRef.current) {
        // eslint-disable-next-line react-hooks/set-state-in-effect -- Synchronizing with external prop
        setPin(Array(PIN_LENGTH).fill(''));
        setShake(false);
        // Focus first input
        setTimeout(() => inputRefs.current[0]?.focus(), 100);
      }
      prevIsOpenRef.current = isOpen;
    }, [isOpen]);

    // Shake animation on new error
    useEffect(() => {
      if (error && error !== prevErrorRef.current) {
        // eslint-disable-next-line react-hooks/set-state-in-effect -- Synchronizing with external prop
        setShake(true);
        haptic.error();
        const timer = setTimeout(() => setShake(false), 500);
        prevErrorRef.current = error;
        return () => clearTimeout(timer);
      }
      prevErrorRef.current = error;
    }, [error, haptic]);

    // Handle input change
    const handleChange = useCallback(
      (index: number, e: ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;

        // Only allow digits
        if (value && !/^\d$/.test(value)) {
          return;
        }

        const newPin = [...pin];
        newPin[index] = value;
        setPin(newPin);

        // Move to next input
        if (value && index < PIN_LENGTH - 1) {
          inputRefs.current[index + 1]?.focus();
        }

        // Auto-submit when complete
        if (value && index === PIN_LENGTH - 1) {
          const fullPin = newPin.join('');
          if (fullPin.length === PIN_LENGTH) {
            haptic.light();
            onSubmit(fullPin);
          }
        }
      },
      [pin, onSubmit, haptic]
    );

    // Handle backspace
    const handleKeyDown = useCallback(
      (index: number, e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Backspace' && !pin[index] && index > 0) {
          inputRefs.current[index - 1]?.focus();
        }
      },
      [pin]
    );

    // Handle paste
    const handlePaste = useCallback(
      (e: React.ClipboardEvent) => {
        e.preventDefault();
        const pastedData = e.clipboardData.getData('text');
        const digits = pastedData.replace(/\D/g, '').slice(0, PIN_LENGTH);

        if (digits.length > 0) {
          const newPin = Array(PIN_LENGTH).fill('');
          for (let i = 0; i < digits.length; i++) {
            newPin[i] = digits[i];
          }
          setPin(newPin);

          // Focus appropriate input
          if (digits.length < PIN_LENGTH) {
            inputRefs.current[digits.length]?.focus();
          } else {
            // Auto-submit
            haptic.light();
            onSubmit(digits);
          }
        }
      },
      [onSubmit, haptic]
    );

    // Manual submit
    const handleManualSubmit = useCallback(() => {
      const fullPin = pin.join('');
      if (fullPin.length === PIN_LENGTH) {
        onSubmit(fullPin);
      }
    }, [pin, onSubmit]);

    // Format remaining time
    const formatTime = (seconds: number): string => {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const isLocked = lockoutRemaining > 0;
    const isPinComplete = pin.every((d) => d !== '');

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
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            onClose();
          }
        }}
        {...props}
      >
        <AppCard
          variant="premiumGlass"
          padding="lg"
          className={cn(
            'w-full max-w-sm',
            'animate-scale-up',
            'relative',
            shake && 'animate-shake'
          )}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className={cn(
              'absolute top-4 right-4',
              'p-2 rounded-full',
              'text-neutral-500 hover:text-neutral-700',
              'dark:text-neutral-400 dark:hover:text-neutral-200',
              'transition-colors'
            )}
            aria-label="Close"
          >
            <CloseIcon className="w-5 h-5" />
          </button>

          {/* Header */}
          <div className="text-center mb-6">
            <div
              className={cn(
                'w-14 h-14 mx-auto mb-4 rounded-full',
                'bg-amber-100 dark:bg-amber-500/20',
                'flex items-center justify-center'
              )}
            >
              <LockIcon className="w-7 h-7 text-amber-600 dark:text-amber-400" />
            </div>

            <h2 className="text-lg sm:text-xl font-semibold text-neutral-800 dark:text-white mb-1">
              Enter PIN to Unlock
            </h2>

            {photoTitle && (
              <p className="text-sm text-neutral-600 dark:text-neutral-300 truncate">
                {photoTitle}
              </p>
            )}
          </div>

          {/* Lockout message */}
          {isLocked && (
            <div
              className={cn(
                'mb-6 p-4 rounded-xl',
                'bg-red-50 dark:bg-red-500/10',
                'text-center'
              )}
            >
              <p className="text-red-700 dark:text-red-300 font-medium">
                Too many attempts
              </p>
              <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                Try again in {formatTime(lockoutRemaining)}
              </p>
            </div>
          )}

          {/* PIN inputs */}
          {!isLocked && (
            <>
              <div
                className="flex justify-center gap-3 mb-6"
                onPaste={handlePaste}
              >
                {pin.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => { inputRefs.current[index] = el; }}
                    type="text"
                    inputMode="numeric"
                    pattern="\d*"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleChange(index, e)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    disabled={isLoading || isLocked}
                    className={cn(
                      'w-14 h-16 text-center text-2xl font-bold',
                      'rounded-xl border-2',
                      'transition-all duration-200',
                      'focus:outline-none',
                      // Default state
                      'bg-neutral-50 border-neutral-200 text-neutral-800',
                      'dark:bg-white/5 dark:border-white/20 dark:text-white',
                      // Focus state
                      'focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
                      'dark:focus:border-primary-400',
                      // Filled state
                      digit && 'border-primary-300 dark:border-primary-500/50',
                      // Error state
                      error && 'border-red-400 dark:border-red-500',
                      // Disabled
                      (isLoading || isLocked) && 'opacity-50 cursor-not-allowed'
                    )}
                    aria-label={`PIN digit ${index + 1}`}
                  />
                ))}
              </div>

              {/* Error message */}
              {error && (
                <p className="text-center text-red-600 dark:text-red-400 text-sm mb-4">
                  {error}
                </p>
              )}

              {/* Remaining attempts warning */}
              {remainingAttempts !== undefined && remainingAttempts <= 3 && !error && (
                <p className="text-center text-amber-600 dark:text-amber-400 text-sm mb-4">
                  {remainingAttempts} attempt{remainingAttempts !== 1 ? 's' : ''}{' '}
                  remaining
                </p>
              )}

              {/* Submit button */}
              <AppButton
                type="button"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isLoading}
                disabled={!isPinComplete || isLoading}
                onClick={handleManualSubmit}
                glowOnHover
              >
                Unlock Photo
              </AppButton>
            </>
          )}

          {/* Contact photographer hint */}
          <p className="text-xs text-center text-neutral-500 dark:text-neutral-400 mt-4">
            Forgot your PIN? Contact your photographer.
          </p>
        </AppCard>
      </div>
    );
  }
);

PinEntryModal.displayName = 'PinEntryModal';

export default PinEntryModal;
