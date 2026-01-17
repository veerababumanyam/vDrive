/**
 * PlatformSelector Component
 * Select migration source platform
 *
 * Subtask-5-4: Create migration wizard UI component
 */

import { cn } from '../../lib/utils';
import type { MigrationPlatform } from '../../services/migration-api';

// ============================================
// Icons
// ============================================

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

// ============================================
// Types
// ============================================

export interface PlatformSelectorProps {
  /** Currently selected platform */
  selectedPlatform: MigrationPlatform | null;
  /** Callback when platform changes */
  onPlatformChange: (platform: MigrationPlatform) => void;
  /** Additional class names */
  className?: string;
}

interface PlatformOption {
  value: MigrationPlatform;
  label: string;
  description: string;
  gradient: string;
}

// ============================================
// Platform Options
// ============================================

const platforms: PlatformOption[] = [
  {
    value: 'pixieset',
    label: 'Pixieset',
    description: 'Import galleries and photos from Pixieset',
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    value: 'pictime',
    label: 'Pic-Time',
    description: 'Import galleries and photos from Pic-Time',
    gradient: 'from-violet-500 to-purple-500',
  },
  {
    value: 'shootproof',
    label: 'ShootProof',
    description: 'Import galleries and photos from ShootProof',
    gradient: 'from-emerald-500 to-teal-500',
  },
  {
    value: 'zenfolio',
    label: 'Zenfolio',
    description: 'Import galleries and photos from Zenfolio',
    gradient: 'from-amber-500 to-orange-500',
  },
  {
    value: 'smugmug',
    label: 'SmugMug',
    description: 'Import galleries and photos from SmugMug',
    gradient: 'from-pink-500 to-rose-500',
  },
];

// ============================================
// Component
// ============================================

export function PlatformSelector({
  selectedPlatform,
  onPlatformChange,
  className,
}: PlatformSelectorProps) {
  return (
    <div className={cn('space-y-6', className)}>
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          Which platform are you migrating from?
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {platforms.map((platform) => (
            <button
              key={platform.value}
              type="button"
              onClick={() => onPlatformChange(platform.value)}
              className={cn(
                'p-4 rounded-xl border text-left transition-all duration-200',
                'flex items-start gap-3 group',
                selectedPlatform === platform.value
                  ? 'bg-primary-500/20 border-primary-500/50 ring-2 ring-primary-500/30'
                  : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
              )}
            >
              <div
                className={cn(
                  'w-10 h-10 rounded-lg flex items-center justify-center transition-all',
                  'bg-gradient-to-br',
                  platform.gradient,
                  selectedPlatform === platform.value
                    ? 'opacity-100 scale-110'
                    : 'opacity-70 group-hover:opacity-100 group-hover:scale-105'
                )}
              >
                <ImageIcon className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white text-sm mb-1">{platform.label}</p>
                <p className="text-xs text-white/50">{platform.description}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Info note */}
      {selectedPlatform && (
        <div className="p-4 rounded-xl bg-primary-500/10 border border-primary-500/20 animate-fade-up">
          <p className="text-sm text-white/70">
            <span className="font-medium text-white">Note:</span> You'll need your API credentials
            from {platforms.find(p => p.value === selectedPlatform)?.label} to proceed with the migration.
          </p>
        </div>
      )}
    </div>
  );
}

export default PlatformSelector;
