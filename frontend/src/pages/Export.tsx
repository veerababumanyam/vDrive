/**
 * Export Page
 * Bulk export and migration tools for photos and galleries
 * Enhanced with mobile-first futuristic design, safe areas, and haptic feedback
 */

import { useNavigate } from 'react-router-dom';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { AppLogo } from '../components/ui/AppLogo';
import { cn } from '../lib/utils';
import { useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';
import { useCallback, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ExportWizard } from '../components/export/ExportWizard';
import { ExportList } from '../components/export/ExportList';
import type { ExportType } from '../services/export-api';

// ============================================
// Icons
// ============================================

function DownloadIcon({ className }: { className?: string }) {
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
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" x2="12" y1="15" y2="3" />
    </svg>
  );
}

function UploadIcon({ className }: { className?: string }) {
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
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" x2="12" y1="3" y2="15" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
    </svg>
  );
}

function PackageIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m7.5 4.27 9 5.15" />
      <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
      <path d="m3.3 7 8.7 5 8.7-5" />
      <path d="M12 22V12" />
    </svg>
  );
}

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
// Export Options
// ============================================

const exportOptions = [
  {
    title: 'Export All Photos',
    description: 'Download all photos from this workspace with original quality',
    icon: DownloadIcon,
    gradient: 'from-blue-500 to-cyan-500',
    lightBg: 'bg-blue-50',
    darkBg: 'bg-blue-500/20',
    iconColor: 'text-blue-600 dark:text-blue-400',
    action: 'export-all',
  },
  {
    title: 'Export Gallery',
    description: 'Download a specific gallery with all metadata preserved',
    icon: FolderIcon,
    gradient: 'from-violet-500 to-purple-500',
    lightBg: 'bg-violet-50',
    darkBg: 'bg-violet-500/20',
    iconColor: 'text-violet-600 dark:text-violet-400',
    action: 'export-gallery',
  },
  {
    title: 'Create Archive',
    description: 'Package all workspace data for backup or migration',
    icon: PackageIcon,
    gradient: 'from-emerald-500 to-teal-500',
    lightBg: 'bg-emerald-50',
    darkBg: 'bg-emerald-500/20',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    action: 'create-archive',
  },
  {
    title: 'Import from Platform',
    description: 'Migrate galleries from Pixieset, Pic-Time, or other platforms',
    icon: UploadIcon,
    gradient: 'from-amber-500 to-orange-500',
    lightBg: 'bg-amber-50',
    darkBg: 'bg-amber-500/20',
    iconColor: 'text-amber-600 dark:text-amber-400',
    action: 'import',
  },
];

// ============================================
// Main Export Page Component
// ============================================

