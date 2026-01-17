/**
 * Dashboard Page - Premium iOS-Inspired Design
 * Mobile-first, responsive, modern, elegant photography dashboard
 * WCAG 2.1 AA compliant with glassmorphism, animations, and haptic feedback
 */

import { useNavigate } from 'react-router-dom';
import { ActivationChecklist } from '../components/onboarding/ActivationChecklist';
import { AnimatedCounter } from '../components/ui/AnimatedCounter';
import type { ActivationChecklistItem } from '../types/onboarding';
import { cn } from '../lib/utils';
import { useBreakpoint, useHaptic, usePrefersReducedMotion, useSafeArea, useScrollPosition } from '../hooks/useMobile';
import { useCallback } from 'react';
import { WorkspaceLayout } from '../components/workspace/WorkspaceLayout';

// ============================================
// Photography-Specific Icons (Lucide-style SVGs)
// ============================================

function CameraIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3" />
    </svg>
  );
}


function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
    </svg>
  );
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" x2="12" y1="3" y2="15" />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14" />
      <path d="M12 5v14" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}

function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}

function TrendingUpIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </svg>
  );
}

function HeartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
    </svg>
  );
}

function ShareIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <line x1="8.59" x2="15.42" y1="13.51" y2="17.49" />
      <line x1="15.41" x2="8.59" y1="6.51" y2="10.49" />
    </svg>
  );
}

function CloudIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
    </svg>
  );
}

function ApertureIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="m14.31 8 5.74 9.94" />
      <path d="M9.69 8h11.48" />
      <path d="m7.38 12 5.74-9.94" />
      <path d="M9.69 16 3.95 6.06" />
      <path d="M14.31 16H2.83" />
      <path d="m16.62 12-5.74 9.94" />
    </svg>
  );
}

// ============================================
// Animated Background Components
// ============================================

function MorphingBlob({ className }: { className?: string }) {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        'absolute rounded-full blur-3xl opacity-20',
        !prefersReducedMotion && 'animate-morph',
        className
      )}
    />
  );
}

// Pre-generated particle data for floating effect
const DASHBOARD_PARTICLES = [...Array(20)].map((_, i) => ({
  id: i,
  left: `${Math.random() * 100}%`,
  top: `${Math.random() * 100}%`,
  size: Math.random() * 3 + 2,
  animationDuration: `${10 + Math.random() * 8}s`,
  animationDelay: `${Math.random() * 5}s`,
}));

function ParticleEffect() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) return null;

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {DASHBOARD_PARTICLES.map((particle) => (
        <div
          key={particle.id}
          className="absolute rounded-full bg-gradient-to-br from-primary-400/40 to-accent-500/30"
          style={{
            left: particle.left,
            top: particle.top,
            width: particle.size,
            height: particle.size,
            animation: `float ${particle.animationDuration} ease-in-out infinite`,
            animationDelay: particle.animationDelay,
          }}
        />
      ))}
    </div>
  );
}

// ============================================
// Statistics Data with Photography Emojis
// ============================================

const stats = [
  {
    id: 'galleries',
    label: 'Galleries',
    value: 0,
    emoji: '📁',
    description: 'Photo collections',
    gradient: 'from-blue-500 via-blue-600 to-indigo-600',
    bgLight: 'bg-blue-50',
    bgDark: 'bg-blue-500/15',
    iconColor: 'text-blue-600 dark:text-blue-400',
    trend: '+2 this week',
    trendUp: true,
  },
  {
    id: 'photos',
    label: 'Photos',
    value: 0,
    emoji: '📸',
    description: 'Total uploaded',
    gradient: 'from-violet-500 via-purple-600 to-fuchsia-600',
    bgLight: 'bg-violet-50',
    bgDark: 'bg-violet-500/15',
    iconColor: 'text-violet-600 dark:text-violet-400',
    trend: '+48 today',
    trendUp: true,
  },
  {
    id: 'clients',
    label: 'Clients',
    value: 0,
    emoji: '👥',
    description: 'Active clients',
    gradient: 'from-emerald-500 via-teal-600 to-cyan-600',
    bgLight: 'bg-emerald-50',
    bgDark: 'bg-emerald-500/15',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    trend: '+5 new',
    trendUp: true,
  },
  {
    id: 'storage',
    label: 'Storage',
    value: 0,
    emoji: '☁️',
    description: 'GB used',
    gradient: 'from-amber-500 via-orange-600 to-red-500',
    bgLight: 'bg-amber-50',
    bgDark: 'bg-amber-500/15',
    iconColor: 'text-amber-600 dark:text-amber-400',
    trend: '12% of 100GB',
    trendUp: false,
  },
];

