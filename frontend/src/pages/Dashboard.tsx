/**
 * Dashboard Page
 * Main authenticated dashboard with activation checklist
 * Enhanced with mobile-first futuristic design, safe areas, and haptic feedback
 *
 * T125: Integrate ActivationChecklist into Dashboard page
 */

import { useNavigate } from 'react-router-dom';
import { ActivationChecklist } from '../components/onboarding/ActivationChecklist';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { AnimatedCounter } from '../components/ui/AnimatedCounter';
import { AppLogo } from '../components/ui/AppLogo';
import type { ActivationChecklistItem } from '../types/onboarding';
import { cn } from '../lib/utils';
import { useBreakpoint, useHaptic, usePrefersReducedMotion, useSafeArea } from '../hooks/useMobile';
import { useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

// ============================================
// Icons
// ============================================

function CameraIcon({ className }: { className?: string }) {
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
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3" />
    </svg>
  );
}

function ImageIcon({ className }: { className?: string }) {
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
      <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
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
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
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

function PlusIcon({ className }: { className?: string }) {
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
      <path d="M5 12h14" />
      <path d="M12 5v14" />
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

function ArrowRightIcon({ className }: { className?: string }) {
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
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
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
// Quick Stats - with unique gradient colors
// ============================================

const quickStats = [
  {
    label: 'Galleries',
    value: '0',
    icon: FolderIcon,
    gradient: 'from-blue-500 to-cyan-500',
    lightBg: 'bg-blue-50',
    darkBg: 'bg-blue-500/20',
    iconColor: 'text-blue-600 dark:text-blue-400',
    glowColor: 'shadow-blue-500/20',
  },
  {
    label: 'Photos',
    value: '0',
    icon: ImageIcon,
    gradient: 'from-violet-500 to-purple-500',
    lightBg: 'bg-violet-50',
    darkBg: 'bg-violet-500/20',
    iconColor: 'text-violet-600 dark:text-violet-400',
    glowColor: 'shadow-violet-500/20',
  },
  {
    label: 'Clients',
    value: '0',
    icon: UsersIcon,
    gradient: 'from-emerald-500 to-teal-500',
    lightBg: 'bg-emerald-50',
    darkBg: 'bg-emerald-500/20',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    glowColor: 'shadow-emerald-500/20',
  },
];

// ============================================
// Quick Actions - with unique visual styles
// ============================================

const quickActions = [
  {
    label: 'Create Gallery',
    description: 'Start a new photo gallery',
    icon: FolderIcon,
    href: '/galleries/new',
    gradient: 'from-blue-500 to-cyan-500',
    hoverGradient: 'group-hover:from-blue-600 group-hover:to-cyan-600',
    shadow: 'shadow-blue-500/25 group-hover:shadow-blue-500/40',
    borderAccent: 'border-l-blue-500',
  },
  {
    label: 'Upload Photos',
    description: 'Add photos to your library',
    icon: ImageIcon,
    href: '/upload',
    gradient: 'from-violet-500 to-purple-500',
    hoverGradient: 'group-hover:from-violet-600 group-hover:to-purple-600',
    shadow: 'shadow-violet-500/25 group-hover:shadow-violet-500/40',
    borderAccent: 'border-l-violet-500',
  },
  {
    label: 'Invite Client',
    description: 'Share galleries with clients',
    icon: UsersIcon,
    href: '/clients/new',
    gradient: 'from-emerald-500 to-teal-500',
    hoverGradient: 'group-hover:from-emerald-600 group-hover:to-teal-600',
    shadow: 'shadow-emerald-500/25 group-hover:shadow-emerald-500/40',
    borderAccent: 'border-l-emerald-500',
  },
];

// ============================================
// Page Component
// ============================================

export function DashboardPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const workspaceName = localStorage.getItem('workspace_name') || 'Your Studio';

  // Mobile-first hooks
  const { isMobile, isTablet } = useBreakpoint();
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();
  const safeArea = useSafeArea();

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

  const handleLogout = useCallback(async () => {
    haptic.medium();
    try {
      await logout();
      navigate('/signin');
    } catch (error) {
      console.error('Logout failed:', error);
      // Still navigate to signin even if API call fails
      navigate('/signin');
    }
  }, [haptic, logout, navigate]);

  return (
    <div className="min-h-screen-dynamic bg-neutral-50 dark:bg-warm-950 transition-colors duration-300 relative overflow-hidden">
      {/* Gradient Mesh Background - Light Mode (REDUCED intensity for better card contrast) */}
      <div className="absolute inset-0 -z-10 dark:hidden">
        <div className="absolute top-0 -left-1/4 w-1/2 h-1/2 bg-gradient-to-br from-blue-100/40 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute top-1/4 -right-1/4 w-1/2 h-1/2 bg-gradient-to-bl from-violet-100/30 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 left-1/3 w-1/2 h-1/2 bg-gradient-to-t from-cyan-100/25 via-transparent to-transparent rounded-full blur-3xl" />
      </div>

      {/* Aurora Background - Dark Mode with Morphing Blobs (REDUCED opacity for better card visibility) */}
      <div className="aurora-bg hidden dark:block opacity-40" />
      <MorphingBlob className="w-[600px] h-[600px] bg-gradient-to-br from-primary-500/6 to-accent-500/6 -top-80 -left-80 hidden dark:block" />
      <MorphingBlob className="w-96 h-96 bg-accent-500/6 bottom-20 right-10 hidden dark:block" />
      <ParticleEffect />

      {/* Header - with entrance animation and safe area */}
      <header
        className={cn(
          "sticky top-0 z-40 transition-colors",
          "bg-white/70 dark:bg-warm-950/80 backdrop-blur-xl",
          "border-b border-neutral-200/50 dark:border-white/10",
          !prefersReducedMotion && "animate-fade-in-down"
        )}
        style={{ paddingTop: safeArea.top }}
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
            {/* T065: Logout button */}
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
            {/* Mobile menu button */}
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
        {/* Welcome Header - Enhanced with staggered entrance */}
        <div className="mb-6 sm:mb-10">
          <div
            className={cn(
              "inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-3 sm:mb-4",
              "bg-gradient-to-r from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20",
              "border border-blue-500/20",
              !prefersReducedMotion && "animate-fade-in-up stagger-1"
            )}
          >
            <SparklesIcon className="w-4 h-4 text-blue-500 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Welcome back</span>
          </div>
          <h1
            className={cn(
              "text-2xl sm:text-3xl lg:text-4xl font-bold text-neutral-900 dark:text-white mb-2 sm:mb-3",
              !prefersReducedMotion && "animate-fade-in-up stagger-2"
            )}
          >
            {workspaceName}
          </h1>
          <p
            className={cn(
              "text-base sm:text-lg text-neutral-600 dark:text-white/60",
              !prefersReducedMotion && "animate-fade-in-up stagger-3"
            )}
          >
            Let's get your photography business set up for success.
          </p>
        </div>

        {/* Dashboard Grid - Mobile-first layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          {/* Left Column - Stats & Actions */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6 lg:space-y-8">
            {/* Quick Stats - Enhanced with iOS-style glass, shadows, and animated counters */}
            <div className="grid grid-cols-3 gap-2 sm:gap-4">
              {quickStats.map((stat, index) => (
                <div
                  key={stat.label}
                  className={cn(
                    'group relative overflow-hidden rounded-xl sm:rounded-2xl p-3 sm:p-5',
                    'transition-all duration-300 glass-hover-lift',
                    // Enhanced glass backgrounds with higher opacity (20% dark, 90% light)
                    'bg-white/90 dark:bg-white/[0.20]',
                    'backdrop-blur-xl',
                    // Enhanced borders
                    'border border-neutral-200 dark:border-white/[0.30]',
                    // iOS-style multi-layer shadows
                    'shadow-[0_2px_4px_rgba(0,0,0,0.1),0_8px_16px_rgba(0,0,0,0.2),0_16px_32px_rgba(0,0,0,0.15)]',
                    'dark:shadow-[0_2px_4px_rgba(0,0,0,0.3),0_8px_20px_rgba(0,0,0,0.4),0_16px_40px_rgba(0,0,0,0.3)]',
                    // Inner highlight glow
                    'shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]',
                    // Hover state
                    'hover:shadow-[0_4px_8px_rgba(0,0,0,0.12),0_12px_24px_rgba(0,0,0,0.24),0_20px_40px_rgba(0,0,0,0.18)]',
                    'dark:hover:shadow-[0_4px_8px_rgba(0,0,0,0.35),0_12px_24px_rgba(0,0,0,0.45),0_20px_40px_rgba(0,0,0,0.35)]',
                    'dark:hover:bg-white/[0.25]',
                    // Spring scale animation
                    !prefersReducedMotion && 'animate-spring-scale-in'
                  )}
                  style={{ animationDelay: prefersReducedMotion ? '0ms' : `${100 + index * 100}ms` }}
                >
                  {/* Gradient accent line with subtle animation */}
                  <div className={cn(
                    'absolute top-0 left-0 right-0 h-1 bg-gradient-to-r',
                    stat.gradient,
                    'opacity-80 group-hover:opacity-100 transition-opacity'
                  )} />

                  <div className="flex flex-col sm:flex-row items-center sm:items-start gap-2 sm:gap-4">
                    {/* Icon with enhanced background and inner glow */}
                    <div className={cn(
                      'relative w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl',
                      'flex items-center justify-center',
                      'transition-all duration-300 group-hover:scale-110',
                      stat.lightBg,
                      `dark:${stat.darkBg}`,
                      // Inner glow effect
                      'shadow-[inset_0_1px_0_rgba(255,255,255,0.2)]'
                    )}>
                      <stat.icon className={cn('w-5 h-5 sm:w-6 sm:h-6', stat.iconColor)} />
                    </div>

                    <div className="text-center sm:text-left">
                      {/* Animated counter with spring physics */}
                      <p className="text-xl sm:text-3xl font-bold text-neutral-900 dark:text-white">
                        <AnimatedCounter
                          value={parseInt(stat.value)}
                          duration={1500}
                          delay={150 + index * 100}
                          formatNumber={false}
                        />
                      </p>
                      <p className="text-xs sm:text-sm font-medium text-neutral-600 dark:text-neutral-300">
                        {stat.label}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Quick Actions - Enhanced with iOS-style glass and press effects */}
            <div
              className={cn(
                'rounded-xl sm:rounded-2xl p-4 sm:p-6',
                'transition-all duration-300',
                // Enhanced glass with higher opacity
                'bg-white/90 dark:bg-white/[0.20]',
                'backdrop-blur-xl',
                // Enhanced borders
                'border border-neutral-200 dark:border-white/[0.30]',
                // iOS-style shadows
                'shadow-[0_2px_4px_rgba(0,0,0,0.1),0_8px_16px_rgba(0,0,0,0.2),0_16px_32px_rgba(0,0,0,0.15)]',
                'dark:shadow-[0_2px_4px_rgba(0,0,0,0.3),0_8px_20px_rgba(0,0,0,0.4),0_16px_40px_rgba(0,0,0,0.3)]',
                'shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]',
                !prefersReducedMotion && 'animate-fade-in-up'
              )}
              style={{ animationDelay: prefersReducedMotion ? '0ms' : '400ms' }}
            >
              <div className="flex items-center justify-between mb-4 sm:mb-5">
                <h2 className="text-lg sm:text-xl font-bold text-neutral-900 dark:text-white">Quick Actions</h2>
                <span className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-300 hidden sm:block">Get started quickly</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                {quickActions.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => handleQuickAction(action.href)}
                    className={cn(
                      'group relative flex flex-row sm:flex-col items-center sm:items-start p-4 sm:p-5 rounded-xl text-left',
                      // Enhanced glass background
                      'bg-white/60 dark:bg-white/[0.08]',
                      'backdrop-blur-md',
                      // Enhanced borders with left accent
                      'border-l-4 border border-neutral-200 dark:border-white/[0.20]',
                      action.borderAccent,
                      // Hover states
                      'hover:bg-white/80 dark:hover:bg-white/[0.12]',
                      'hover:shadow-[0_4px_12px_rgba(0,0,0,0.15)]',
                      'dark:hover:shadow-[0_4px_12px_rgba(0,0,0,0.4)]',
                      // iOS-style press effect (scale down)
                      'active:scale-[0.97]',
                      'transition-all duration-200',
                      action.shadow,
                      'touch-target min-h-touch'
                    )}
                  >
                    {/* Icon with gradient background and inner glow */}
                    <div className={cn(
                      'w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-br',
                      'flex items-center justify-center mr-4 sm:mr-0 sm:mb-4',
                      'shadow-md transition-all duration-300',
                      'group-hover:scale-110 group-hover:shadow-lg',
                      'shadow-[inset_0_1px_0_rgba(255,255,255,0.3)]',
                      action.gradient,
                      action.hoverGradient,
                      action.shadow
                    )}>
                      <action.icon className="w-5 h-5 text-white" />
                    </div>

                    <div className="flex-1">
                      <p className="font-semibold text-neutral-900 dark:text-white mb-0.5 sm:mb-1">
                        {action.label}
                      </p>
                      <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-300 hidden sm:block">
                        {action.description}
                      </p>
                    </div>

                    {/* Arrow indicator with animation */}
                    <div className="sm:absolute sm:top-5 sm:right-4 opacity-60 sm:opacity-0 group-hover:opacity-100 transition-all duration-200 group-hover:translate-x-1">
                      <ArrowRightIcon className="w-5 h-5 text-neutral-400 dark:text-neutral-400" />
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Empty State - Enhanced with iOS-style glass and shadows */}
            <div
              className={cn(
                'relative overflow-hidden rounded-xl sm:rounded-2xl p-6 sm:p-8',
                'transition-all duration-300',
                // Enhanced glass backgrounds
                'bg-gradient-to-br from-white/95 to-white/85',
                'dark:from-white/[0.20] dark:to-white/[0.15]',
                'backdrop-blur-xl',
                // Enhanced borders
                'border border-neutral-200 dark:border-white/[0.30]',
                // iOS-style multi-layer shadows
                'shadow-[0_2px_4px_rgba(0,0,0,0.1),0_8px_16px_rgba(0,0,0,0.2),0_16px_32px_rgba(0,0,0,0.15)]',
                'dark:shadow-[0_2px_4px_rgba(0,0,0,0.3),0_8px_20px_rgba(0,0,0,0.4),0_16px_40px_rgba(0,0,0,0.3)]',
                'shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]',
                !prefersReducedMotion && 'animate-spring-scale-in'
              )}
              style={{ animationDelay: prefersReducedMotion ? '0ms' : '500ms' }}
            >
              {/* Decorative gradient orbs */}
              <div className="absolute -top-20 -right-20 w-40 h-40 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full blur-3xl" />
              <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-gradient-to-br from-violet-500/20 to-purple-500/20 rounded-full blur-3xl" />

              <div className="relative text-center py-4 sm:py-8">
                {/* Animated icon container */}
                <div className="relative w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 sm:mb-6">
                  <div className={cn(
                    "absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl opacity-20",
                    !prefersReducedMotion && "animate-pulse"
                  )} />
                  <div className="absolute inset-1 bg-white dark:bg-warm-950 rounded-xl" />
                  <div className="relative w-full h-full flex items-center justify-center">
                    <ImageIcon className="w-8 h-8 sm:w-10 sm:h-10 text-blue-500 dark:text-blue-400" />
                  </div>
                </div>

                <h3 className="text-xl sm:text-2xl font-bold text-neutral-900 dark:text-white mb-2 sm:mb-3">
                  Create your first gallery
                </h3>
                <p className="text-sm sm:text-lg text-neutral-700 dark:text-neutral-200 mb-6 sm:mb-8 max-w-md mx-auto">
                  Start showcasing your photography to clients with beautiful, customizable galleries.
                </p>

                <button
                  onClick={handleCreateGallery}
                  className={cn(
                    'inline-flex items-center gap-2 sm:gap-2.5 px-6 sm:px-8 py-3 sm:py-4',
                    'rounded-xl font-semibold text-white',
                    // Enhanced gradient
                    'bg-gradient-to-r from-blue-500 to-cyan-500',
                    'hover:from-blue-600 hover:to-cyan-600',
                    // iOS-style multi-layer shadow with glow
                    'shadow-[0_2px_4px_rgba(59,130,246,0.2),0_8px_16px_rgba(59,130,246,0.3),0_16px_32px_rgba(59,130,246,0.25)]',
                    'hover:shadow-[0_4px_8px_rgba(59,130,246,0.3),0_12px_24px_rgba(59,130,246,0.4),0_20px_40px_rgba(59,130,246,0.3)]',
                    // Inner highlight
                    'shadow-[inset_0_1px_0_rgba(255,255,255,0.3)]',
                    // Smooth transitions with hover lift
                    'transition-all duration-300 hover:-translate-y-1',
                    // iOS-style press effect
                    'active:scale-[0.97] active:translate-y-0',
                    'touch-target min-h-touch'
                  )}
                >
                  <PlusIcon className="w-5 h-5" />
                  Create Gallery
                  <ArrowRightIcon className="w-5 h-5 opacity-70 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all hidden sm:block" />
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Checklist (T125) with slide-in animation */}
          <div
            className={cn(
              "lg:col-span-1",
              !prefersReducedMotion && (isMobile ? "animate-fade-in-up" : "animate-slide-in-right")
            )}
            style={{ animationDelay: prefersReducedMotion ? '0ms' : '300ms' }}
          >
            <ActivationChecklist onItemClick={handleChecklistItemClick} />
          </div>
        </div>
      </main>

      {/* Mobile FAB for quick gallery creation */}
      {(isMobile || isTablet) && (
        <button
          onClick={handleCreateGallery}
          className={cn(
            "fixed z-50 w-14 h-14 rounded-full",
            "bg-gradient-to-br from-blue-500 to-cyan-500",
            "shadow-lg shadow-blue-500/40",
            "flex items-center justify-center",
            "active:scale-95 transition-transform",
            !prefersReducedMotion && "animate-fade-in-scale"
          )}
          style={{
            bottom: `calc(1.5rem + ${safeArea.bottom}px)`,
            right: '1rem',
            animationDelay: '800ms',
          }}
          aria-label="Create Gallery"
        >
          <PlusIcon className="w-6 h-6 text-white" />
        </button>
      )}
    </div>
  );
}

export default DashboardPage;
