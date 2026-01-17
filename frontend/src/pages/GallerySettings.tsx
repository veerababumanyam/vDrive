/**
 * Gallery Settings Page
 * Configure watermark settings for galleries
 * Enhanced with mobile-first futuristic design and safe areas
 *
 * Subtask-4-3: Create GallerySettings page with watermark configuration
 * Subtask-4-5: Add batch watermark apply button with progress tracking
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { WatermarkEditor } from '../components/gallery/WatermarkEditor';
import { WatermarkPreview } from '../components/gallery/WatermarkPreview';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { AppLogo } from '../components/ui/AppLogo';
import { cn } from '../lib/utils';
import { useBreakpoint, useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';
import {
  applyWatermark,
  getWatermarkStatus,
  getWatermarkConfig,
  updateWatermarkConfig
} from '../services/watermark-api';
import { useWorkspaceContext } from '../contexts/WorkspaceContext';
import type { ApiError, WatermarkConfig } from '../types/watermark';


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



function SettingsIcon({ className }: { className?: string }) {
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
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
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

function GridPattern() {
  return (
    <div className="absolute inset-0 opacity-[0.015] dark:opacity-[0.02]">
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(to right, currentColor 1px, transparent 1px),
            linear-gradient(to bottom, currentColor 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />
    </div>
  );
}

// ============================================
// Main Component
// ============================================

export function GallerySettingsPage() {

  const { galleryId } = useParams<{ galleryId: string }>();
  const { currentWorkspace } = useWorkspaceContext();
  const workspaceId = currentWorkspace?.id;
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const { top, bottom } = useSafeArea();
  const triggerHaptic = useHaptic();

  // Watermark configuration state
  // Watermark configuration state
  const [watermarkConfig, setWatermarkConfig] = useState<WatermarkConfig>({
    enabled: true,
    watermark_type: 'text',
    text_config: {
      text: '© Your Brand',
      font_size: 24,
      font_family: 'Arial',
      color: '#FFFFFF',
      opacity: 0.7,
      position: 'bottom_right',
      rotation: 0,
    },
  });

  // const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Batch watermark apply state
  const [isApplying, setIsApplying] = useState(false);
  const [batchJobId, setBatchJobId] = useState<string | null>(null);
  const [batchProgress, setBatchProgress] = useState(0);
  const [batchError, setBatchError] = useState<string | null>(null);
  const [batchSuccess, setBatchSuccess] = useState(false);
  const progressPollInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch initial configuration
  useEffect(() => {
    if (!galleryId || !workspaceId) return;

    const fetchConfig = async () => {
      try {
        const response = await getWatermarkConfig(galleryId, workspaceId);
        if (response) {
          // Map response to config
          setWatermarkConfig({
            enabled: response.enabled,
            watermark_type: response.watermark_type || 'text',
            text_config: response.text_config,
            image_config: response.image_config
          });
        }
      } catch (error) {
        // Only log error if strictly necessary, or handle UI feedback
        // console.error('Failed to fetch watermark config:', error);
      } finally {
        // setIsLoading(false);
      }
    };

    fetchConfig();
  }, [galleryId, workspaceId]);

  // Handle back navigation
  const handleBack = useCallback(() => {
    triggerHaptic.light();
    navigate('/dashboard');
  }, [navigate, triggerHaptic]);

  // Handle watermark config change
  const handleConfigChange = useCallback((config: WatermarkConfig) => {
    setWatermarkConfig(config);
    setSaveSuccess(false);
  }, []);

  // Handle save
  const handleSave = useCallback(
    async (config: WatermarkConfig) => {
      if (!galleryId || !workspaceId) return;

      try {
        setIsSaving(true);
        triggerHaptic.medium();

        await updateWatermarkConfig(galleryId, workspaceId, config);

        setSaveSuccess(true);
        triggerHaptic.success();

        // Clear success message after 3 seconds
        setTimeout(() => setSaveSuccess(false), 3000);
      } catch (error) {
        triggerHaptic.error();
        // TODO: Show error message via toast
      } finally {
        setIsSaving(false);
      }
    },
    [galleryId, workspaceId, triggerHaptic]
  );

  // Handle batch watermark apply
  const handleBatchApply = useCallback(async () => {
    if (!galleryId || !workspaceId) return;

    try {
      setIsApplying(true);
      setBatchError(null);
      setBatchSuccess(false);
      setBatchProgress(0);
      triggerHaptic.medium();

      // Call API to start batch apply
      const response = await applyWatermark(galleryId, workspaceId);
      setBatchJobId(response.job_id);
      triggerHaptic.light();
    } catch (error) {
      const apiError = error as ApiError;
      setBatchError(apiError.message || 'Failed to start batch watermark application');
      setIsApplying(false);
      triggerHaptic.error();
    }
  }, [galleryId, workspaceId, triggerHaptic]);

  // Poll for batch progress
  useEffect(() => {
    if (!batchJobId || !isApplying || !galleryId || !workspaceId) {
      return;
    }

    const pollProgress = async () => {
      try {
        const status = await getWatermarkStatus(galleryId, workspaceId, batchJobId);

        // Update progress
        setBatchProgress(status.progress_percentage || 0);

        // Check if completed
        if (status.status === 'completed') {
          setBatchSuccess(true);
          setIsApplying(false);
          setBatchJobId(null);
          triggerHaptic('success');

          // Clear success message after 5 seconds
          setTimeout(() => setBatchSuccess(false), 5000);

          // Stop polling
          if (progressPollInterval.current) {
            clearInterval(progressPollInterval.current);
            progressPollInterval.current = null;
          }
        } else if (status.status === 'failed') {
          setBatchError(status.message || 'Batch watermark application failed');
          setIsApplying(false);
          setBatchJobId(null);
          triggerHaptic.error();

          // Stop polling
          if (progressPollInterval.current) {
            clearInterval(progressPollInterval.current);
            progressPollInterval.current = null;
          }
        }
      } catch (error) {
        const apiError = error as ApiError;
        setBatchError(apiError.message || 'Failed to check batch progress');
        setIsApplying(false);
        setBatchJobId(null);
        triggerHaptic.error();

        // Stop polling
        if (progressPollInterval.current) {
          clearInterval(progressPollInterval.current);
          progressPollInterval.current = null;
        }
      }
    };

    // Start polling every 2 seconds
    progressPollInterval.current = setInterval(pollProgress, 2000);

    // Initial poll
    pollProgress();

    // Cleanup on unmount
    return () => {
      if (progressPollInterval.current) {
        clearInterval(progressPollInterval.current);
        progressPollInterval.current = null;
      }
    };
  }, [batchJobId, isApplying, galleryId, workspaceId, triggerHaptic]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-white to-primary-50/30 dark:from-neutral-950 dark:via-neutral-900 dark:to-primary-950/20 relative overflow-hidden">
      {/* Futuristic Background Effects */}
      <GridPattern />
      <ParticleEffect />
      <MorphingBlob className="top-0 left-0 w-96 h-96 bg-primary-300 dark:bg-primary-500" />
      <MorphingBlob className="bottom-0 right-0 w-96 h-96 bg-purple-300 dark:bg-purple-500" />

      {/* Header */}
      <header
        className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 dark:bg-neutral-900/70 border-b border-neutral-200/50 dark:border-white/10"
        style={{ paddingTop: `${top}px` }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20">
            {/* Left: Back Button / Menu */}
            <div className="flex items-center gap-3 sm:gap-4">
              <button
                onClick={handleBack}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200',
                  'text-neutral-700 dark:text-white/80',
                  'hover:bg-neutral-100 dark:hover:bg-white/5',
                  'active:scale-95'
                )}
              >
                <ArrowLeftIcon className="w-5 h-5" />
                {!isMobile && <span className="font-medium">Back</span>}
              </button>
            </div>

            {/* Center: Logo & Title */}
            <div className="flex items-center gap-3">
              <AppLogo size="sm" className="hidden sm:block" />
              <div className="flex items-center gap-2">
                <SettingsIcon className="w-5 h-5 text-primary-500" />
                <h1 className="text-lg sm:text-xl font-bold text-neutral-900 dark:text-white">
                  Gallery Settings
                </h1>
              </div>
            </div>

            {/* Right: Theme Toggle */}
            <div className="flex items-center gap-2 sm:gap-3">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12"
        style={{ paddingBottom: `${bottom + 24}px` }}
      >
        {/* Success Message - Save */}
        {saveSuccess && (
          <div className="mb-6 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-500/30 animate-fade-up">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <svg
                  className="w-5 h-5 text-green-600 dark:text-green-400"
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
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  Watermark settings saved successfully!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Success Message - Batch Apply */}
        {batchSuccess && (
          <div className="mb-6 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-500/30 animate-fade-up">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <svg
                  className="w-5 h-5 text-green-600 dark:text-green-400"
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
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  Watermarks applied to all photos successfully!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message - Batch Apply */}
        {batchError && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-500/30 animate-fade-up">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <svg
                  className="w-5 h-5 text-red-600 dark:text-red-400"
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
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">{batchError}</p>
              </div>
              <button
                onClick={() => setBatchError(null)}
                className="flex-shrink-0 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
              >
                <svg
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" x2="6" y1="6" y2="18" />
                  <line x1="6" x2="18" y1="6" y2="18" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Batch Apply Section */}
        <div className="mb-6 animate-fade-up">
          <div className="p-6 rounded-xl bg-white/50 dark:bg-white/5 border border-neutral-200 dark:border-white/10 backdrop-blur-sm">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex-1">
                <h3 className="text-base font-semibold text-neutral-900 dark:text-white mb-1">
                  Apply Watermark to All Photos
                </h3>
                <p className="text-sm text-neutral-600 dark:text-white/70">
                  Apply the current watermark configuration to all photos in this gallery. This may
                  take a few moments for large galleries.
                </p>
              </div>
              <button
                onClick={handleBatchApply}
                disabled={isApplying}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all duration-200',
                  'bg-primary-500 text-white',
                  'hover:bg-primary-600 active:scale-95',
                  'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-primary-500',
                  'shadow-lg shadow-primary-500/20'
                )}
              >
                {isApplying ? (
                  <>
                    <svg
                      className="w-4 h-4 animate-spin"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                    <span>Applying...</span>
                  </>
                ) : (
                  <>
                    <svg
                      className="w-4 h-4"
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
                    <span>Apply to All</span>
                  </>
                )}
              </button>
            </div>

            {/* Progress Bar */}
            {isApplying && (
              <div className="mt-4 animate-fade-in">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-neutral-600 dark:text-white/70">
                    Processing photos...
                  </span>
                  <span className="text-xs font-semibold text-primary-600 dark:text-primary-400">
                    {Math.round(batchProgress)}%
                  </span>
                </div>
                <div className="h-2 bg-neutral-200 dark:bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-500 ease-out"
                    style={{ width: `${batchProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Left: Watermark Editor */}
          <div className="animate-fade-up" style={{ animationDelay: '100ms' }}>
            <WatermarkEditor
              value={watermarkConfig}
              onChange={handleConfigChange}
              onSave={handleSave}
              showSaveButton={true}
              isSaving={isSaving}
            />
          </div>

          {/* Right: Preview */}
          <div className="animate-fade-up" style={{ animationDelay: '200ms' }}>
            <WatermarkPreview config={watermarkConfig} />
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-8 animate-fade-up" style={{ animationDelay: '300ms' }}>
          <div className="p-6 rounded-xl bg-white/50 dark:bg-white/5 border border-neutral-200 dark:border-white/10 backdrop-blur-sm">
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-3">
              💡 Watermark Tips
            </h3>
            <ul className="space-y-2 text-sm text-neutral-600 dark:text-white/70">
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>
                  Use a semi-transparent watermark (50-70% opacity) to protect your images while
                  keeping them visible
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>
                  For logo watermarks, upload a PNG image with a transparent background for best
                  results
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>
                  The tiled option creates a repeating pattern across the entire image, making it
                  harder to remove
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">•</span>
                <span>
                  Watermarks are only applied to preview images - purchased high-resolution
                  downloads remain unwatermarked
                </span>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}

export default GallerySettingsPage;
