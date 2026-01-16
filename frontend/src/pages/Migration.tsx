/**
 * Migration Page
 * Import galleries and photos from external platforms
 *
 * Subtask-5-4: Create migration wizard UI component
 */

import { useNavigate } from 'react-router-dom';
import { useCallback, useState } from 'react';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { AppLogo } from '../components/ui/AppLogo';
import { MigrationWizard } from '../components/migration/MigrationWizard';
import { cn } from '../lib/utils';
import { useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';
import { useAuth } from '../contexts/AuthContext';
import type { MigrationResponse } from '../services/migration-api';

// ============================================
// Icons
// ============================================

function ArrowLeftIcon({ className }: { className?: string }) {
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
      <path d="M19 12H5" />
      <path d="m12 19-7-7 7-7" />
    </svg>
  );
}

function MenuIcon({ className }: { className?: string }) {
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
      <line x1="4" x2="20" y1="12" y2="12" />
      <line x1="4" x2="20" y1="6" y2="6" />
      <line x1="4" x2="20" y1="18" y2="18" />
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
      <polyline points="22 4 12 14.01 9 11.01" />
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
      {[...Array(15)].map((_, i) => (
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
// Main Migration Page Component
// ============================================

export function MigrationPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const safeArea = useSafeArea();
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();
  const [migrationComplete, setMigrationComplete] = useState(false);
  const [completedMigration, setCompletedMigration] = useState<MigrationResponse | null>(null);

  const handleLogout = useCallback(async () => {
    haptic.medium();
    await logout();
    navigate('/signin');
  }, [logout, navigate, haptic]);

  const handleBackToExport = useCallback(() => {
    haptic.light();
    navigate('/export');
  }, [navigate, haptic]);

  const handleMigrationComplete = useCallback((migration: MigrationResponse) => {
    haptic.success();
    setCompletedMigration(migration);
    setMigrationComplete(true);
  }, [haptic]);

  const handleViewDashboard = useCallback(() => {
    haptic.light();
    navigate('/dashboard');
  }, [navigate, haptic]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 dark:from-neutral-900 dark:to-neutral-800 relative overflow-hidden">
      {/* Animated Background Elements */}
      <ParticleEffect />
      <MorphingBlob
        className="w-[500px] h-[500px] bg-gradient-to-br from-violet-500/30 to-purple-500/30 -top-48 -left-24"
        style={{ animationDelay: '0s' }}
      />
      <MorphingBlob
        className="w-[600px] h-[600px] bg-gradient-to-br from-blue-500/20 to-cyan-500/20 top-1/3 -right-48"
        style={{ animationDelay: '2s' }}
      />
      <MorphingBlob
        className="w-[400px] h-[400px] bg-gradient-to-br from-amber-500/25 to-orange-500/25 bottom-0 left-1/4"
        style={{ animationDelay: '4s' }}
      />

      {/* Header */}
      <header
        className="sticky top-0 z-50 glass-header border-b border-neutral-200 dark:border-white/10"
        style={{ paddingTop: `${safeArea.top}px` }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          {/* Logo */}
          <a href="/" className="flex items-center gap-2.5 group touch-target">
            <AppLogo size="sm" className="transition-transform group-hover:scale-110" />
            <span className="text-lg font-bold text-neutral-900 dark:text-white hidden sm:block">vDrive</span>
          </a>

          {/* Right side */}
          <div className="flex items-center gap-2 sm:gap-4">
            <ThemeToggle size="sm" />
            <button
              onClick={handleLogout}
              className={cn(
                "hidden sm:flex items-center gap-2 touch-target px-3 py-1.5 rounded-xl",
                "bg-neutral-100 dark:bg-white/10",
                "hover:bg-neutral-200 dark:hover:bg-white/15",
                "text-neutral-700 dark:text-white/80",
                "text-sm font-medium",
                "transition-colors"
              )}
              aria-label="Sign out"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden lg:inline">Sign Out</span>
            </button>
            <button
              className={cn(
                "lg:hidden touch-target p-2 rounded-xl",
                "bg-neutral-100 dark:bg-white/10",
                "hover:bg-neutral-200 dark:hover:bg-white/15",
                "transition-colors"
              )}
              onClick={() => haptic.light()}
              aria-label="Menu"
            >
              <MenuIcon className="w-5 h-5 text-neutral-600 dark:text-white/70" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main
        className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-10"
        style={{ paddingBottom: `calc(1.5rem + ${safeArea.bottom}px)` }}
      >
        {/* Back Button */}
        <button
          onClick={handleBackToExport}
          className={cn(
            "inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-xl",
            "bg-white/90 dark:bg-white/10",
            "hover:bg-white dark:hover:bg-white/15",
            "border border-neutral-200 dark:border-white/20",
            "text-neutral-700 dark:text-white/80",
            "text-sm font-medium",
            "transition-all duration-200",
            !prefersReducedMotion && "animate-fade-in-up"
          )}
        >
          <ArrowLeftIcon className="w-4 h-4" />
          <span>Back to Export</span>
        </button>

        {!migrationComplete ? (
          <>
            {/* Page Header */}
            <div className="mb-8 sm:mb-12 text-center">
              <h1
                className={cn(
                  "text-2xl sm:text-3xl lg:text-4xl font-bold text-neutral-900 dark:text-white mb-3",
                  !prefersReducedMotion && "animate-fade-in-up stagger-2"
                )}
              >
                Import from External Platform
              </h1>
              <p
                className={cn(
                  "text-base sm:text-lg text-neutral-600 dark:text-white/60 max-w-3xl mx-auto",
                  !prefersReducedMotion && "animate-fade-in-up stagger-3"
                )}
              >
                Migrate your galleries and photos from Pixieset, Pic-Time, ShootProof, Zenfolio, or SmugMug.
                We'll preserve your organization and metadata.
              </p>
            </div>

            {/* Migration Wizard */}
            <div className={cn(!prefersReducedMotion && "animate-fade-in-up stagger-4")}>
              <MigrationWizard onComplete={handleMigrationComplete} />
            </div>
          </>
        ) : (
          <>
            {/* Success State */}
            <div className="max-w-2xl mx-auto text-center">
              <div
                className={cn(
                  "mb-8",
                  !prefersReducedMotion && "animate-fade-in-up"
                )}
              >
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center">
                  <CheckCircleIcon className="w-10 h-10 text-green-400" />
                </div>
                <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-white mb-3">
                  Migration Started!
                </h1>
                <p className="text-base sm:text-lg text-neutral-600 dark:text-white/60">
                  Your migration is now in progress. We'll import all your galleries and photos in the background.
                  You can close this page and continue working.
                </p>
              </div>

              <div
                className={cn(
                  "p-6 rounded-2xl bg-white/90 dark:bg-white/10 backdrop-blur-xl border border-neutral-200 dark:border-white/20 mb-8",
                  !prefersReducedMotion && "animate-fade-in-up stagger-2"
                )}
              >
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">
                  What happens next?
                </h2>
                <div className="space-y-3 text-left text-sm text-neutral-600 dark:text-white/70">
                  <div className="flex gap-3">
                    <span className="text-primary-500">1.</span>
                    <p>We'll connect to your account and scan all galleries</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-primary-500">2.</span>
                    <p>Photos will be downloaded with original quality and metadata</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-primary-500">3.</span>
                    <p>Gallery structure and organization will be preserved</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-primary-500">4.</span>
                    <p>You'll receive an email when the migration is complete</p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleViewDashboard}
                className={cn(
                  "inline-flex items-center gap-2 px-6 py-3 rounded-xl",
                  "bg-primary-500 hover:bg-primary-600",
                  "text-white font-medium",
                  "transition-colors",
                  !prefersReducedMotion && "animate-fade-in-up stagger-3"
                )}
              >
                Go to Dashboard
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default MigrationPage;
