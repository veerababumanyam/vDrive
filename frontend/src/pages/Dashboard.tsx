/**
 * Dashboard Page
 * Main authenticated dashboard with activation checklist
 *
 * T125: Integrate ActivationChecklist into Dashboard page
 */

import { useNavigate } from 'react-router-dom';
import { ActivationChecklist } from '../components/onboarding/ActivationChecklist';
import { ThemeToggle } from '../components/onboarding/ThemeToggle';
import { AppCard } from '../components/ui/AppCard';
import type { ActivationChecklistItem } from '../types/onboarding';

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

// ============================================
// Quick Stats
// ============================================

const quickStats = [
  { label: 'Galleries', value: '0', icon: FolderIcon },
  { label: 'Photos', value: '0', icon: ImageIcon },
  { label: 'Clients', value: '0', icon: UsersIcon },
];

// ============================================
// Quick Actions
// ============================================

const quickActions = [
  {
    label: 'Create Gallery',
    description: 'Start a new photo gallery',
    icon: FolderIcon,
    href: '/galleries/new',
  },
  {
    label: 'Upload Photos',
    description: 'Add photos to your library',
    icon: ImageIcon,
    href: '/upload',
  },
  {
    label: 'Invite Client',
    description: 'Share galleries with clients',
    icon: UsersIcon,
    href: '/clients/new',
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
    <div className="min-h-screen bg-neutral-950">
      {/* Aurora Background */}
      <div className="aurora-bg" />

      {/* Header */}
      <header className="sticky top-0 z-40 bg-neutral-950/80 backdrop-blur-xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <a href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <CameraIcon className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-white">vDrive</span>
          </a>

          {/* Right side */}
          <div className="flex items-center gap-4">
            <ThemeToggle size="sm" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome to {workspaceName}
          </h1>
          <p className="text-white/60">
            Let's get your photography business set up for success.
          </p>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Stats & Actions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4">
              {quickStats.map((stat) => (
                <AppCard key={stat.label} variant="glass" padding="md">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center">
                      <stat.icon className="w-5 h-5 text-white/50" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-white">{stat.value}</p>
                      <p className="text-sm text-white/50">{stat.label}</p>
                    </div>
                  </div>
                </AppCard>
              ))}
            </div>

            {/* Quick Actions */}
            <AppCard variant="glass" padding="md">
              <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {quickActions.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => navigate(action.href)}
                    className="flex flex-col items-center p-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all duration-200 group"
                  >
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mb-3 group-hover:from-primary-500/30 group-hover:to-accent-500/30 transition-colors">
                      <action.icon className="w-6 h-6 text-primary-400" />
                    </div>
                    <p className="font-medium text-white text-sm">{action.label}</p>
                    <p className="text-xs text-white/50 mt-1">{action.description}</p>
                  </button>
                ))}
              </div>
            </AppCard>

            {/* Empty State */}
            <AppCard variant="glass" padding="lg">
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mx-auto mb-4">
                  <ImageIcon className="w-8 h-8 text-primary-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  No galleries yet
                </h3>
                <p className="text-white/60 mb-6 max-w-md mx-auto">
                  Create your first gallery to start showcasing your photography
                  to clients.
                </p>
                <button
                  onClick={() => navigate('/galleries/new')}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium hover:opacity-90 transition-opacity"
                >
                  <PlusIcon className="w-5 h-5" />
                  Create Gallery
                </button>
              </div>
            </AppCard>
          </div>

          {/* Right Column - Checklist (T125) */}
          <div className="lg:col-span-1">
            <ActivationChecklist onItemClick={handleChecklistItemClick} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default DashboardPage;
