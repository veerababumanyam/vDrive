/**
 * GalleryCreate Page
 *
 * Premium iOS-inspired gallery creation wizard.
 * Features:
 * - 📸 Photography-centric design with glassmorphism
 * - 🎨 Animated backgrounds and visual effects
 * - 📱 Mobile-first with haptic feedback
 * - ♿ WCAG 2.1 AA compliant
 */

import { useState, useCallback, useRef, useMemo, type FormEvent, type ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../lib/utils';
import { useHaptic, useBreakpoint, usePrefersReducedMotion } from '../hooks';
import { AppButton } from '../components/ui/AppButton';
import { AppInput } from '../components/ui/AppInput';
import { createGallery } from '../services/gallery-api';
import type { GalleryCreateRequest, DownloadPolicy, LayoutStyle } from '../types/gallery';
import { WorkspaceLayout } from '../components/workspace/WorkspaceLayout';

// ============================================================================
// Icons
// ============================================================================

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
    </svg>
  );
}

function GalleryIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M22 16V4c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2zm-11-4l2.03 2.71L16 11l4 5H8l3-4zM2 6v14c0 1.1.9 2 2 2h14v-2H4V6H2z" />
    </svg>
  );
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z" />
    </svg>
  );
}

function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

function SparkleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3zm7 14l.62 2.38L22 20l-2.38.62L19 23l-.62-2.38L16 20l2.38-.62L19 17zM5 17l.62 2.38L8 20l-2.38.62L5 23l-.62-2.38L2 20l2.38-.62L5 17z" />
    </svg>
  );
}

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" />
    </svg>
  );
}

// ============================================================================
// Animated Backgrounds
// ============================================================================

function MorphingBlob() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) {
    return (
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl" />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div
        className="absolute top-0 right-0 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-morph"
        style={{ animationDuration: '20s' }}
      />
      <div
        className="absolute bottom-0 left-0 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl animate-morph"
        style={{ animationDuration: '25s', animationDelay: '-5s' }}
      />
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl animate-morph"
        style={{ animationDuration: '18s', animationDelay: '-10s' }}
      />
    </div>
  );
}

