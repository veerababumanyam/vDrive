/**
 * ActivationChecklist Component
 * Gamified checklist for first-mile user activation
 *
 * T124: Create ActivationChecklist component with progress tracking
 * T126: Add dismiss and re-access functionality
 * T127: Add completion celebration animation
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { onboardingApi } from '../../services/onboarding-api';
import { AppCard } from '../ui/AppCard';
import { AppButton } from '../ui/AppButton';
import type { ActivationChecklistItem } from '../../types/onboarding';
import { cn } from '../../lib/utils';

// ============================================
// Icons
// ============================================

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

function CircleIcon({ className }: { className?: string }) {
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

function SparklesIcon({ className }: { className?: string }) {
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
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
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
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}

function PartyPopperIcon({ className }: { className?: string }) {
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
      <path d="M5.8 11.3 2 22l10.7-3.79" />
      <path d="M4 3h.01" />
      <path d="M22 8h.01" />
      <path d="M15 2h.01" />
      <path d="M22 20h.01" />
      <path d="m22 2-2.24.75a2.9 2.9 0 0 0-1.96 3.12c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10" />
      <path d="m22 13-.82-.33c-.86-.34-1.82.2-1.98 1.11-.11.7-.72 1.22-1.43 1.22H17" />
      <path d="m11 2 .33.82c.34.86-.2 1.82-1.11 1.98-.7.11-1.22.72-1.22 1.43V7" />
      <path d="M11 13c1.93 1.93 2.83 4.17 2 5-.83.83-3.07-.07-5-2-1.93-1.93-2.83-4.17-2-5 .83-.83 3.07.07 5 2Z" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface ActivationChecklistProps {
  /** Whether to show as a compact widget */
  compact?: boolean;
  /** Callback when an item is clicked */
  onItemClick?: (item: ActivationChecklistItem) => void;
  /** Additional class names */
  className?: string;
}

// ============================================
// Storage Keys
// ============================================

const DISMISSED_KEY = 'vdrive-checklist-dismissed';
const CELEBRATION_KEY = 'vdrive-checklist-celebrated';

// ============================================
// Component
// ============================================

/**
 * Activation checklist with gamified progress tracking
 *
 * @example
 * ```tsx
 * <ActivationChecklist onItemClick={(item) => navigate(item.action_url)} />
 * ```
 */
