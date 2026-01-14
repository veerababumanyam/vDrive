/**
 * Dashboard Page
 * Main authenticated dashboard with activation checklist
 *
 * T125: Integrate ActivationChecklist into Dashboard page
 */

import { useNavigate } from 'react-router-dom';
import { ActivationChecklist } from '../components/onboarding/ActivationChecklist';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import type { ActivationChecklistItem } from '../types/onboarding';
import { cn } from '../lib/utils';

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
  },
  {
    label: 'Photos',
    value: '0',
    icon: ImageIcon,
    gradient: 'from-violet-500 to-purple-500',
    lightBg: 'bg-violet-50',
    darkBg: 'bg-violet-500/20',
    iconColor: 'text-violet-600 dark:text-violet-400',
  },
  {
    label: 'Clients',
    value: '0',
    icon: UsersIcon,
    gradient: 'from-emerald-500 to-teal-500',
    lightBg: 'bg-emerald-50',
    darkBg: 'bg-emerald-500/20',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
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
  const workspaceName = localStorage.getItem('workspace_name') || 'Your Studio';

  const handleChecklistItemClick = (item: ActivationChecklistItem) => {
    if (item.action_url) {
      navigate(item.action_url);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-warm-950 transition-colors duration-300 relative overflow-hidden">
      {/* Gradient Mesh Background - Light Mode */}
      <div className="absolute inset-0 -z-10 dark:hidden">
        <div className="absolute top-0 -left-1/4 w-1/2 h-1/2 bg-gradient-to-br from-blue-100/80 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute top-1/4 -right-1/4 w-1/2 h-1/2 bg-gradient-to-bl from-violet-100/60 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 left-1/3 w-1/2 h-1/2 bg-gradient-to-t from-cyan-100/50 via-transparent to-transparent rounded-full blur-3xl" />
      </div>

      {/* Aurora Background - Dark Mode */}
      <div className="aurora-bg hidden dark:block" />

      {/* Header - with entrance animation */}
      <header className="sticky top-0 z-40 bg-white/70 dark:bg-warm-950/80 backdrop-blur-xl border-b border-neutral-200/50 dark:border-white/10 transition-colors animate-fade-in-down">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <a href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/25 group-hover:shadow-blue-500/40 transition-shadow">
              <CameraIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-neutral-900 dark:text-white">vDrive</span>
          </a>

          {/* Right side */}
          <div className="flex items-center gap-4">
            <ThemeToggle size="sm" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-10">
        {/* Welcome Header - Enhanced with staggered entrance */}
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 border border-blue-500/20 mb-4 animate-fade-in-up stagger-1">
            <SparklesIcon className="w-4 h-4 text-blue-500 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Welcome back</span>
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-white mb-3 animate-fade-in-up stagger-2">
            {workspaceName}
          </h1>
          <p className="text-lg text-neutral-600 dark:text-white/60 animate-fade-in-up stagger-3">
            Let's get your photography business set up for success.
          </p>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Stats & Actions */}
          <div className="lg:col-span-2 space-y-8">
            {/* Quick Stats - Enhanced with unique colors and staggered entrance */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {quickStats.map((stat, index) => (
                <div
                  key={stat.label}
                  className={cn(
                    'group relative overflow-hidden rounded-2xl p-5 transition-all duration-300',
                    'bg-white dark:bg-white/[0.08] backdrop-blur-xl',
                    'border border-neutral-200/80 dark:border-white/10',
                    'shadow-lg shadow-neutral-200/50 dark:shadow-none',
                    'hover:shadow-xl hover:-translate-y-1 dark:hover:bg-white/[0.12]',
                    'animate-fade-in-up'
                  )}
                  style={{ animationDelay: `${200 + index * 100}ms` }}
                >
                  {/* Gradient accent line */}
                  <div className={cn(
                    'absolute top-0 left-0 right-0 h-1 bg-gradient-to-r',
                    stat.gradient
                  )} />

                  <div className="flex items-center gap-4">
                    <div className={cn(
                      'w-12 h-12 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110',
                      stat.lightBg,
                      `dark:${stat.darkBg}`
                    )}>
                      <stat.icon className={cn('w-6 h-6', stat.iconColor)} />
                    </div>
                    <div>
                      <p className="text-3xl font-bold text-neutral-900 dark:text-white">{stat.value}</p>
                      <p className="text-sm font-medium text-neutral-500 dark:text-white/60">{stat.label}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Quick Actions - Enhanced with unique gradients and entrance animation */}
            <div className={cn(
              'rounded-2xl p-6 transition-all duration-300',
              'bg-white dark:bg-white/[0.08] backdrop-blur-xl',
              'border border-neutral-200/80 dark:border-white/10',
              'shadow-lg shadow-neutral-200/50 dark:shadow-none',
              'animate-fade-in-up'
            )} style={{ animationDelay: '500ms' }}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-xl font-bold text-neutral-900 dark:text-white">Quick Actions</h2>
                <span className="text-sm text-neutral-500 dark:text-white/50">Get started quickly</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {quickActions.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => navigate(action.href)}
                    className={cn(
                      'group relative flex flex-col items-start p-5 rounded-xl text-left',
                      'bg-neutral-50 dark:bg-white/5',
                      'border-l-4 border border-neutral-200/80 dark:border-white/10',
                      action.borderAccent,
                      'hover:bg-neutral-100 dark:hover:bg-white/10',
                      'transition-all duration-300 hover:shadow-lg',
                      action.shadow
                    )}
                  >
                    {/* Icon with gradient background */}
                    <div className={cn(
                      'w-11 h-11 rounded-xl bg-gradient-to-br flex items-center justify-center mb-4',
                      'shadow-md transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg',
                      action.gradient,
                      action.hoverGradient,
                      action.shadow
                    )}>
                      <action.icon className="w-5 h-5 text-white" />
                    </div>

                    <div className="flex-1">
                      <p className="font-semibold text-neutral-900 dark:text-white mb-1">{action.label}</p>
                      <p className="text-sm text-neutral-500 dark:text-white/60">{action.description}</p>
                    </div>

                    {/* Arrow indicator */}
                    <div className="absolute top-5 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                      <ArrowRightIcon className="w-5 h-5 text-neutral-400 dark:text-white/40" />
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Empty State - Premium Design with entrance animation */}
            <div className={cn(
              'relative overflow-hidden rounded-2xl p-8 transition-all duration-300',
              'bg-gradient-to-br from-white to-neutral-50 dark:from-white/[0.08] dark:to-white/[0.04]',
              'border border-neutral-200/80 dark:border-white/10',
              'shadow-lg shadow-neutral-200/50 dark:shadow-none',
              'animate-fade-in-scale'
            )} style={{ animationDelay: '650ms' }}>
              {/* Decorative gradient orbs */}
              <div className="absolute -top-20 -right-20 w-40 h-40 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full blur-3xl" />
              <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-gradient-to-br from-violet-500/20 to-purple-500/20 rounded-full blur-3xl" />

              <div className="relative text-center py-8">
                {/* Animated icon container */}
                <div className="relative w-20 h-20 mx-auto mb-6">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl opacity-20 animate-pulse" />
                  <div className="absolute inset-1 bg-white dark:bg-warm-950 rounded-xl" />
                  <div className="relative w-full h-full flex items-center justify-center">
                    <ImageIcon className="w-10 h-10 text-blue-500 dark:text-blue-400" />
                  </div>
                </div>

                <h3 className="text-2xl font-bold text-neutral-900 dark:text-white mb-3">
                  Create your first gallery
                </h3>
                <p className="text-neutral-600 dark:text-white/60 mb-8 max-w-md mx-auto text-lg">
                  Start showcasing your photography to clients with beautiful, customizable galleries.
                </p>

                <button
                  onClick={() => navigate('/galleries/new')}
                  className={cn(
                    'inline-flex items-center gap-2.5 px-8 py-4 rounded-xl font-semibold text-white',
                    'bg-gradient-to-r from-blue-500 to-cyan-500',
                    'hover:from-blue-600 hover:to-cyan-600',
                    'shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40',
                    'transition-all duration-300 hover:-translate-y-0.5'
                  )}
                >
                  <PlusIcon className="w-5 h-5" />
                  Create Gallery
                  <ArrowRightIcon className="w-5 h-5 opacity-70" />
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Checklist (T125) with slide-in animation */}
          <div className="lg:col-span-1 animate-slide-in-right" style={{ animationDelay: '300ms' }}>
            <ActivationChecklist onItemClick={handleChecklistItemClick} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default DashboardPage;