// ============================================
// Quick Actions with Photography Focus
// ============================================

const quickActions = [
  {
    id: 'create-gallery',
    label: 'New Gallery',
    description: 'Create a stunning photo gallery',
    emoji: '🎨',
    icon: FolderIcon,
    href: '/galleries/new',
    gradient: 'from-blue-500 to-cyan-500',
    shadowColor: 'shadow-blue-500/30',
  },
  {
    id: 'upload-photos',
    label: 'Upload',
    description: 'Add photos to your library',
    emoji: '📤',
    icon: UploadIcon,
    href: '/upload',
    gradient: 'from-violet-500 to-purple-500',
    shadowColor: 'shadow-violet-500/30',
  },
  {
    id: 'invite-client',
    label: 'Invite',
    description: 'Share with clients',
    emoji: '💌',
    icon: UsersIcon,
    href: '/clients/new',
    gradient: 'from-emerald-500 to-teal-500',
    shadowColor: 'shadow-emerald-500/30',
  },
];

// ============================================
// Recent Activity Mock Data
// ============================================

const recentActivity = [
  {
    id: '1',
    type: 'upload',
    title: 'Wedding Photos Uploaded',
    description: '48 photos added to "Johnson Wedding"',
    time: '2 min ago',
    emoji: '📸',
  },
  {
    id: '2',
    type: 'share',
    title: 'Gallery Shared',
    description: 'Sarah viewed "Beach Session"',
    time: '15 min ago',
    emoji: '🔗',
  },
  {
    id: '3',
    type: 'favorite',
    title: 'Client Favorites',
    description: 'Mike selected 12 favorites',
    time: '1 hour ago',
    emoji: '❤️',
  },
];

// ============================================
// Stat Card Component
// ============================================

interface StatCardProps {
  stat: typeof stats[0];
  index: number;
  prefersReducedMotion: boolean;
  onClick?: () => void;
}