export function ActivationChecklist({
  compact = false,
  onItemClick,
  className,
}: ActivationChecklistProps) {
  const [isDismissed, setIsDismissed] = useState(() => {
    return localStorage.getItem(DISMISSED_KEY) === 'true';
  });
  const [showCelebration, setShowCelebration] = useState(false);
  const [hasCelebrated, setHasCelebrated] = useState(() => {
    return localStorage.getItem(CELEBRATION_KEY) === 'true';
  });

  // Fetch checklist data
  const { data, isLoading } = useQuery({
    queryKey: ['activationChecklist'],
    queryFn: onboardingApi.getActivationChecklist,
    staleTime: 60000,
  });

  // Check for completion celebration (T127)
  useEffect(() => {
    if (data && data.progress_percentage === 100 && !hasCelebrated) {
      setShowCelebration(true);
      setHasCelebrated(true);
      localStorage.setItem(CELEBRATION_KEY, 'true');

      // Auto-hide celebration after 5 seconds
      const timer = setTimeout(() => {
        setShowCelebration(false);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [data, hasCelebrated]);

  // Dismiss handler (T126)
  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem(DISMISSED_KEY, 'true');
  };

  // Re-show handler (T126)
  const handleReshow = () => {
    setIsDismissed(false);
    localStorage.removeItem(DISMISSED_KEY);
  };

  // Handle item click
  const handleItemClick = (item: ActivationChecklistItem) => {
    if (!item.completed && item.action_url) {
      onItemClick?.(item);
    }
  };

  // Don't render if dismissed (show re-access button instead)
  if (isDismissed && !compact) {
    return (
      <button
        onClick={handleReshow}
        className={cn(
          'fixed bottom-6 right-6 z-40',
          'flex items-center gap-2 px-4 py-2.5 rounded-xl',
          'bg-primary-500/20 border border-primary-500/30',
          'text-primary-400 text-sm font-medium',
          'hover:bg-primary-500/30 transition-all duration-200',
          'shadow-lg shadow-primary-500/20'
        )}
      >
        <SparklesIcon className="w-4 h-4" />
        <span>Getting Started</span>
      </button>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <AppCard variant="glass" padding="md" className={cn('animate-pulse', className)}>
        <div className="h-6 bg-neutral-200 dark:bg-white/10 rounded w-1/2 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-neutral-100 dark:bg-white/5 rounded-lg" />
          ))}
        </div>
      </AppCard>
    );
  }

  if (!data || !data.items) return null;

  const { items, completed_items, total_items, progress_percentage } = data;

  // Celebration overlay (T127)
  if (showCelebration) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-950/80 backdrop-blur-sm animate-fade-in">
        <AppCard
          variant="glass"
          padding="lg"
          className="max-w-md text-center animate-fade-up"
        >
          <div className="relative">
            {/* Confetti-like animation */}
            <div className="absolute -top-8 left-1/2 -translate-x-1/2">
              <PartyPopperIcon className="w-16 h-16 text-accent-500 dark:text-accent-400 animate-float" />
            </div>

            <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mt-8 mb-2">
              Congratulations!
            </h2>
            <p className="text-neutral-600 dark:text-white/60 mb-6">
              You've completed all the getting started tasks. Your workspace is
              ready for amazing things!
            </p>

            <AppButton
              variant="accent"
              onClick={() => setShowCelebration(false)}
            >
              Let's Go!
            </AppButton>
          </div>
        </AppCard>
      </div>
    );
  }

  // All complete - don't show checklist
  if (progress_percentage === 100 && !compact) {
    return null;
  }

  return (
    <AppCard
      variant={compact ? 'default' : 'glass'}
      padding={compact ? 'sm' : 'md'}
      className={cn(
        compact ? 'w-full' : 'w-full max-w-sm',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-accent-500 dark:text-accent-400" />
          <h3 className="font-semibold text-neutral-900 dark:text-white">Getting Started</h3>
        </div>

        {!compact && (
          <button
            onClick={handleDismiss}
            className="p-1 text-neutral-400 hover:text-neutral-600 dark:text-white/40 dark:hover:text-white/70 transition-colors"
            aria-label="Dismiss checklist"
          >
            <XIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1.5">
          <span className="text-neutral-500 dark:text-white/60">Progress</span>
          <span className="text-neutral-900 dark:text-white font-medium">
            {completed_items}/{total_items}
          </span>
        </div>
        <div className="h-2 bg-neutral-200 dark:bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress_percentage}%` }}
          />
        </div>
      </div>

      {/* Checklist items */}
      <div className="space-y-2">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => handleItemClick(item)}
            disabled={item.completed}
            className={cn(
              'w-full flex items-center gap-3 p-3 rounded-lg text-left',
              'transition-all duration-200',
              item.completed
                ? 'bg-success-100 dark:bg-success-500/10 cursor-default'
                : 'bg-neutral-100 hover:bg-neutral-200 dark:bg-white/5 dark:hover:bg-white/10 cursor-pointer'
            )}
          >
            {/* Check icon */}
            <div
              className={cn(
                'shrink-0 w-5 h-5 rounded-full transition-colors',
                item.completed ? 'text-success-500 dark:text-success-400' : 'text-neutral-400 dark:text-white/30'
              )}
            >
              {item.completed ? (
                <CheckCircleIcon className="w-5 h-5" />
              ) : (
                <CircleIcon className="w-5 h-5" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <p
                className={cn(
                  'font-medium text-sm',
                  item.completed ? 'text-neutral-400 dark:text-white/50 line-through' : 'text-neutral-900 dark:text-white'
                )}
              >
                {item.title}
              </p>
              {!compact && (
                <p className="text-xs text-neutral-500 dark:text-white/40 mt-0.5 line-clamp-1">
                  {item.description}
                </p>
              )}
            </div>

            {/* Arrow for actionable items */}
            {!item.completed && item.action_url && (
              <ChevronRightIcon className="w-4 h-4 text-neutral-400 dark:text-white/30" />
            )}
          </button>
        ))}
      </div>
    </AppCard>
  );
}

export default ActivationChecklist;