function ParticleEffect() {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) return null;

  const particles = useMemo(() =>
    Array.from({ length: 8 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      size: Math.random() * 3 + 2,
      delay: Math.random() * 5,
      duration: Math.random() * 10 + 15,
    })), []
  );

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {particles.map(particle => (
        <div
          key={particle.id}
          className="absolute rounded-full bg-primary-500/20 animate-float"
          style={{
            left: particle.left,
            top: particle.top,
            width: particle.size,
            height: particle.size,
            animationDelay: `${particle.delay}s`,
            animationDuration: `${particle.duration}s`,
          }}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Section Card Component
// ============================================================================

interface SectionCardProps {
  icon: React.ReactNode;
  emoji: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

function SectionCard({ icon, emoji, title, subtitle, children, className, delay = 0 }: SectionCardProps) {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        'relative overflow-hidden',
        'rounded-3xl p-6 sm:p-8',
        // Glassmorphism
        'bg-white/80 dark:bg-white/[0.08]',
        'border border-neutral-200/80 dark:border-white/10',
        'backdrop-blur-xl',
        // iOS-style shadows
        'shadow-[0_8px_40px_-12px_rgba(0,0,0,0.12),0_0_0_1px_rgba(255,255,255,0.05)_inset]',
        'dark:shadow-[0_8px_40px_-12px_rgba(0,0,0,0.4),0_0_0_1px_rgba(255,255,255,0.05)_inset]',
        // Animation
        !prefersReducedMotion && 'animate-fade-in-up',
        className
      )}
      style={{ animationDelay: prefersReducedMotion ? '0ms' : `${delay}ms` }}
    >
      {/* Decorative gradient */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-primary-500/5 via-transparent to-transparent rounded-full blur-2xl" />

      {/* Header */}
      <div className="relative flex items-center gap-4 mb-6">
        <div
          className={cn(
            'w-12 h-12 rounded-2xl',
            'bg-gradient-to-br from-primary-500 to-primary-600',
            'shadow-lg shadow-primary-500/30',
            'flex items-center justify-center'
          )}
        >
          {icon}
        </div>
        <div>
          <h2 className="font-semibold text-lg text-neutral-800 dark:text-white flex items-center gap-2">
            {title}
            <span aria-hidden="true">{emoji}</span>
          </h2>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            {subtitle}
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="relative space-y-5">
        {children}
      </div>
    </div>
  );
}

// ============================================================================
// Cover Image Upload Component
// ============================================================================

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
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
        Cover Image 🖼️
      </label>
      <div
        className={cn(
          'relative aspect-video rounded-2xl overflow-hidden',
          'border-2 border-dashed',
          !prefersReducedMotion && 'transition-all duration-300',
          coverPreview
            ? 'border-transparent'
            : cn(
                'border-neutral-300 dark:border-white/20',
                'hover:border-primary-400 dark:hover:border-primary-500',
                'hover:bg-primary-50/50 dark:hover:bg-primary-500/5'
              )
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={onFileSelect}
          aria-label="Upload cover image"
        />

        <AnimatePresence mode="wait">
          {coverPreview ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
              className="absolute inset-0"
            >
              <img
                src={coverPreview}
                alt="Cover preview"
                className="w-full h-full object-cover"
              />
              {/* Overlay with actions */}
              <div
                className={cn(
                  'absolute inset-0 bg-black/50 opacity-0 hover:opacity-100',
                  'flex items-center justify-center gap-4',
                  !prefersReducedMotion && 'transition-opacity duration-200'
                )}
              >
                <button
                  type="button"
                  onClick={() => {
                    haptic.light();
                    inputRef.current?.click();
                  }}
                  className={cn(
                    'p-4 rounded-full min-w-[56px] min-h-[56px]',
                    'bg-white/20 backdrop-blur-sm text-white',
                    'hover:bg-white/30',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-white',
                    !prefersReducedMotion && 'transition-colors'
                  )}
                  aria-label="Change cover image"
                >
                  <UploadIcon className="w-6 h-6" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    haptic.light();
                    onRemove();
                  }}
                  className={cn(
                    'p-4 rounded-full min-w-[56px] min-h-[56px]',
                    'bg-rose-500/80 backdrop-blur-sm text-white',
                    'hover:bg-rose-600',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-white',
                    !prefersReducedMotion && 'transition-colors'
                  )}
                  aria-label="Remove cover image"
                >
                  <XIcon className="w-6 h-6" />
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
              transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
              onClick={() => {
                haptic.light();
                inputRef.current?.click();
              }}
              className={cn(
                'absolute inset-0 w-full h-full',
                'flex flex-col items-center justify-center gap-3',
                'text-neutral-500 dark:text-neutral-400',
                'hover:text-primary-600 dark:hover:text-primary-400',
                !prefersReducedMotion && 'transition-all',
                'cursor-pointer',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-inset'
              )}
            >
              <div
                className={cn(
                  'w-16 h-16 rounded-2xl',
                  'bg-neutral-100 dark:bg-white/10',
                  'flex items-center justify-center'
                )}
              >
                <UploadIcon className="w-8 h-8" />
              </div>
              <div className="text-center">
                <span className="block text-sm font-medium">Add Cover Image 📷</span>
                <span className="block text-xs opacity-60 mt-1">Recommended: 16:9 ratio</span>
              </div>
            </motion.button>
          )}
        </AnimatePresence>
      </div>
      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        This will be shown in gallery listings. JPG, PNG, or WebP (max 10MB) ✨
      </p>
    </div>
  );
}

// ============================================================================
// Option Card Component (for download policy, layout style)
// ============================================================================

interface OptionCardProps {
  label: string;
  description: string;
  emoji: string;
  isSelected: boolean;
  onClick: () => void;
}

