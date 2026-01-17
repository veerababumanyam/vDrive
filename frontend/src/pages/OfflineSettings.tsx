/**
 * Offline Settings Page
 * Manage offline gallery settings: encryption, storage, cache management
 * Enhanced with mobile-first futuristic design, safe areas, and haptic feedback
 *
 * T4-3: Add offline settings page with encryption toggle
 */

import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppCard } from '../components/ui/AppCard';
import { AppButton } from '../components/ui/AppButton';
import { AppInput } from '../components/ui/AppInput';
import { AppLogo } from '../components/ui/AppLogo';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { useOfflineGallery } from '../hooks/useOfflineGallery';
import { useAuth } from '../contexts/AuthContext';
import {
  setEncryptionPassword,
  clearEncryptionKey,
  hasEncryptionKey,
  validatePasswordStrength,
  isCryptoAvailable,
} from '../utils/encryption';
import { cn } from '../lib/utils';
import { useBreakpoint, useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';

// ============================================
// Icons
// ============================================

function LockIcon({ className }: { className?: string }) {
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
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function UnlockIcon({ className }: { className?: string }) {
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
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 9.9-1" />
    </svg>
  );
}

function DatabaseIcon({ className }: { className?: string }) {
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
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5v14a9 3 0 0 0 18 0V5" />
      <path d="M3 12a9 3 0 0 0 18 0" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
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
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    </svg>
  );
}

function ChevronLeftIcon({ className }: { className?: string }) {
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
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

function AlertCircleIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
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
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <path d="m9 11 3 3L22 4" />
    </svg>
  );
}

// ============================================
// Futuristic Background Components
// ============================================

function MorphingBlob({ className }: { className?: string }) {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        'absolute rounded-full blur-3xl opacity-30',
        !prefersReducedMotion && 'animate-morph',
        className
      )}
    />
  );
}

function ParticleEffect() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) return null;

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(10)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-primary-400/30 dark:bg-primary-300/25"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `float ${8 + Math.random() * 4}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 5}s`,
          }}
        />
      ))}
    </div>
  );
}

// ============================================
// Main Component
// ============================================

