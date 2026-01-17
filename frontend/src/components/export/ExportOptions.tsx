/**
 * ExportOptions Component
 * Options selection for export configuration
 *
 * Subtask-4-2: Create export wizard component
 */

import type { ReactNode } from 'react';
import { cn } from '../../lib/utils';
import type { ExportType, ExportOptions as ExportOptionsType } from '../../services/export-api';

// ============================================
// Icons
// ============================================

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
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
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

function CheckSquareIcon({ className }: { className?: string }) {
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
      <polyline points="9 11 12 14 22 4" />
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  );
}

function InfoIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface ExportOptionsProps {
  /** Current export type */
  exportType: ExportType | null;
  /** Current export options */
  options: ExportOptionsType;
  /** Callback when export type changes */
  onExportTypeChange: (type: ExportType) => void;
  /** Callback when options change */
  onOptionsChange: (options: ExportOptionsType) => void;
  /** Additional class names */
  className?: string;
}

interface ExportTypeOption {
  value: ExportType;
  label: string;
  description: string;
  icon: ReactNode;
}

// ============================================
// Export Type Options
// ============================================

const exportTypes: ExportTypeOption[] = [
  {
    value: 'workspace',
    label: 'Full Workspace',
    description: 'Export all galleries and photos in this workspace',
    icon: <FolderIcon className="w-6 h-6" />,
  },
  {
    value: 'gallery',
    label: 'Specific Galleries',
    description: 'Choose which galleries to export',
    icon: <ImageIcon className="w-6 h-6" />,
  },
  {
    value: 'selection',
    label: 'Selected Photos',
    description: 'Export only selected photos',
    icon: <CheckSquareIcon className="w-6 h-6" />,
  },
];

// ============================================
// Component
// ============================================

export function ExportOptions({
  exportType,
  options,
  onExportTypeChange,
  onOptionsChange,
  className,
}: ExportOptionsProps) {
  const handleToggleMetadata = () => {
    onOptionsChange({
      ...options,
      include_metadata: !options.include_metadata,
    });
  };

  const handleToggleThumbnails = () => {
    onOptionsChange({
      ...options,
      include_thumbnails: !options.include_thumbnails,
    });
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Export Type Selection */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          What do you want to export?
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {exportTypes.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => onExportTypeChange(type.value)}
              className={cn(
                'p-4 rounded-xl border text-left transition-all duration-200',
                'flex flex-col items-start gap-3',
                exportType === type.value
                  ? 'bg-primary-500/20 border-primary-500/50 ring-2 ring-primary-500/30'
                  : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
              )}
            >
              <div
                className={cn(
                  'w-10 h-10 rounded-lg flex items-center justify-center transition-colors',
                  exportType === type.value
                    ? 'bg-primary-500 text-white'
                    : 'bg-white/10 text-white/60'
                )}
              >
                {type.icon}
              </div>
              <div>
                <p className="font-medium text-white text-sm mb-1">{type.label}</p>
                <p className="text-xs text-white/50">{type.description}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Export Options */}
      {exportType && (
        <div className="space-y-4 animate-fade-up">
          <h3 className="text-lg font-semibold text-white mb-4">
            Export options
          </h3>

          {/* Include Metadata Toggle */}
          <label className="flex items-start gap-3 cursor-pointer group">
            <div className="relative flex items-center">
              <input
                type="checkbox"
                checked={options.include_metadata ?? true}
                onChange={handleToggleMetadata}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-white/10 rounded-full peer-checked:bg-primary-500 transition-colors border border-white/20 peer-checked:border-primary-500" />
              <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5 shadow-sm" />
            </div>
            <div className="flex-1">
              <p className="text-white font-medium text-sm">Include metadata</p>
              <p className="text-white/50 text-xs mt-0.5">
                Export EXIF data, tags, and other photo metadata
              </p>
            </div>
          </label>

          {/* Include Thumbnails Toggle */}
          <label className="flex items-start gap-3 cursor-pointer group">
            <div className="relative flex items-center">
              <input
                type="checkbox"
                checked={options.include_thumbnails ?? false}
                onChange={handleToggleThumbnails}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-white/10 rounded-full peer-checked:bg-primary-500 transition-colors border border-white/20 peer-checked:border-primary-500" />
              <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5 shadow-sm" />
            </div>
            <div className="flex-1">
              <p className="text-white font-medium text-sm">Include thumbnails</p>
              <p className="text-white/50 text-xs mt-0.5">
                Include optimized thumbnail images (increases export size)
              </p>
            </div>
          </label>

          {/* Info Box */}
          <div className="mt-6 p-4 rounded-xl bg-primary-500/10 border border-primary-500/20">
            <div className="flex gap-3">
              <InfoIcon className="w-5 h-5 text-primary-400 shrink-0 mt-0.5" />
              <div className="text-sm text-white/70">
                <p className="font-medium text-white mb-1">Export includes:</p>
                <ul className="space-y-1 text-xs">
                  <li>• Original full-resolution photos</li>
                  <li>• Organized folder structure matching galleries</li>
                  {options.include_metadata && <li>• Complete metadata in JSON format</li>}
                  {options.include_thumbnails && <li>• Preview thumbnails for quick browsing</li>}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExportOptions;