function OptionCard({ label, description, emoji, isSelected, onClick }: OptionCardProps) {
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <button
      type="button"
      onClick={() => {
        haptic.light();
        onClick();
      }}
      className={cn(
        'relative p-4 rounded-2xl text-left min-h-[80px]',
        'border-2',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
        'focus-visible:ring-offset-white dark:focus-visible:ring-offset-neutral-900',
        !prefersReducedMotion && 'transition-all duration-200',
        isSelected
          ? cn(
              'border-primary-500 bg-primary-50 dark:bg-primary-500/10',
              'shadow-lg shadow-primary-500/20'
            )
          : cn(
              'border-neutral-200 dark:border-white/10',
              'bg-white/50 dark:bg-white/5',
              'hover:border-neutral-300 dark:hover:border-white/20',
              'hover:bg-white dark:hover:bg-white/10'
            )
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span aria-hidden="true">{emoji}</span>
          <span
            className={cn(
              'text-sm font-medium',
              isSelected
                ? 'text-primary-700 dark:text-primary-300'
                : 'text-neutral-700 dark:text-neutral-300'
            )}
          >
            {label}
          </span>
        </div>
        {isSelected && (
          <div className="w-5 h-5 rounded-full bg-primary-500 flex items-center justify-center flex-shrink-0">
            <CheckIcon className="w-3 h-3 text-white" />
          </div>
        )}
      </div>
      <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1.5 ml-6">
        {description}
      </p>
    </button>
  );
}

// ============================================================================
// Toggle Switch Component
// ============================================================================

interface ToggleSwitchProps {
  label: string;
  description: string;
  emoji: string;
  isOn: boolean;
  onToggle: () => void;
}

function ToggleSwitch({ label, description, emoji, isOn, onToggle }: ToggleSwitchProps) {
  const haptic = useHaptic();
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-4 p-4 rounded-2xl',
        'bg-white/50 dark:bg-white/5',
        'border border-neutral-200/80 dark:border-white/10'
      )}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl" aria-hidden="true">{emoji}</span>
        <div>
          <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
            {label}
          </label>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            {description}
          </p>
        </div>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={isOn}
        onClick={() => {
          haptic.light();
          onToggle();
        }}
        className={cn(
          'relative flex-shrink-0 w-14 h-8 rounded-full',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
          'focus-visible:ring-offset-white dark:focus-visible:ring-offset-neutral-900',
          !prefersReducedMotion && 'transition-colors duration-200',
          isOn
            ? 'bg-primary-500 shadow-lg shadow-primary-500/30'
            : 'bg-neutral-200 dark:bg-white/20'
        )}
      >
        <span
          className={cn(
            'absolute top-1 w-6 h-6 rounded-full bg-white shadow-md',
            !prefersReducedMotion && 'transition-transform duration-200',
            isOn ? 'translate-x-7' : 'translate-x-1'
          )}
        />
      </button>
    </div>
  );
}

// ============================================================================
// Form Options
// ============================================================================

const downloadPolicies: Array<{ value: DownloadPolicy; label: string; description: string; emoji: string }> = [
  { value: 'VIEW_ONLY', label: 'View Only', description: 'Clients can view but not download', emoji: '👁️' },
  { value: 'WEB_ONLY', label: 'Web Quality', description: 'Compressed downloads for sharing', emoji: '🌐' },
  { value: 'WATERMARKED_ONLY', label: 'Watermarked', description: 'Full resolution with watermark', emoji: '💧' },
  { value: 'ORIGINAL_ALLOWED', label: 'Full Access', description: 'Original quality downloads', emoji: '✨' },
];

const layoutStyles: Array<{ value: LayoutStyle; label: string; description: string; emoji: string }> = [
  { value: 'tab', label: 'Tabs', description: 'Sub-galleries as tabs', emoji: '📑' },
  { value: 'continuous_scroll', label: 'Continuous', description: 'All photos in one scroll', emoji: '📜' },
];

// ============================================================================
// Form Types
// ============================================================================

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

// ============================================================================
// Main Component
// ============================================================================