export function OfflineSettings() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isMobile } = useBreakpoint();
  const haptic = useHaptic();
  const { top, bottom } = useSafeArea();

  // Offline gallery hook
  const {
    storageStats,
    isLoadingStats,
    refreshStorageStats,
    clearAllOfflineData,
    error: offlineError,
    clearError,
  } = useOfflineGallery({
    workspaceId: user?.workspace_id,
  });

  // Encryption state
  const [encryptionEnabled, setEncryptionEnabled] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Clear cache confirmation
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Success/error messages
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Check if encryption is already enabled
  useEffect(() => {
    setEncryptionEnabled(hasEncryptionKey());
  }, []);

  // Handle encryption toggle
  const handleEncryptionToggle = useCallback(async () => {
    haptic('light');
    clearError();
    setPasswordError('');
    setSuccessMessage('');
    setErrorMessage('');

    if (encryptionEnabled) {
      // Disable encryption
      clearEncryptionKey();
      setEncryptionEnabled(false);
      setPassword('');
      setConfirmPassword('');
      setSuccessMessage('Encryption disabled. Existing encrypted data will be inaccessible.');
      setTimeout(() => setSuccessMessage(''), 5000);
    } else {
      // Enable encryption - show password input
      setShowPassword(true);
    }
  }, [encryptionEnabled, haptic, clearError]);

  // Handle password submission
  const handleSetPassword = useCallback(async () => {
    haptic('light');
    setPasswordError('');
    setErrorMessage('');

    // Validate password
    if (!password) {
      setPasswordError('Password is required');
      return;
    }

    const validation = validatePasswordStrength(password);
    if (!validation.valid) {
      setPasswordError(validation.message);
      return;
    }

    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    setIsProcessing(true);

    try {
      await setEncryptionPassword(password);
      setEncryptionEnabled(true);
      setPassword('');
      setConfirmPassword('');
      setShowPassword(false);
      setSuccessMessage('Encryption enabled successfully! Future downloads will be encrypted.');
      haptic('success');
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to enable encryption';
      setErrorMessage(message);
      haptic('error');
    } finally {
      setIsProcessing(false);
    }
  }, [password, confirmPassword, haptic]);

  // Handle clear all cache
  const handleClearCache = useCallback(async () => {
    haptic('medium');
    setShowClearConfirm(false);
    setIsProcessing(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const success = await clearAllOfflineData();
      if (success) {
        await refreshStorageStats();
        setSuccessMessage('All offline data cleared successfully');
        haptic('success');
        setTimeout(() => setSuccessMessage(''), 5000);
      } else {
        setErrorMessage('Failed to clear offline data');
        haptic('error');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to clear offline data';
      setErrorMessage(message);
      haptic('error');
    } finally {
      setIsProcessing(false);
    }
  }, [clearAllOfflineData, refreshStorageStats, haptic]);

  // Format storage size
  const formatSize = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  // Check if crypto is available
  const cryptoAvailable = isCryptoAvailable();

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Futuristic Background */}
      <div className="fixed inset-0 -z-10">
        {/* Base gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-secondary-50 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950" />

        {/* Morphing blobs */}
        <MorphingBlob className="w-96 h-96 bg-primary-400/30 dark:bg-primary-500/20 -top-20 -left-20" />
        <MorphingBlob
          className="w-80 h-80 bg-secondary-400/30 dark:bg-secondary-500/20 top-1/3 right-0"
          style={{ animationDelay: '2s' }}
        />
        <MorphingBlob
          className="w-72 h-72 bg-accent-400/30 dark:bg-accent-500/20 bottom-0 left-1/4"
          style={{ animationDelay: '4s' }}
        />

        {/* Particle effect */}
        <ParticleEffect />

        {/* Grid overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.05)_1px,transparent_1px)] bg-[size:64px_64px] dark:bg-[linear-gradient(rgba(139,92,246,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.05)_1px,transparent_1px)]" />
      </div>

      {/* Main Content */}
      <div
        className="relative"
        style={{
          paddingTop: `max(1rem, ${top}px)`,
          paddingBottom: `max(1rem, ${bottom}px)`,
        }}
      >
        {/* Header */}
        <header className="px-4 sm:px-6 py-4 flex items-center justify-between backdrop-blur-md bg-white/50 dark:bg-black/30 border-b border-neutral-200/50 dark:border-white/10">
          <div className="flex items-center gap-4">
            <AppButton
              variant="ghost"
              size={isMobile ? 'sm' : 'md'}
              onClick={() => {
                haptic('light');
                navigate(-1);
              }}
              className="gap-2"
            >
              <ChevronLeftIcon className="w-5 h-5" />
              <span className="hidden sm:inline">Back</span>
            </AppButton>
            <AppLogo size={isMobile ? 'sm' : 'md'} />
          </div>
          <ThemeToggle />
        </header>

        {/* Page Content */}
        <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-4xl">
          {/* Page Title */}
          <div className="mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 dark:from-primary-400 dark:to-secondary-400 bg-clip-text text-transparent">
              Offline Settings
            </h1>
            <p className="mt-2 text-neutral-600 dark:text-white/70">
              Manage offline gallery storage, encryption, and cache
            </p>
          </div>

          {/* Success/Error Messages */}
          {successMessage && (
            <AppCard className="mb-6 border-success-500/50 bg-success-50/50 dark:bg-success-900/20">
              <div className="flex items-start gap-3">
                <CheckCircleIcon className="w-5 h-5 text-success-600 dark:text-success-400 shrink-0 mt-0.5" />
                <p className="text-success-700 dark:text-success-300 text-sm">{successMessage}</p>
              </div>
            </AppCard>
          )}

          {(errorMessage || offlineError) && (
            <AppCard className="mb-6 border-error-500/50 bg-error-50/50 dark:bg-error-900/20">
              <div className="flex items-start gap-3">
                <AlertCircleIcon className="w-5 h-5 text-error-600 dark:text-error-400 shrink-0 mt-0.5" />
                <p className="text-error-700 dark:text-error-300 text-sm">
                  {errorMessage || offlineError}
                </p>
              </div>
            </AppCard>
          )}

          {/* Storage Statistics */}
          <AppCard className="mb-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-primary-100 dark:bg-primary-900/30">
                <DatabaseIcon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-1">
                  Storage Usage
                </h2>
                <p className="text-sm text-neutral-600 dark:text-white/70 mb-4">
                  {storageStats
                    ? `${storageStats.gallery_count} galleries cached (${formatSize(storageStats.total_gallery_size_mb)})`
                    : 'Loading...'}
                </p>

                {storageStats && (
                  <>
                    {/* Progress bar */}
                    <div className="mb-2">
                      <div className="h-2 bg-neutral-200 dark:bg-white/10 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-primary-500 to-secondary-500 transition-all duration-500"
                          style={{ width: `${Math.min(storageStats.percentage_used, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Storage details */}
                    <div className="flex justify-between text-xs text-neutral-600 dark:text-white/60">
                      <span>{formatSize(storageStats.usage_mb)} used</span>
                      <span>{formatSize(storageStats.available_mb)} available</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </AppCard>

          {/* Encryption Settings */}
          <AppCard className="mb-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="p-3 rounded-xl bg-secondary-100 dark:bg-secondary-900/30">
                {encryptionEnabled ? (
                  <LockIcon className="w-6 h-6 text-secondary-600 dark:text-secondary-400" />
                ) : (
                  <UnlockIcon className="w-6 h-6 text-secondary-600 dark:text-secondary-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-1">
                  Offline Encryption
                </h2>
                <p className="text-sm text-neutral-600 dark:text-white/70 mb-4">
                  {encryptionEnabled
                    ? 'Your offline data is encrypted with AES-256-GCM'
                    : 'Encrypt cached galleries with a password or PIN'}
                </p>

                {!cryptoAvailable && (
                  <div className="mb-4 p-3 rounded-lg bg-warning-50 dark:bg-warning-900/20 border border-warning-500/50">
                    <p className="text-sm text-warning-700 dark:text-warning-300">
                      Web Crypto API is not available in this environment. Encryption is disabled.
                    </p>
                  </div>
                )}

                {/* Password inputs (shown when enabling encryption) */}
                {showPassword && !encryptionEnabled && cryptoAvailable && (
                  <div className="space-y-4 mb-4">
                    <AppInput
                      type="password"
                      label="Password or PIN"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      error={passwordError}
                      helperText="Use at least 8 characters or a 6-digit PIN"
                      disabled={isProcessing}
                    />
                    <AppInput
                      type="password"
                      label="Confirm Password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={isProcessing}
                    />
                    <div className="flex gap-2">
                      <AppButton
                        variant="primary"
                        onClick={handleSetPassword}
                        loading={isProcessing}
                        disabled={isProcessing}
                      >
                        Enable Encryption
                      </AppButton>
                      <AppButton
                        variant="ghost"
                        onClick={() => {
                          setShowPassword(false);
                          setPassword('');
                          setConfirmPassword('');
                          setPasswordError('');
                        }}
                        disabled={isProcessing}
                      >
                        Cancel
                      </AppButton>
                    </div>
                  </div>
                )}

                {/* Toggle button */}
                {!showPassword && cryptoAvailable && (
                  <AppButton
                    variant={encryptionEnabled ? 'error' : 'primary'}
                    onClick={handleEncryptionToggle}
                    disabled={isProcessing}
                  >
                    {encryptionEnabled ? 'Disable Encryption' : 'Enable Encryption'}
                  </AppButton>
                )}
              </div>
            </div>
          </AppCard>

          {/* Clear Cache */}
          <AppCard>
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-error-100 dark:bg-error-900/30">
                <TrashIcon className="w-6 h-6 text-error-600 dark:text-error-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-1">
                  Clear All Offline Data
                </h2>
                <p className="text-sm text-neutral-600 dark:text-white/70 mb-4">
                  Remove all cached galleries and photos from local storage
                </p>

                {!showClearConfirm ? (
                  <AppButton
                    variant="error"
                    onClick={() => {
                      haptic('medium');
                      setShowClearConfirm(true);
                    }}
                    disabled={isProcessing || isLoadingStats || !storageStats?.gallery_count}
                  >
                    Clear All Cache
                  </AppButton>
                ) : (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-warning-50 dark:bg-warning-900/20 border border-warning-500/50">
                      <p className="text-sm text-warning-700 dark:text-warning-300">
                        <strong>Warning:</strong> This will permanently delete all offline galleries
                        and photos from this device. This action cannot be undone.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <AppButton
                        variant="error"
                        onClick={handleClearCache}
                        loading={isProcessing}
                        disabled={isProcessing}
                      >
                        Yes, Clear All Data
                      </AppButton>
                      <AppButton
                        variant="ghost"
                        onClick={() => {
                          haptic('light');
                          setShowClearConfirm(false);
                        }}
                        disabled={isProcessing}
                      >
                        Cancel
                      </AppButton>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </AppCard>

          {/* Info footer */}
          <div className="mt-8 text-center">
            <p className="text-xs text-neutral-500 dark:text-white/50">
              Offline data is stored locally on your device using IndexedDB.
              <br />
              Data is automatically synced when you're back online.
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}

export default OfflineSettings;
