/**
 * GalleryCreate Page
 *
 * Premium form for creating new galleries with:
 * - Step-by-step wizard flow
 * - Real-time validation
 * - Cover image upload
 * - Advanced settings
 */

import { useState, useCallback, useRef, type FormEvent, type ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../lib/utils';
import { useHaptic, useBreakpoint } from '../hooks';
import { AppButton } from '../components/ui/AppButton';
import { AppCard } from '../components/ui/AppCard';
import { AppInput } from '../components/ui/AppInput';
import { createGallery } from '../services/gallery-api';
import type { GalleryCreateRequest, DownloadPolicy, LayoutStyle } from '../types/gallery';

/**
 * Arrow Left icon for back navigation
 */
function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
    </svg>
  );
}

/**
 * Gallery icon
 */
function GalleryIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M22 16V4c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2zm-11-4l2.03 2.71L16 11l4 5H8l3-4zM2 6v14c0 1.1.9 2 2 2h14v-2H4V6H2z" />
    </svg>
  );
}

/**
 * Calendar icon
 */
function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z" />
    </svg>
  );
}

/**
 * Settings icon
 */
function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
    </svg>
  );
}

/**
 * Check icon
 */
function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

/**
 * Upload icon for cover image
 */
function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" />
    </svg>
  );
}

/**
 * X/Close icon for removing cover
 */
function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

/**
 * Cover Image Upload component with preview
 */
function CoverImageUpload({
  coverPreview,
  onFileSelect,
  onRemove,
}: {
  coverPreview: string | null;
  onFileSelect: (e: ChangeEvent<HTMLInputElement>) => void;
  onRemove: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const haptic = useHaptic();

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
        Cover Image
      </label>
      <div
        className={cn(
          'relative aspect-video rounded-xl overflow-hidden',
          'border-2 border-dashed transition-all duration-200',
          coverPreview
            ? 'border-transparent'
            : 'border-neutral-300 dark:border-white/20 hover:border-primary-400 dark:hover:border-primary-500'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={onFileSelect}
        />

        <AnimatePresence mode="wait">
          {coverPreview ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0"
            >
              {/* Cover preview image */}
              <img
                src={coverPreview}
                alt="Cover preview"
                className="w-full h-full object-cover"
              />
              {/* Overlay with actions */}
              <div
                className={cn(
                  'absolute inset-0 bg-black/40 opacity-0 hover:opacity-100',
                  'flex items-center justify-center gap-3',
                  'transition-opacity duration-200'
                )}
              >
                <button
                  type="button"
                  onClick={() => {
                    haptic.light();
                    inputRef.current?.click();
                  }}
                  className={cn(
                    'p-3 rounded-full',
                    'bg-white/20 backdrop-blur-sm text-white',
                    'hover:bg-white/30 transition-colors'
                  )}
                  aria-label="Change cover image"
                >
                  <UploadIcon className="w-5 h-5" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    haptic.light();
                    onRemove();
                  }}
                  className={cn(
                    'p-3 rounded-full',
                    'bg-red-500/80 backdrop-blur-sm text-white',
                    'hover:bg-red-600 transition-colors'
                  )}
                  aria-label="Remove cover image"
                >
                  <XIcon className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.button
              key="upload"
              type="button"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => {
                haptic.light();
                inputRef.current?.click();
              }}
              className={cn(
                'absolute inset-0 w-full h-full',
                'flex flex-col items-center justify-center gap-2',
                'text-neutral-500 dark:text-neutral-400',
                'hover:text-primary-600 dark:hover:text-primary-400',
                'hover:bg-neutral-50 dark:hover:bg-white/5',
                'transition-all cursor-pointer'
              )}
            >
              <div
                className={cn(
                  'w-12 h-12 rounded-full',
                  'bg-neutral-100 dark:bg-white/10',
                  'flex items-center justify-center',
                  'group-hover:bg-primary-100 dark:group-hover:bg-primary-500/20'
                )}
              >
                <UploadIcon className="w-6 h-6" />
              </div>
              <span className="text-sm font-medium">Add Cover Image</span>
              <span className="text-xs opacity-60">Recommended: 16:9 ratio</span>
            </motion.button>
          )}
        </AnimatePresence>
      </div>
      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        This will be shown in gallery listings. JPG, PNG, or WebP (max 10MB)
      </p>
    </div>
  );
}

