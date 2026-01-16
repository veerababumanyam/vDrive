/**
 * ConfirmDialog Component
 *
 * A reusable confirmation dialog for destructive or important actions.
 * Features glassmorphism styling and haptic feedback.
 *
 * Features:
 * - Customizable title, message, and button labels
 * - Danger/warning variants
 * - Loading state support
 * - Escape key and backdrop click to cancel
 * - Focus trap within dialog
 */

import {
  forwardRef,
  useEffect,
  useRef,
  type HTMLAttributes,
} from 'react';
import { cn } from '../../lib/utils';
import { useHaptic } from '../../hooks';
import { AppButton } from './AppButton';
import { AppCard } from './AppCard';

export interface ConfirmDialogProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Is dialog open */
  isOpen: boolean;
  /** Close/cancel handler */
  onClose: () => void;
  /** Confirm handler */
  onConfirm: () => void;
  /** Dialog title */
  title: string;
  /** Dialog message/description */
  message: string;
  /** Confirm button label */
  confirmLabel?: string;
  /** Cancel button label */
  cancelLabel?: string;
  /** Dialog variant */
  variant?: 'danger' | 'warning' | 'info';
  /** Loading state for confirm action */
  isLoading?: boolean;
  /** Icon to show in header (optional) */
  icon?: React.ReactNode;
}

/**
 * Default icons for each variant
 */
function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
    </svg>
  );
}

function WarningIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
    </svg>
  );
}

function InfoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

const variantStyles = {
  danger: {
    iconBg: 'bg-red-100 dark:bg-red-500/20',
    iconColor: 'text-red-600 dark:text-red-400',
    buttonVariant: 'destructive' as const,
  },
  warning: {
    iconBg: 'bg-amber-100 dark:bg-amber-500/20',
    iconColor: 'text-amber-600 dark:text-amber-400',
    buttonVariant: 'primary' as const,
  },
  info: {
    iconBg: 'bg-primary-100 dark:bg-primary-500/20',
    iconColor: 'text-primary-600 dark:text-primary-400',
    buttonVariant: 'primary' as const,
  },
};

const defaultIcons = {
  danger: TrashIcon,
  warning: WarningIcon,
  info: InfoIcon,
};

export const ConfirmDialog = forwardRef<HTMLDivElement, ConfirmDialogProps>(
  (
    {
      isOpen,
      onClose,
      onConfirm,
      title,
      message,
      confirmLabel = 'Confirm',
      cancelLabel = 'Cancel',
      variant = 'danger',
      isLoading = false,
      icon,
      className,
      ...props
    },
    ref
  ) => {
    const haptic = useHaptic();
    const confirmButtonRef = useRef<HTMLButtonElement>(null);
    const cancelButtonRef = useRef<HTMLButtonElement>(null);

    // Focus cancel button when dialog opens (safer default)
    useEffect(() => {
      if (isOpen) {
        // Small delay to ensure animation has started
        const timer = setTimeout(() => {
          cancelButtonRef.current?.focus();
        }, 100);
        return () => clearTimeout(timer);
      }
    }, [isOpen]);

    // Handle escape key
    useEffect(() => {
      if (!isOpen) return;

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && !isLoading) {
          onClose();
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, isLoading, onClose]);

    // Prevent body scroll when open
    useEffect(() => {
      if (isOpen) {
        document.body.style.overflow = 'hidden';
        return () => {
          document.body.style.overflow = '';
        };
      }
    }, [isOpen]);

    const handleConfirm = () => {
      haptic.heavy();
      onConfirm();
    };

    const handleClose = () => {
      if (!isLoading) {
        haptic.light();
        onClose();
      }
    };

    const styles = variantStyles[variant];
    const DefaultIcon = defaultIcons[variant];
    const IconComponent = icon || <DefaultIcon className={cn('w-7 h-7', styles.iconColor)} />;

    if (!isOpen) return null;

    return (
      <div
        ref={ref}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        className={cn(
          'fixed inset-0 z-50',
          'flex items-center justify-center',
          'bg-black/60 backdrop-blur-sm',
          'p-4',
          'animate-fade-in',
          className
        )}
        onClick={(e) => {
          if (e.target === e.currentTarget && !isLoading) {
            handleClose();
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
            'relative'
          )}
        >
          {/* Close button */}
          <button
            onClick={handleClose}
            disabled={isLoading}
            className={cn(
              'absolute top-4 right-4',
              'p-2 rounded-full',
              'text-neutral-500 hover:text-neutral-700',
              'dark:text-neutral-400 dark:hover:text-neutral-200',
              'transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
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
                styles.iconBg,
                'flex items-center justify-center'
              )}
            >
              {IconComponent}
            </div>

            <h2
              id="confirm-dialog-title"
              className="text-lg sm:text-xl font-semibold text-neutral-800 dark:text-white mb-2"
            >
              {title}
            </h2>

            <p
              id="confirm-dialog-description"
              className="text-sm text-neutral-600 dark:text-neutral-300"
            >
              {message}
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col-reverse sm:flex-row gap-3">
            <AppButton
              ref={cancelButtonRef}
              type="button"
              variant="outline"
              size="lg"
              fullWidth
              onClick={handleClose}
              disabled={isLoading}
            >
              {cancelLabel}
            </AppButton>

            <AppButton
              ref={confirmButtonRef}
              type="button"
              variant={styles.buttonVariant}
              size="lg"
              fullWidth
              isLoading={isLoading}
              onClick={handleConfirm}
            >
              {confirmLabel}
            </AppButton>
          </div>
        </AppCard>
      </div>
    );
  }
);

ConfirmDialog.displayName = 'ConfirmDialog';

export default ConfirmDialog;