export function ExportPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const safeArea = useSafeArea();
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [exportType, setExportType] = useState<ExportType>('workspace');
  const [showExportList, setShowExportList] = useState(true);

  const handleLogout = useCallback(async () => {
    haptic.medium();
    await logout();
    navigate('/signin');
  }, [logout, navigate, haptic]);

  const handleBackToDashboard = useCallback(() => {
    haptic.light();
    navigate('/dashboard');
  }, [navigate, haptic]);

  const handleExportAction = useCallback((action: string) => {
    haptic.medium();

    if (action === 'import') {
      navigate('/migration');
      return;
    }

    setSelectedOption(action);

    // Map actions to export types
    if (action === 'export-all' || action === 'create-archive') {
      setExportType('workspace');
      setShowWizard(true);
    } else if (action === 'export-gallery') {
      setExportType('gallery');
      setShowWizard(true);
    }
  }, [haptic, navigate]);

  const workspaceName = user?.workspace_name || 'Your Workspace';

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 dark:from-neutral-900 dark:to-neutral-800 relative overflow-hidden">
      {/* Animated Background Elements */}
      <ParticleEffect />
      <MorphingBlob
        className="w-[500px] h-[500px] bg-gradient-to-br from-blue-500/30 to-cyan-500/30 -top-48 -left-24"
        style={{ animationDelay: '0s' }}
      />
      <MorphingBlob
        className="w-[600px] h-[600px] bg-gradient-to-br from-violet-500/20 to-purple-500/20 top-1/3 -right-48"
        style={{ animationDelay: '2s' }}
      />
      <MorphingBlob
        className="w-[400px] h-[400px] bg-gradient-to-br from-emerald-500/25 to-teal-500/25 bottom-0 left-1/4"
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
          onClick={handleBackToDashboard}
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
          <span>Back to Dashboard</span>
        </button>

        {/* Page Header */}
        <div className="mb-8 sm:mb-12">
          <h1
            className={cn(
              "text-2xl sm:text-3xl lg:text-4xl font-bold text-neutral-900 dark:text-white mb-3",
              !prefersReducedMotion && "animate-fade-in-up stagger-2"
            )}
          >
            Export & Migration
          </h1>
          <p
            className={cn(
              "text-base sm:text-lg text-neutral-600 dark:text-white/60 max-w-3xl",
              !prefersReducedMotion && "animate-fade-in-up stagger-3"
            )}
          >
            Download your photos, create backups, or migrate from other platforms. Your data is always yours.
          </p>
        </div>

        {/* Conditional Content: Wizard or Export Options */}
        {showWizard ? (
          <>
            {/* Back Button to Export Options */}
            <button
              onClick={() => {
                haptic.light();
                setShowWizard(false);
              }}
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
              <span>Back to Export Options</span>
            </button>

            {/* Export Wizard */}
            <div className={cn(!prefersReducedMotion && "animate-fade-in-up")}>
              <ExportWizard
                initialType={exportType}
                onComplete={() => {
                  setShowWizard(false);
                  setShowExportList(true);
                }}
              />
            </div>
          </>
        ) : (
          <>
            {/* Export Options Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              {exportOptions.map((option, index) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.action}
                    onClick={() => handleExportAction(option.action)}
                    className={cn(
                      'group relative overflow-hidden rounded-xl sm:rounded-2xl p-6 sm:p-8',
                      'text-left transition-all duration-300 glass-hover-lift',
                      'bg-white/90 dark:bg-white/[0.20]',
                      'backdrop-blur-xl',
                      'border border-neutral-200 dark:border-white/[0.30]',
                      'shadow-[0_2px_4px_rgba(0,0,0,0.1),0_8px_16px_rgba(0,0,0,0.2)]',
                      'hover:shadow-[0_4px_8px_rgba(0,0,0,0.15),0_16px_32px_rgba(0,0,0,0.25)]',
                      selectedOption === option.action && 'ring-2 ring-primary-500',
                      !prefersReducedMotion && `animate-fade-in-up stagger-${index + 4}`
                    )}
                  >
                    {/* Icon Container */}
                    <div className="flex items-start gap-4 mb-4">
                      <div
                        className={cn(
                          'p-3 rounded-xl',
                          'transition-transform duration-300 group-hover:scale-110',
                          option.lightBg,
                          `dark:${option.darkBg}`
                        )}
                      >
                        <Icon className={cn('w-6 h-6', option.iconColor)} />
                      </div>
                    </div>

                    {/* Content */}
                    <div>
                      <h3 className="text-lg sm:text-xl font-semibold text-neutral-900 dark:text-white mb-2">
                        {option.title}
                      </h3>
                      <p className="text-sm sm:text-base text-neutral-600 dark:text-white/60">
                        {option.description}
                      </p>
                    </div>

                    {/* Gradient Accent Bar */}
                    <div
                      className={cn(
                        'absolute bottom-0 left-0 right-0 h-1',
                        'bg-gradient-to-r',
                        option.gradient,
                        'opacity-0 group-hover:opacity-100',
                        'transition-opacity duration-300'
                      )}
                    />
                  </button>
                );
              })}
            </div>

            {/* Export List - Show recent/active exports */}
            {showExportList && (
              <div className="mt-12">
                <h2 className="text-xl font-bold text-neutral-900 dark:text-white mb-6">
                  Recent Exports
                </h2>
                <ExportList />
              </div>
            )}
          </>
        )}

        {/* Info Section */}
        <div
          className={cn(
            'mt-8 sm:mt-12 p-6 sm:p-8 rounded-xl sm:rounded-2xl',
            'bg-white/90 dark:bg-white/10',
            'backdrop-blur-xl',
            'border border-neutral-200 dark:border-white/20',
            !prefersReducedMotion && 'animate-fade-in-up stagger-8'
          )}
        >
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
            Your Data, Your Control
          </h2>
          <div className="space-y-3 text-neutral-600 dark:text-white/70">
            <p className="text-sm sm:text-base">
              <strong>Data Freedom:</strong> Unlike other platforms, vDrive gives you complete control over your data.
              Export at any time, in any format, with no restrictions.
            </p>
            <p className="text-sm sm:text-base">
              <strong>Original Quality:</strong> All exports include your original, uncompressed files with full EXIF
              metadata, tags, and organization preserved.
            </p>
            <p className="text-sm sm:text-base">
              <strong>No Lock-In:</strong> We believe your work should never be held hostage. Export everything
              whenever you need, whether for backup or migration.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ExportPage;
