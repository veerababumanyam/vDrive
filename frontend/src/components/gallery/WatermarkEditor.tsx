/**
 * WatermarkEditor Component
 * Configure text and image watermarks with position, opacity, and size controls
 *
 * Subtask-4-1: Create WatermarkEditor component with text/image options
 */

import { useState } from 'react';
import { AppButton } from '../ui/AppButton';
import { AppInput } from '../ui/AppInput';
import { AppCard } from '../ui/AppCard';
import { cn } from '../../lib/utils';
import type {
  WatermarkConfig,
  WatermarkType,
  WatermarkPosition,
  TextWatermark,
  ImageWatermark
} from '../../types/watermark';

// ============================================
// Icons
// ============================================

function TypeIcon({ className }: { className?: string }) {
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
      <polyline points="4 7 4 4 20 4 20 7" />
      <line x1="9" x2="15" y1="20" y2="20" />
      <line x1="12" x2="12" y1="4" y2="20" />
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
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
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

function PaletteIcon({ className }: { className?: string }) {
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
      <circle cx="13.5" cy="6.5" r=".5" fill="currentColor" />
      <circle cx="17.5" cy="10.5" r=".5" fill="currentColor" />
      <circle cx="8.5" cy="7.5" r=".5" fill="currentColor" />
      <circle cx="6.5" cy="12.5" r=".5" fill="currentColor" />
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z" />
    </svg>
  );
}

function DropletIcon({ className }: { className?: string }) {
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
      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
    </svg>
  );
}

function MaximizeIcon({ className }: { className?: string }) {
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
      <path d="M8 3H5a2 2 0 0 0-2 2v3" />
      <path d="M21 8V5a2 2 0 0 0-2-2h-3" />
      <path d="M3 16v3a2 2 0 0 0 2 2h3" />
      <path d="M16 21h3a2 2 0 0 0 2-2v-3" />
    </svg>
  );
}

function RotateCwIcon({ className }: { className?: string }) {
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
      <path d="M21 2v6h-6" />
      <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
      <path d="M3 12a9 9 0 0 0 15 6.7" />
    </svg>
  );
}

// ============================================
// Types
// ============================================



export interface WatermarkEditorProps {
  /** Initial watermark configuration */
  value?: WatermarkConfig;
  /** Callback when configuration changes */
  onChange?: (config: WatermarkConfig) => void;
  /** Callback when save is clicked */
  onSave?: (config: WatermarkConfig) => void;
  /** Show save button */
  showSaveButton?: boolean;
  /** Loading state for save operation */
  isSaving?: boolean;
  /** Additional class names */
  className?: string;
}

// ============================================
// Position Options
// ============================================

const positionOptions: { value: WatermarkPosition; label: string; icon: string }[] = [
  { value: 'center', label: 'Center', icon: '⊕' },
  { value: 'top_left', label: 'Top Left', icon: '↖' },
  { value: 'top_right', label: 'Top Right', icon: '↗' },
  { value: 'bottom_left', label: 'Bottom Left', icon: '↙' },
  { value: 'bottom_right', label: 'Bottom Right', icon: '↘' },
  { value: 'tiled', label: 'Tiled', icon: '▦' },
];

const fontFamilies = [
  'Arial',
  'Helvetica',
  'Times New Roman',
  'Georgia',
  'Courier New',
  'Verdana',
  'Impact',
];

// ============================================
// Component
// ============================================