function StatCard({ stat, index, prefersReducedMotion, onClick }: StatCardProps) {
  const haptic = useHaptic();

  return (
    <button
      onClick={() => {
        haptic.light();
        onClick?.();
      }}
      className={cn(
        'group relative overflow-hidden rounded-2xl sm:rounded-3xl p-4 sm:p-5',
        'w-full text-left transition-all duration-300',
        // Glass effect
        'bg-white/90 dark:bg-white/[0.12]',
        'backdrop-blur-xl',
        // Border
        'border border-neutral-200/80 dark:border-white/20',
        // Multi-layer iOS shadows
        'shadow-[0_2px_8px_rgba(0,0,0,0.08),0_8px_24px_rgba(0,0,0,0.12)]',
        'dark:shadow-[0_4px_16px_rgba(0,0,0,0.4),0_8px_32px_rgba(0,0,0,0.3)]',
        // Hover effects
        'hover:shadow-[0_4px_12px_rgba(0,0,0,0.1),0_12px_32px_rgba(0,0,0,0.15)]',
        'dark:hover:shadow-[0_8px_24px_rgba(0,0,0,0.5),0_16px_48px_rgba(0,0,0,0.4)]',
        'hover:scale-[1.02] hover:-translate-y-1',
        'active:scale-[0.98]',
        // Focus ring
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
        'dark:focus-visible:ring-offset-warm-950',
        // Animation
        !prefersReducedMotion && 'animate-fade-in-up'
      )}
      style={{ animationDelay: prefersReducedMotion ? '0ms' : `${100 + index * 80}ms` }}
      aria-label={`${stat.label}: ${stat.value} ${stat.description}`}
    >
      {/* Gradient accent bar */}
      <div className={cn(
        'absolute top-0 left-0 right-0 h-1 bg-gradient-to-r opacity-90',
        stat.gradient
      )} />

      {/* Shimmer effect on hover */}
      <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      <div className="relative">
        {/* Emoji + Icon */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-2xl sm:text-3xl" role="img" aria-hidden="true">
            {stat.emoji}
          </span>
          <div className={cn(
            'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
            stat.trendUp
              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400'
              : 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400'
          )}>
            {stat.trendUp && <TrendingUpIcon className="w-3 h-3" />}
            <span className="hidden sm:inline">{stat.trend}</span>
          </div>
        </div>

        {/* Value with animated counter */}
        <div className="mb-1">
          <span className="text-3xl sm:text-4xl font-bold text-neutral-900 dark:text-white">
            <AnimatedCounter
              value={stat.value}
              duration={1500}
              delay={200 + index * 100}
              formatNumber={stat.id !== 'storage'}
            />
          </span>
        </div>

        {/* Label */}
        <p className="text-sm font-semibold text-neutral-700 dark:text-neutral-200">
          {stat.label}
        </p>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          {stat.description}
        </p>
      </div>
    </button>
  );
}

// ============================================
// Quick Action Button Component
// ============================================

interface QuickActionProps {
  action: typeof quickActions[0];
  index: number;
  prefersReducedMotion: boolean;
  onClick: () => void;
}

function QuickActionButton({ action, index, prefersReducedMotion, onClick }: QuickActionProps) {
  const haptic = useHaptic();
  const Icon = action.icon;

  return (
    <button
      onClick={() => {
        haptic.medium();
        onClick();
      }}
      className={cn(
        'group relative flex items-center gap-4 p-4 sm:p-5 rounded-2xl w-full text-left',
        'transition-all duration-300',
        // Glass effect
        'bg-white/80 dark:bg-white/[0.08]',
        'backdrop-blur-lg',
        // Border
        'border border-neutral-200/60 dark:border-white/15',
        // Shadows
        'shadow-sm hover:shadow-lg',
        'dark:shadow-none dark:hover:shadow-[0_8px_24px_rgba(0,0,0,0.3)]',
        // Hover
        'hover:bg-white dark:hover:bg-white/[0.12]',
        'hover:scale-[1.02] hover:-translate-y-0.5',
        // Active press effect (iOS-style)
        'active:scale-[0.98]',
        // Focus
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
        // Animation
        !prefersReducedMotion && 'animate-fade-in-up'
      )}
      style={{ animationDelay: prefersReducedMotion ? '0ms' : `${300 + index * 80}ms` }}
      aria-label={`${action.label}: ${action.description}`}
    >
      {/* Icon container with gradient */}
      <div className={cn(
        'relative flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 rounded-xl sm:rounded-2xl',
        'bg-gradient-to-br shadow-lg transition-transform duration-300',
        'group-hover:scale-110 group-hover:rotate-3',
        action.gradient,
        action.shadowColor
      )}>
        <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-white" />

        {/* Inner glow */}
        <div className="absolute inset-0 rounded-xl sm:rounded-2xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-lg" role="img" aria-hidden="true">{action.emoji}</span>
          <span className="font-semibold text-neutral-900 dark:text-white">
            {action.label}
          </span>
        </div>
        <p className="text-sm text-neutral-600 dark:text-neutral-300 truncate">
          {action.description}
        </p>
      </div>

      {/* Arrow indicator */}
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-neutral-100 dark:bg-white/10 transition-all duration-300 group-hover:bg-neutral-200 dark:group-hover:bg-white/20 group-hover:translate-x-1">
        <ArrowRightIcon className="w-4 h-4 text-neutral-500 dark:text-neutral-300" />
      </div>
    </button>
  );
}

// ============================================
// Activity Item Component
// ============================================

interface ActivityItemProps {
  activity: typeof recentActivity[0];
  isLast: boolean;
}

function ActivityItem({ activity, isLast }: ActivityItemProps) {
  return (
    <div className={cn(
      'flex items-start gap-3 py-3',
      !isLast && 'border-b border-neutral-200/60 dark:border-white/10'
    )}>
      {/* Emoji indicator */}
      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-neutral-100 dark:bg-white/10 shrink-0">
        <span className="text-lg" role="img" aria-hidden="true">{activity.emoji}</span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
          {activity.title}
        </p>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
          {activity.description}
        </p>
      </div>

      {/* Time */}
      <span className="text-xs text-neutral-400 dark:text-neutral-500 shrink-0">
        {activity.time}
      </span>
    </div>
  );
}

// ============================================
// Empty State Component
// ============================================

function EmptyState({ onCreateGallery }: { onCreateGallery: () => void }) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-2xl sm:rounded-3xl p-6 sm:p-10',
        'text-center',
        // Glass effect
        'bg-gradient-to-br from-white/95 via-white/90 to-white/85',
        'dark:from-white/[0.15] dark:via-white/[0.10] dark:to-white/[0.08]',
        'backdrop-blur-xl',
        // Border
        'border border-neutral-200/80 dark:border-white/20',
        // Shadows
        'shadow-[0_4px_16px_rgba(0,0,0,0.08),0_8px_32px_rgba(0,0,0,0.1)]',
        'dark:shadow-[0_8px_32px_rgba(0,0,0,0.4)]',
        !prefersReducedMotion && 'animate-fade-in-scale'
      )}
      style={{ animationDelay: '400ms' }}
    >
      {/* Decorative gradient orbs */}
      <div className="absolute -top-24 -right-24 w-48 h-48 bg-gradient-to-br from-blue-500/20 to-cyan-500/10 rounded-full blur-3xl" aria-hidden="true" />
      <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-gradient-to-br from-violet-500/20 to-purple-500/10 rounded-full blur-3xl" aria-hidden="true" />

      <div className="relative">
        {/* Animated camera icon */}
        <div className={cn(
          'relative w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6',
          !prefersReducedMotion && 'animate-float'
        )}>
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl opacity-20 blur-xl" />
          <div className="relative w-full h-full bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30">
            <CameraIcon className="w-10 h-10 sm:w-12 sm:h-12 text-white" />
          </div>
        </div>

        {/* Content */}
        <h3 className="text-xl sm:text-2xl font-bold text-neutral-900 dark:text-white mb-2">
          Start Your Photography Journey 📸
        </h3>
        <p className="text-sm sm:text-base text-neutral-600 dark:text-neutral-300 mb-6 max-w-md mx-auto">
          Create beautiful galleries, share with clients, and showcase your work like never before.
        </p>

        {/* CTA Button */}
        <button
          onClick={() => {
            haptic.success();
            onCreateGallery();
          }}
          className={cn(
            'inline-flex items-center gap-2.5 px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl sm:rounded-2xl',
            'font-semibold text-white',
            'bg-gradient-to-r from-blue-500 via-blue-600 to-cyan-500',
            'shadow-[0_4px_16px_rgba(59,130,246,0.4),0_8px_32px_rgba(59,130,246,0.25)]',
            'hover:shadow-[0_8px_24px_rgba(59,130,246,0.5),0_16px_48px_rgba(59,130,246,0.3)]',
            'hover:scale-[1.02] hover:-translate-y-0.5',
            'active:scale-[0.98]',
            'transition-all duration-300',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
            // Touch target
            'min-h-[44px]'
          )}
        >
          <PlusIcon className="w-5 h-5" />
          Create Your First Gallery
          <SparklesIcon className="w-5 h-5 opacity-80" />
        </button>

        {/* Feature highlights */}
        <div className="flex flex-wrap justify-center gap-4 mt-8 text-xs text-neutral-500 dark:text-neutral-400">
          <span className="flex items-center gap-1.5">
            <ApertureIcon className="w-4 h-4" />
            Pro editing
          </span>
          <span className="flex items-center gap-1.5">
            <ShareIcon className="w-4 h-4" />
            Easy sharing
          </span>
          <span className="flex items-center gap-1.5">
            <HeartIcon className="w-4 h-4" />
            Client favorites
          </span>
          <span className="flex items-center gap-1.5">
            <CloudIcon className="w-4 h-4" />
            Cloud backup
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Mobile Floating Action Button
// ============================================