// Download policy options
const downloadPolicies: Array<{ value: DownloadPolicy; label: string; description: string }> = [
  { value: 'VIEW_ONLY', label: 'View Only', description: 'Clients can view but not download' },
  { value: 'WEB_ONLY', label: 'Web Quality', description: 'Compressed downloads for sharing' },
  { value: 'WATERMARKED_ONLY', label: 'Watermarked', description: 'Full resolution with watermark' },
  { value: 'ORIGINAL_ALLOWED', label: 'Full Access', description: 'Original quality downloads' },
];

// Layout style options
const layoutStyles: Array<{ value: LayoutStyle; label: string; description: string }> = [
  { value: 'tab', label: 'Tabs', description: 'Sub-galleries as tabs' },
  { value: 'continuous_scroll', label: 'Continuous', description: 'All photos in one scroll' },
];

interface FormData {
  title: string;
  description: string;
  client_name: string;
  shoot_date: string;
  password: string;
  email_registration_required: boolean;
  download_policy: DownloadPolicy;
  layout_style: LayoutStyle;
}

interface FormErrors {
  title?: string;
  client_name?: string;
  shoot_date?: string;
  password?: string;
}

export function GalleryCreatePage() {
  const navigate = useNavigate();
  const haptic = useHaptic();
  const { isMobile } = useBreakpoint();

  // Form state
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    client_name: '',
    shoot_date: '',
    password: '',
    email_registration_required: false,
    download_policy: 'WEB_ONLY',
    layout_style: 'tab',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Cover image state
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverPreview, setCoverPreview] = useState<string | null>(null);

  // Handle cover image selection
  const handleCoverSelect = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setErrors((prev) => ({ ...prev, title: 'Cover image must be JPG, PNG, or WebP' }));
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setErrors((prev) => ({ ...prev, title: 'Cover image must be less than 10MB' }));
      return;
    }

    setCoverFile(file);

    // Create preview URL
    const reader = new FileReader();
    reader.onloadend = () => {
      setCoverPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    haptic.success();
  }, [haptic]);

  // Remove cover image
  const handleCoverRemove = useCallback(() => {
    setCoverFile(null);
    setCoverPreview(null);
    haptic.light();
  }, [haptic]);

  // Validate form
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Gallery title is required';
    } else if (formData.title.length > 100) {
      newErrors.title = 'Title must be less than 100 characters';
    }

    if (formData.shoot_date) {
      const date = new Date(formData.shoot_date);
      if (isNaN(date.getTime())) {
        newErrors.shoot_date = 'Invalid date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  // Handle field change
  const handleChange = useCallback(
    (field: keyof FormData, value: string | boolean) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      // Clear error when user starts typing
      if (errors[field as keyof FormErrors]) {
        setErrors((prev) => ({ ...prev, [field]: undefined }));
      }
    },
    [errors]
  );

  // Handle form submission
  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        haptic.error();
        return;
      }

      setIsSubmitting(true);

      try {
        const request: GalleryCreateRequest = {
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          client_name: formData.client_name.trim() || undefined,
          shoot_date: formData.shoot_date || undefined,
          password: formData.password || undefined,
          email_registration_required: formData.email_registration_required,
          download_policy: formData.download_policy,
          layout_style: formData.layout_style,
        };

        const gallery = await createGallery(request);

        // TODO: If cover file exists, upload it and update gallery
        // This would require a separate API call after gallery creation
        // For now, cover can be set after gallery is created via edit
        if (coverFile) {
          console.log('Cover file selected, will be uploaded in future implementation');
        }

        haptic.success();

        // Navigate to the new gallery
        navigate(`/galleries/${gallery.gallery_id}`, { replace: true });
      } catch (err) {
        haptic.error();
        setErrors({
          title: err instanceof Error ? err.message : 'Failed to create gallery',
        });
      } finally {
        setIsSubmitting(false);
      }
    },
    [formData, validateForm, navigate, haptic]
  );

  return (
    <div
      className={cn(
        'min-h-screen',
        'bg-neutral-50 dark:bg-neutral-900'
      )}
    >
      {/* Header */}
      <header
        className={cn(
          'sticky top-0 z-20',
          'bg-white/80 dark:bg-neutral-900/80',
          'backdrop-blur-xl',
          'border-b border-neutral-200 dark:border-white/10',
          'px-4 py-4 sm:px-6'
        )}
      >
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate('/galleries')}
            className={cn(
              'p-2 rounded-full',
              'text-neutral-600 hover:text-neutral-900',
              'dark:text-neutral-400 dark:hover:text-white',
              'hover:bg-neutral-100 dark:hover:bg-white/10',
              'transition-colors'
            )}
            aria-label="Back to galleries"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <h1 className="text-xl sm:text-2xl font-bold text-neutral-800 dark:text-white">
            Create Gallery
          </h1>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-2xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info Card */}
          <AppCard variant="glass" padding="lg">
            <div className="flex items-center gap-3 mb-6">
              <div
                className={cn(
                  'w-10 h-10 rounded-full',
                  'bg-primary-100 dark:bg-primary-500/20',
                  'flex items-center justify-center'
                )}
              >
                <GalleryIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h2 className="font-semibold text-neutral-800 dark:text-white">
                  Basic Information
                </h2>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                  Essential details for your gallery
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <AppInput
                label="Gallery Title"
                placeholder="e.g., Smith Wedding 2024"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                error={errors.title}
                required
                autoFocus
              />

              <AppInput
                label="Client Name"
                placeholder="e.g., John & Jane Smith"
                value={formData.client_name}
                onChange={(e) => handleChange('client_name', e.target.value)}
                error={errors.client_name}
              />

              <AppInput
                label="Shoot Date"
                type="date"
                value={formData.shoot_date}
                onChange={(e) => handleChange('shoot_date', e.target.value)}
                error={errors.shoot_date}
                leftIcon={<CalendarIcon className="w-5 h-5 text-neutral-400" />}
              />

              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                  Description
                </label>
                <textarea
                  placeholder="Optional notes about this gallery..."
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  rows={3}
                  className={cn(
                    'w-full px-4 py-3 rounded-xl',
                    'bg-white dark:bg-white/5',
                    'border border-neutral-200 dark:border-white/10',
                    'text-neutral-800 dark:text-white',
                    'placeholder:text-neutral-400 dark:placeholder:text-neutral-500',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
                    'transition-all resize-none'
                  )}
                />
              </div>

              {/* Cover Image Upload */}
              <CoverImageUpload
                coverPreview={coverPreview}
                onFileSelect={handleCoverSelect}
                onRemove={handleCoverRemove}
              />
            </div>
          </AppCard>

          {/* Advanced Settings Toggle */}
          <button
            type="button"
            onClick={() => {
              setShowAdvanced(!showAdvanced);
              haptic.light();
            }}
            className={cn(
              'w-full flex items-center justify-between px-4 py-3',
              'rounded-xl',
              'bg-neutral-100 dark:bg-white/5',
              'border border-neutral-200 dark:border-white/10',
              'text-neutral-700 dark:text-neutral-300',
              'hover:bg-neutral-200 dark:hover:bg-white/10',
              'transition-colors'
            )}
          >
            <div className="flex items-center gap-3">
              <SettingsIcon className="w-5 h-5" />
              <span className="font-medium">Advanced Settings</span>
            </div>
            <svg
              className={cn(
                'w-5 h-5 transition-transform',
                showAdvanced && 'rotate-180'
              )}
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" />
            </svg>
          </button>

          {/* Advanced Settings Card */}
          {showAdvanced && (
            <AppCard variant="glass" padding="lg" className="animate-slide-down">
              <h2 className="font-semibold text-neutral-800 dark:text-white mb-6">
                Gallery Settings
              </h2>

              <div className="space-y-6">
                {/* Download Policy */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
                    Download Policy
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {downloadPolicies.map((policy) => (
                      <button
                        key={policy.value}
                        type="button"
                        onClick={() => {
                          handleChange('download_policy', policy.value);
                          haptic.light();
                        }}
                        className={cn(
                          'p-3 rounded-xl text-left',
                          'border-2 transition-all',
                          formData.download_policy === policy.value
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10'
                            : 'border-neutral-200 dark:border-white/10 hover:border-neutral-300 dark:hover:border-white/20'
                        )}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span
                            className={cn(
                              'text-sm font-medium',
                              formData.download_policy === policy.value
                                ? 'text-primary-700 dark:text-primary-300'
                                : 'text-neutral-700 dark:text-neutral-300'
                            )}
                          >
                            {policy.label}
                          </span>
                          {formData.download_policy === policy.value && (
                            <CheckIcon className="w-4 h-4 text-primary-500" />
                          )}
                        </div>
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">
                          {policy.description}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Layout Style */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
                    Layout Style
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {layoutStyles.map((style) => (
                      <button
                        key={style.value}
                        type="button"
                        onClick={() => {
                          handleChange('layout_style', style.value);
                          haptic.light();
                        }}
                        className={cn(
                          'p-3 rounded-xl text-left',
                          'border-2 transition-all',
                          formData.layout_style === style.value
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10'
                            : 'border-neutral-200 dark:border-white/10 hover:border-neutral-300 dark:hover:border-white/20'
                        )}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span
                            className={cn(
                              'text-sm font-medium',
                              formData.layout_style === style.value
                                ? 'text-primary-700 dark:text-primary-300'
                                : 'text-neutral-700 dark:text-neutral-300'
                            )}
                          >
                            {style.label}
                          </span>
                          {formData.layout_style === style.value && (
                            <CheckIcon className="w-4 h-4 text-primary-500" />
                          )}
                        </div>
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">
                          {style.description}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Password Protection */}
                <AppInput
                  label="Gallery Password"
                  type="password"
                  placeholder="Optional - leave empty for no password"
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  helperText="Clients will need this password to access the gallery"
                />

                {/* Email Registration Toggle */}
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
                      Require Email Registration
                    </label>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                      Collect client emails before they can view
                    </p>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={formData.email_registration_required}
                    onClick={() => {
                      handleChange(
                        'email_registration_required',
                        !formData.email_registration_required
                      );
                      haptic.light();
                    }}
                    className={cn(
                      'relative w-12 h-7 rounded-full transition-colors',
                      formData.email_registration_required
                        ? 'bg-primary-500'
                        : 'bg-neutral-200 dark:bg-white/20'
                    )}
                  >
                    <span
                      className={cn(
                        'absolute top-1 w-5 h-5 rounded-full bg-white shadow-sm transition-transform',
                        formData.email_registration_required
                          ? 'translate-x-6'
                          : 'translate-x-1'
                      )}
                    />
                  </button>
                </div>
              </div>
            </AppCard>
          )}

          {/* Submit Button */}
          <div className="flex flex-col sm:flex-row gap-3">
            <AppButton
              type="button"
              variant="outline"
              size="lg"
              onClick={() => navigate('/galleries')}
              className="sm:flex-1"
            >
              Cancel
            </AppButton>
            <AppButton
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              glowOnHover
              className="sm:flex-1"
            >
              {isMobile ? 'Create' : 'Create Gallery'}
            </AppButton>
          </div>
        </form>
      </main>
    </div>
  );
}

export default GalleryCreatePage;