export function WatermarkEditor({
  value,
  onChange,
  onSave,
  showSaveButton = true,
  isSaving = false,
  className,
}: WatermarkEditorProps) {
  // Initialize state with default values
  const [watermarkType, setWatermarkType] = useState<WatermarkType>(
    value?.watermark_type || 'text'
  );

  // Extract initial position
  const getInitialPosition = (): WatermarkPosition => {
    if (value?.watermark_type === 'text' && value.text_config?.position) {
      return value.text_config.position;
    }
    if (value?.watermark_type === 'image' && value.image_config?.position) {
      return value.image_config.position;
    }
    return 'bottom_right';
  };

  const [position, setPosition] = useState<WatermarkPosition>(getInitialPosition());

  // Text watermark state
  const [textConfig, setTextConfig] = useState<TextWatermark>(
    value?.text_config || {
      text: '© Your Brand',
      font_size: 24,
      font_family: 'Arial',
      color: '#FFFFFF',
      opacity: 0.7,
      rotation: 0,
    }
  );

  // Image watermark state
  const [imageConfig, setImageConfig] = useState<ImageWatermark>(
    value?.image_config || {
      image_url: '',
      scale: 1.0,
      opacity: 0.7,
    }
  );

  // Build current config
  const currentConfig: WatermarkConfig = {
    enabled: true,
    watermark_type: watermarkType,
    text_config: watermarkType === 'text' ? { ...textConfig, position } : null,
    image_config: watermarkType === 'image' ? { ...imageConfig, position } : null,
  };

  // Handle changes
  const handleTypeChange = (type: WatermarkType) => {
    setWatermarkType(type);

    const newConfig: WatermarkConfig = {
      ...currentConfig,
      watermark_type: type,
      text_config: type === 'text' ? { ...textConfig, position } : null,
      image_config: type === 'image' ? { ...imageConfig, position } : null
    };
    onChange?.(newConfig);
  };

  const handlePositionChange = (newPosition: WatermarkPosition) => {
    setPosition(newPosition);

    const newConfig: WatermarkConfig = {
      ...currentConfig,
      text_config: watermarkType === 'text' ? { ...textConfig, position: newPosition } : null,
      image_config: watermarkType === 'image' ? { ...imageConfig, position: newPosition } : null
    };
    onChange?.(newConfig);
  };

  const handleTextConfigChange = (updates: Partial<TextWatermark>) => {
    const newTextConfig = { ...textConfig, ...updates };
    setTextConfig(newTextConfig);

    const newConfig: WatermarkConfig = {
      ...currentConfig,
      text_config: { ...newTextConfig, position }
    };
    onChange?.(newConfig);
  };

  const handleImageConfigChange = (updates: Partial<ImageWatermark>) => {
    const newImageConfig = { ...imageConfig, ...updates };
    setImageConfig(newImageConfig);

    const newConfig: WatermarkConfig = {
      ...currentConfig,
      image_config: { ...newImageConfig, position }
    };
    onChange?.(newConfig);
  };

  const handleSave = () => {
    onSave?.(currentConfig);
  };

  return (
    <AppCard variant="glass" padding="lg" className={cn('w-full', className)}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-neutral-900 dark:text-white mb-2">
          Watermark Settings
        </h2>
        <p className="text-sm text-neutral-500 dark:text-white/60">
          Configure your watermark to protect your photos
        </p>
      </div>

      <div className="space-y-6">
        {/* Watermark Type Selector */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-3">
            Watermark Type
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleTypeChange('text')}
              className={cn(
                'flex items-center justify-center gap-2 p-4 rounded-xl border-2 transition-all duration-200',
                watermarkType === 'text'
                  ? 'bg-primary-500/20 border-primary-500/50 ring-2 ring-primary-500/30'
                  : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 dark:border-white/20'
              )}
            >
              <TypeIcon className="w-5 h-5 text-neutral-700 dark:text-white" />
              <span className="font-medium text-neutral-900 dark:text-white">Text</span>
            </button>
            <button
              type="button"
              onClick={() => handleTypeChange('image')}
              className={cn(
                'flex items-center justify-center gap-2 p-4 rounded-xl border-2 transition-all duration-200',
                watermarkType === 'image'
                  ? 'bg-primary-500/20 border-primary-500/50 ring-2 ring-primary-500/30'
                  : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 dark:border-white/20'
              )}
            >
              <ImageIcon className="w-5 h-5 text-neutral-700 dark:text-white" />
              <span className="font-medium text-neutral-900 dark:text-white">Logo</span>
            </button>
          </div>
        </div>

        {/* Position Selector */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-3">
            Position
          </label>
          <div className="grid grid-cols-3 gap-2">
            {positionOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => handlePositionChange(option.value)}
                className={cn(
                  'p-3 rounded-lg border transition-all duration-200 text-center',
                  position === option.value
                    ? 'bg-primary-500/20 border-primary-500/50 ring-2 ring-primary-500/30'
                    : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 dark:border-white/20'
                )}
              >
                <div className="text-2xl mb-1">{option.icon}</div>
                <div className="text-xs font-medium text-neutral-900 dark:text-white">
                  {option.label}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Text Watermark Configuration */}
        {watermarkType === 'text' && (
          <div className="space-y-4 animate-fade-up">
            <div className="border-t border-neutral-200 dark:border-white/10 pt-4">
              <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-4">
                Text Options
              </h3>

              {/* Text Input */}
              <AppInput
                label="Watermark Text"
                value={textConfig.text}
                onChange={(e) => handleTextConfigChange({ text: e.target.value })}
                leftIcon={<TypeIcon className="w-5 h-5" />}
                placeholder="© Your Brand"
              />

              {/* Font Family */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-2">
                  Font Family
                </label>
                <select
                  value={textConfig.font_family}
                  onChange={(e) => handleTextConfigChange({ font_family: e.target.value })}
                  className={cn(
                    'w-full rounded-xl border px-4 py-3 transition-all duration-200',
                    'bg-white text-neutral-900 border-neutral-300',
                    'dark:bg-white/[0.06] dark:text-white dark:border-white/20',
                    'focus:outline-none focus:ring-2 focus:border-primary-500 focus:ring-primary-500/20'
                  )}
                >
                  {fontFamilies.map((font) => (
                    <option key={font} value={font}>
                      {font}
                    </option>
                  ))}
                </select>
              </div>

              {/* Font Size */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-2">
                  Font Size: {textConfig.font_size}px
                </label>
                <input
                  type="range"
                  min="12"
                  max="72"
                  step="1"
                  value={textConfig.font_size}
                  onChange={(e) =>
                    handleTextConfigChange({ font_size: parseInt(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              {/* Color */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-2">
                  Color
                </label>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <AppInput
                      type="text"
                      value={textConfig.color}
                      onChange={(e) => handleTextConfigChange({ color: e.target.value })}
                      leftIcon={<PaletteIcon className="w-5 h-5" />}
                      placeholder="#FFFFFF"
                    />
                  </div>
                  <input
                    type="color"
                    value={textConfig.color}
                    onChange={(e) => handleTextConfigChange({ color: e.target.value })}
                    className="w-16 h-12 rounded-xl border border-neutral-300 dark:border-white/20 cursor-pointer"
                  />
                </div>
              </div>

              {/* Opacity */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-2">
                  <DropletIcon className="w-4 h-4 inline mr-1" />
                  Opacity: {Math.round((textConfig.opacity ?? 0.7) * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={textConfig.opacity ?? 0.7}
                  onChange={(e) =>
                    handleTextConfigChange({ opacity: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              {/* Rotation */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-2">
                  <RotateCwIcon className="w-4 h-4 inline mr-1" />
                  Rotation: {textConfig.rotation}°
                </label>
                <input
                  type="range"
                  min="-45"
                  max="45"
                  step="1"
                  value={textConfig.rotation}
                  onChange={(e) =>
                    handleTextConfigChange({ rotation: parseInt(e.target.value) })
                  }
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* Image Watermark Configuration */}
        {watermarkType === 'image' && (
          <div className="space-y-4 animate-fade-up">
            <div className="border-t border-neutral-200 dark:border-white/10 pt-4">
              <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-4">
                Logo Options
              </h3>

              {/* Image URL Input */}
              <AppInput
                label="Logo URL"
                value={imageConfig.image_url}
                onChange={(e) => handleImageConfigChange({ image_url: e.target.value })}
                leftIcon={<ImageIcon className="w-5 h-5" />}
                placeholder="https://example.com/logo.png"
                helperText="Enter URL or upload an image below"
              />

              {/* Upload Button */}
              <div className="mt-3">
                <AppButton
                  variant="outline"
                  size="md"
                  fullWidth
                  leftIcon={<UploadIcon className="w-5 h-5" />}
                  onClick={() => {
                    // TODO: Implement file upload
                  }}
                >
                  Upload Logo
                </AppButton>
              </div>

              {/* Scale */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-2">
                  <MaximizeIcon className="w-4 h-4 inline mr-1" />
                  Scale: {Math.round((imageConfig.scale ?? 1.0) * 100)}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="2"
                  step="0.05"
                  value={imageConfig.scale ?? 1.0}
                  onChange={(e) =>
                    handleImageConfigChange({ scale: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              {/* Opacity */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-neutral-700 dark:text-white/80 mb-2">
                  <DropletIcon className="w-4 h-4 inline mr-1" />
                  Opacity: {Math.round((imageConfig.opacity ?? 0.7) * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={imageConfig.opacity ?? 0.7}
                  onChange={(e) =>
                    handleImageConfigChange({ opacity: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* Save Button */}
        {showSaveButton && (
          <div className="pt-4 border-t border-neutral-200 dark:border-white/10">
            <AppButton
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleSave}
              isLoading={isSaving}
            >
              Save Watermark Settings
            </AppButton>
          </div>
        )}
      </div>
    </AppCard>
  );
}

export default WatermarkEditor;