function FloatingActionButton({ onClick }: { onClick: () => void }) {
  const haptic = useHaptic();
  const safeArea = useSafeArea();
  const prefersReducedMotion = usePrefersReducedMotion();
  const { y: scrollY, direction } = useScrollPosition();

  // Compute visibility directly (no state needed)
  const isVisible = !(direction === 'down' && scrollY > 100);

  return (
    <button
      onClick={() => {
        haptic.success();
        onClick();
      }}
      className={cn(
        'fixed z-50 w-14 h-14 sm:w-16 sm:h-16 rounded-full',
        'flex items-center justify-center',
        // Gradient background
        'bg-gradient-to-br from-blue-500 via-blue-600 to-cyan-500',
        // Multi-layer shadow with glow
        'shadow-[0_4px_16px_rgba(59,130,246,0.4),0_8px_32px_rgba(59,130,246,0.3)]',
        // Hover effects
        'hover:shadow-[0_8px_24px_rgba(59,130,246,0.5),0_12px_40px_rgba(59,130,246,0.35)]',
        'hover:scale-105',
        // Active press effect
        'active:scale-95',
        // Transitions
        'transition-all duration-300',
        // Visibility
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-16 pointer-events-none',
        // Focus
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2',
        // Animation
        !prefersReducedMotion && 'animate-fade-in-scale'
      )}
      style={{
        bottom: `calc(1.5rem + ${safeArea.bottom}px)`,
        right: '1rem',
        animationDelay: '600ms',
      }}
      aria-label="Create new gallery"
    >
      {/* Pulsing ring effect */}
      <div className={cn(
        'absolute inset-0 rounded-full bg-blue-400 opacity-30',
        !prefersReducedMotion && 'animate-ping'
      )} />

      {/* Icon */}
      <PlusIcon className="relative w-7 h-7 text-white" />
    </button>
  );
}