export function GalleryCreatePage() {
  const navigate = useNavigate();
  const haptic = useHaptic();
  const { isMobile } = useBreakpoint();
  const prefersReducedMotion = usePrefersReducedMotion();

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

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setErrors((prev) => ({ ...prev, title: 'Cover image must be JPG, PNG, or WebP' }));
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrors((prev) => ({ ...prev, title: 'Cover image must be less than 10MB' }));
      return;
    }

    setCoverFile(file);

    const reader = new FileReader();
    reader.onloadend = () => {
      setCoverPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    haptic.success();
  }, [haptic]);

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

        if (coverFile) {
          console.log('Cover file selected, will be uploaded in future implementation');
        }

        haptic.success();
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
    [formData, coverFile, validateForm, navigate, haptic]
  );

  return (
    <WorkspaceLayout currentPage="galleries" pageTitle="Create Gallery">
      <div
        className={cn(
          'min-h-screen relative',
          'bg-neutral-50 dark:bg-neutral-900'
        )}
      >
        {/* Animated Background */}
        <MorphingBlob />
        <ParticleEffect />

        {/* Page Header */}
        <header
          className={cn(
            'bg-white/80 dark:bg-neutral-900/80',
            'backdrop-blur-xl',
            'border-b border-neutral-200/80 dark:border-white/10',
            'shadow-sm'
          )}
        >
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4">
          <div
            className={cn(
              'flex items-center gap-4',
              !prefersReducedMotion && 'animate-fade-in-up'
            )}
          >
            <button
              onClick={() => {
                haptic.light();
                navigate('/galleries');
              }}
              className={cn(
                'p-3 rounded-2xl min-w-[48px] min-h-[48px]',
                'text-neutral-600 hover:text-neutral-900',
                'dark:text-neutral-400 dark:hover:text-white',
                'bg-white/50 dark:bg-white/5',
                'border border-neutral-200/80 dark:border-white/10',
                'hover:bg-white dark:hover:bg-white/10',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                !prefersReducedMotion && 'transition-all duration-200',
                'flex items-center justify-center'
              )}
              aria-label="Back to galleries"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-neutral-800 dark:text-white flex items-center gap-2">
                Create Gallery
                <SparkleIcon className="w-6 h-6 text-amber-400" />
              </h1>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                Showcase your photography ✨
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-2xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info Section */}
          <SectionCard
            icon={<GalleryIcon className="w-6 h-6 text-white" />}
            emoji="📸"
            title="Basic Information"
            subtitle="Essential details for your gallery"
            delay={0}
          >
            <AppInput
              label="Gallery Title"
              placeholder="e.g., Smith Wedding 2024"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              error={errors.title}
              required
              autoFocus
              className="min-h-[48px]"
            />

            <AppInput
              label="Client Name"
              placeholder="e.g., John & Jane Smith"
              value={formData.client_name}
              onChange={(e) => handleChange('client_name', e.target.value)}
              error={errors.client_name}
              className="min-h-[48px]"
            />

            <AppInput
              label="Shoot Date"
              type="date"
              value={formData.shoot_date}
              onChange={(e) => handleChange('shoot_date', e.target.value)}
              error={errors.shoot_date}
              leftIcon={<CalendarIcon className="w-5 h-5 text-neutral-400" />}
              className="min-h-[48px]"
            />

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Description 📝
              </label>
              <textarea
                placeholder="Optional notes about this gallery..."
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                rows={3}
                className={cn(
                  'w-full px-4 py-3 rounded-2xl',
                  'bg-white dark:bg-white/5',
                  'border border-neutral-200/80 dark:border-white/10',
                  'text-neutral-800 dark:text-white',
                  'placeholder:text-neutral-400 dark:placeholder:text-neutral-500',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/30 focus-visible:border-primary-500',
                  !prefersReducedMotion && 'transition-all',
                  'resize-none'
                )}
              />
            </div>

            <CoverImageUpload
              coverPreview={coverPreview}
              onFileSelect={handleCoverSelect}
              onRemove={handleCoverRemove}
            />
          </SectionCard>

          {/* Advanced Settings Toggle */}
          <button
            type="button"
            onClick={() => {
              setShowAdvanced(!showAdvanced);
              haptic.light();
            }}
            className={cn(
              'w-full flex items-center justify-between px-5 py-4',
              'rounded-2xl min-h-[56px]',
              'bg-white/80 dark:bg-white/[0.08]',
              'border border-neutral-200/80 dark:border-white/10',
              'backdrop-blur-xl',
              'text-neutral-700 dark:text-neutral-300',
              'hover:bg-white dark:hover:bg-white/10',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
              !prefersReducedMotion && 'transition-all duration-200',
              !prefersReducedMotion && 'animate-fade-in-up'
            )}
            style={{ animationDelay: prefersReducedMotion ? '0ms' : '100ms' }}
          >
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  'w-10 h-10 rounded-xl',
                  'bg-gradient-to-br from-neutral-500 to-neutral-600',
                  'flex items-center justify-center'
                )}
              >
                <SettingsIcon className="w-5 h-5 text-white" />
              </div>
              <span className="font-medium">Advanced Settings ⚙️</span>
            </div>
            <ChevronDownIcon
              className={cn(
                'w-5 h-5',
                !prefersReducedMotion && 'transition-transform duration-200',
                showAdvanced && 'rotate-180'
              )}
            />
          </button>

          {/* Advanced Settings Section */}
          <AnimatePresence>
            {showAdvanced && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: prefersReducedMotion ? 0 : 0.3 }}
              >
                <SectionCard
                  icon={<SettingsIcon className="w-6 h-6 text-white" />}
                  emoji="⚙️"
                  title="Gallery Settings"
                  subtitle="Customize how clients interact"
                  delay={0}
                >
                  {/* Download Policy */}
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
                      Download Policy 📥
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {downloadPolicies.map((policy) => (
                        <OptionCard
                          key={policy.value}
                          label={policy.label}
                          description={policy.description}
                          emoji={policy.emoji}
                          isSelected={formData.download_policy === policy.value}
                          onClick={() => handleChange('download_policy', policy.value)}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Layout Style */}
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
                      Layout Style 🎨
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {layoutStyles.map((style) => (
                        <OptionCard
                          key={style.value}
                          label={style.label}
                          description={style.description}
                          emoji={style.emoji}
                          isSelected={formData.layout_style === style.value}
                          onClick={() => handleChange('layout_style', style.value)}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Password Protection */}
                  <AppInput
                    label="Gallery Password 🔒"
                    type="password"
                    placeholder="Optional - leave empty for no password"
                    value={formData.password}
                    onChange={(e) => handleChange('password', e.target.value)}
                    helperText="Clients will need this password to access the gallery"
                    className="min-h-[48px]"
                  />

                  {/* Email Registration Toggle */}
                  <ToggleSwitch
                    label="Require Email Registration"
                    description="Collect client emails before they can view"
                    emoji="📧"
                    isOn={formData.email_registration_required}
                    onToggle={() => handleChange('email_registration_required', !formData.email_registration_required)}
                  />
                </SectionCard>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Submit Buttons */}
          <div
            className={cn(
              'flex flex-col sm:flex-row gap-3 pt-2',
              !prefersReducedMotion && 'animate-fade-in-up'
            )}
            style={{ animationDelay: prefersReducedMotion ? '0ms' : '200ms' }}
          >
            <AppButton
              type="button"
              variant="outline"
              size="lg"
              onClick={() => {
                haptic.light();
                navigate('/galleries');
              }}
              className="sm:flex-1 min-h-[52px]"
            >
              Cancel
            </AppButton>
            <AppButton
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              glowOnHover
              className="sm:flex-1 min-h-[52px]"
            >
              {isMobile ? 'Create 📸' : 'Create Gallery 📸'}
            </AppButton>
          </div>
        </form>
        </main>

        {/* Safe area padding */}
        <div
          className="h-8"
          style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
        />
      </div>
    </WorkspaceLayout>
  );
}

export default GalleryCreatePage;