// ============================================
// Main Dashboard Component
// ============================================

export function DashboardPage() {
  const navigate = useNavigate();
  const workspaceName = localStorage.getItem('workspace_name') || 'Your Studio';
  const userName = localStorage.getItem('user_name') || 'Creative';

  // Mobile-first hooks
  const { isMobile, isTablet } = useBreakpoint();
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  // Get time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return { text: 'Good morning', emoji: '🌅' };
    if (hour < 17) return { text: 'Good afternoon', emoji: '☀️' };
    if (hour < 21) return { text: 'Good evening', emoji: '🌆' };
    return { text: 'Good night', emoji: '🌙' };
  };

  const greeting = getGreeting();

  const handleChecklistItemClick = useCallback((item: ActivationChecklistItem) => {
    haptic.light();
    if (item.action_url) {
      navigate(item.action_url);
    }
  }, [haptic, navigate]);

  const handleQuickAction = useCallback((href: string) => {
    haptic.medium();
    navigate(href);
  }, [haptic, navigate]);

  const handleCreateGallery = useCallback(() => {
    haptic.success();
    navigate('/galleries/new');
  }, [haptic, navigate]);

  return (
    <WorkspaceLayout currentPage="dashboard" pageTitle="Dashboard">
      <div className="relative overflow-hidden min-h-screen">
        {/* ===== Background Effects ===== */}

        {/* Light mode gradient mesh */}
      <div className="absolute inset-0 -z-10 dark:hidden" aria-hidden="true">
        <div className="absolute top-0 -left-1/4 w-1/2 h-1/2 bg-gradient-to-br from-blue-100/50 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute top-1/4 -right-1/4 w-1/2 h-1/2 bg-gradient-to-bl from-violet-100/40 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 left-1/3 w-1/2 h-1/2 bg-gradient-to-t from-cyan-100/30 via-transparent to-transparent rounded-full blur-3xl" />
      </div>

      {/* Dark mode aurora + blobs */}
      <div className="aurora-bg hidden dark:block opacity-50" aria-hidden="true" />
      <MorphingBlob className="w-[600px] h-[600px] bg-gradient-to-br from-primary-500/10 to-accent-500/8 -top-80 -left-80 hidden dark:block" />
      <MorphingBlob className="w-[500px] h-[500px] bg-gradient-to-tr from-violet-500/8 to-blue-500/6 -bottom-40 -right-40 hidden dark:block" />
      <ParticleEffect />

      {/* ===== Main Content ===== */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 lg:py-10">

        {/* ===== Welcome Header ===== */}
        <header className="mb-6 sm:mb-8">
          {/* Greeting badge */}
          <div
            className={cn(
              'inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-3',
              'bg-gradient-to-r from-primary-500/10 to-accent-500/10',
              'dark:from-primary-500/20 dark:to-accent-500/15',
              'border border-primary-500/20',
              !prefersReducedMotion && 'animate-fade-in-up stagger-1'
            )}
          >
            <SparklesIcon className="w-4 h-4 text-primary-500 dark:text-primary-400" />
            <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
              {greeting.emoji} {greeting.text}, {userName}
            </span>
          </div>

          {/* Workspace name */}
          <h1
            className={cn(
              'text-2xl sm:text-3xl lg:text-4xl font-bold text-neutral-900 dark:text-white mb-2',
              !prefersReducedMotion && 'animate-fade-in-up stagger-2'
            )}
          >
            {workspaceName}
          </h1>

          <p
            className={cn(
              'text-base sm:text-lg text-neutral-600 dark:text-neutral-300',
              !prefersReducedMotion && 'animate-fade-in-up stagger-3'
            )}
          >
            Let's create something beautiful today ✨
          </p>
        </header>

        {/* ===== Dashboard Grid ===== */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">

          {/* Left Column - Stats, Actions, Empty State */}
          <div className="lg:col-span-2 space-y-6">

            {/* ===== Statistics Cards ===== */}
            <section aria-labelledby="stats-heading">
              <h2 id="stats-heading" className="sr-only">Your Statistics</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                {stats.map((stat, index) => (
                  <StatCard
                    key={stat.id}
                    stat={stat}
                    index={index}
                    prefersReducedMotion={prefersReducedMotion}
                    onClick={() => haptic.light()}
                  />
                ))}
              </div>
            </section>

            {/* ===== Quick Actions ===== */}
            <section aria-labelledby="actions-heading">
              <div
                className={cn(
                  'rounded-2xl sm:rounded-3xl p-4 sm:p-6',
                  // Glass effect
                  'bg-white/90 dark:bg-white/[0.10]',
                  'backdrop-blur-xl',
                  // Border
                  'border border-neutral-200/80 dark:border-white/15',
                  // Shadows
                  'shadow-[0_2px_8px_rgba(0,0,0,0.06)]',
                  'dark:shadow-[0_4px_24px_rgba(0,0,0,0.3)]',
                  !prefersReducedMotion && 'animate-fade-in-up'
                )}
                style={{ animationDelay: '250ms' }}
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 id="actions-heading" className="text-lg sm:text-xl font-bold text-neutral-900 dark:text-white flex items-center gap-2">
                    <span>Quick Actions</span>
                    <span className="text-xl" role="img" aria-hidden="true">⚡</span>
                  </h2>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400 hidden sm:block">
                    Get started quickly
                  </span>
                </div>

                <div className="space-y-3">
                  {quickActions.map((action, index) => (
                    <QuickActionButton
                      key={action.id}
                      action={action}
                      index={index}
                      prefersReducedMotion={prefersReducedMotion}
                      onClick={() => handleQuickAction(action.href)}
                    />
                  ))}
                </div>
              </div>
            </section>

            {/* ===== Recent Activity (Desktop only) ===== */}
            <section
              aria-labelledby="activity-heading"
              className={cn(
                'hidden sm:block',
                'rounded-2xl sm:rounded-3xl p-4 sm:p-6',
                // Glass effect
                'bg-white/90 dark:bg-white/[0.08]',
                'backdrop-blur-xl',
                // Border
                'border border-neutral-200/80 dark:border-white/15',
                // Shadows
                'shadow-[0_2px_8px_rgba(0,0,0,0.06)]',
                'dark:shadow-[0_4px_24px_rgba(0,0,0,0.25)]',
                !prefersReducedMotion && 'animate-fade-in-up'
              )}
              style={{ animationDelay: '500ms' }}
            >
              <h2 id="activity-heading" className="text-lg font-bold text-neutral-900 dark:text-white mb-3 flex items-center gap-2">
                <span>Recent Activity</span>
                <span className="text-lg" role="img" aria-hidden="true">📋</span>
              </h2>

              {recentActivity.length > 0 ? (
                <div>
                  {recentActivity.map((activity, index) => (
                    <ActivityItem
                      key={activity.id}
                      activity={activity}
                      isLast={index === recentActivity.length - 1}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-neutral-500 dark:text-neutral-400 py-4 text-center">
                  No recent activity. Start by creating a gallery! 📸
                </p>
              )}
            </section>

            {/* ===== Empty State ===== */}
            <EmptyState onCreateGallery={handleCreateGallery} />
          </div>

          {/* ===== Right Column - Checklist ===== */}
          <aside
            className={cn(
              'lg:col-span-1',
              !prefersReducedMotion && (isMobile ? 'animate-fade-in-up' : 'animate-slide-in-right')
            )}
            style={{ animationDelay: prefersReducedMotion ? '0ms' : '350ms' }}
            aria-labelledby="checklist-heading"
          >
            <h2 id="checklist-heading" className="sr-only">Setup Checklist</h2>
            <ActivationChecklist onItemClick={handleChecklistItemClick} />
          </aside>
        </div>
      </main>

        {/* ===== Mobile Floating Action Button ===== */}
        {(isMobile || isTablet) && (
          <FloatingActionButton onClick={handleCreateGallery} />
        )}
      </div>
    </WorkspaceLayout>
  );
}

export default DashboardPage;
