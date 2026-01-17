/**
 * WatermarkPreview Component
 * Shows a live preview of the watermark applied to a sample image
 *
 * Subtask-4-2: Create WatermarkPreview component showing live preview
 */

import { useEffect, useRef, useState } from 'react';
import { AppCard } from '../ui/AppCard';
import { cn } from '../../lib/utils';
import type { WatermarkConfig } from './WatermarkEditor';

// ============================================
// Icons
// ============================================

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn('animate-spin', className)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

function AlertCircleIcon({ className }: { className?: string }) {
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
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
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

// ============================================
// Types
// ============================================

export interface WatermarkPreviewProps {
  /** Watermark configuration to preview */
  config: WatermarkConfig;
  /** Sample image URL to use for preview */
  sampleImageUrl?: string;
  /** Additional class names */
  className?: string;
}

// ============================================
// Helper Functions
// ============================================

/**
 * Calculate position coordinates based on position type
 */
function calculatePosition(
  position: string,
  canvasWidth: number,
  canvasHeight: number,
  elementWidth: number,
  elementHeight: number,
  padding = 20
): { x: number; y: number } {
  switch (position) {
    case 'center':
      return {
        x: (canvasWidth - elementWidth) / 2,
        y: (canvasHeight - elementHeight) / 2,
      };
    case 'top_left':
      return { x: padding, y: padding };
    case 'top_right':
      return { x: canvasWidth - elementWidth - padding, y: padding };
    case 'bottom_left':
      return { x: padding, y: canvasHeight - elementHeight - padding };
    case 'bottom_right':
      return {
        x: canvasWidth - elementWidth - padding,
        y: canvasHeight - elementHeight - padding,
      };
    default:
      return { x: padding, y: padding };
  }
}

/**
 * Draw text watermark on canvas
 */
function drawTextWatermark(
  ctx: CanvasRenderingContext2D,
  config: WatermarkConfig,
  canvasWidth: number,
  canvasHeight: number
) {
  if (!config.text_config) return;

  const { text, font_size, font_family, color, opacity, rotation } = config.text_config;

  ctx.save();

  // Set font and measure text
  ctx.font = `${font_size}px ${font_family}`;
  const metrics = ctx.measureText(text);
  const textWidth = metrics.width;
  const textHeight = font_size;

  if (config.position === 'tiled') {
    // Tiled watermark
    const spacing = Math.max(textWidth, textHeight) * 2;
    ctx.globalAlpha = opacity;
    ctx.fillStyle = color;

    for (let y = 0; y < canvasHeight + spacing; y += spacing) {
      for (let x = 0; x < canvasWidth + spacing; x += spacing) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate((rotation * Math.PI) / 180);
        ctx.fillText(text, 0, 0);
        ctx.restore();
      }
    }
  } else {
    // Single position watermark
    const pos = calculatePosition(
      config.position,
      canvasWidth,
      canvasHeight,
      textWidth,
      textHeight
    );

    ctx.globalAlpha = opacity;
    ctx.fillStyle = color;
    ctx.translate(pos.x + textWidth / 2, pos.y + textHeight / 2);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.fillText(text, -textWidth / 2, textHeight / 4);
  }

  ctx.restore();
}

/**
 * Draw image watermark on canvas
 */
async function drawImageWatermark(
  ctx: CanvasRenderingContext2D,
  config: WatermarkConfig,
  canvasWidth: number,
  canvasHeight: number
): Promise<void> {
  if (!config.image_config?.image_url) return;

  const { image_url, scale, opacity } = config.image_config;

  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      ctx.save();

      const scaledWidth = img.width * scale;
      const scaledHeight = img.height * scale;

      if (config.position === 'tiled') {
        // Tiled watermark
        const spacing = Math.max(scaledWidth, scaledHeight) * 1.5;
        ctx.globalAlpha = opacity;

        for (let y = 0; y < canvasHeight + spacing; y += spacing) {
          for (let x = 0; x < canvasWidth + spacing; x += spacing) {
            ctx.drawImage(img, x, y, scaledWidth, scaledHeight);
          }
        }
      } else {
        // Single position watermark
        const pos = calculatePosition(
          config.position,
          canvasWidth,
          canvasHeight,
          scaledWidth,
          scaledHeight
        );

        ctx.globalAlpha = opacity;
        ctx.drawImage(img, pos.x, pos.y, scaledWidth, scaledHeight);
      }

      ctx.restore();
      resolve();
    };

    img.onerror = () => {
      reject(new Error('Failed to load watermark image'));
    };

    img.src = image_url;
  });
}

// ============================================
// Component
// ============================================

export function WatermarkPreview({
  config,
  sampleImageUrl = '/images/testimonials/ananya.png',
  className,
}: WatermarkPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsLoading(true);
    setError(null);

    // Load the sample image
    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = async () => {
      try {
        // Set canvas size to match image
        canvas.width = img.width;
        canvas.height = img.height;

        // Draw the base image
        ctx.drawImage(img, 0, 0);

        // Apply watermark based on type
        if (config.type === 'text') {
          drawTextWatermark(ctx, config, canvas.width, canvas.height);
        } else if (config.type === 'image' && config.image_config?.image_url) {
          try {
            await drawImageWatermark(ctx, config, canvas.width, canvas.height);
          } catch (err) {
            setError('Failed to load watermark image');
          }
        }

        setIsLoading(false);
      } catch (err) {
        setError('Failed to apply watermark');
        setIsLoading(false);
      }
    };

    img.onerror = () => {
      setError('Failed to load sample image');
      setIsLoading(false);
    };

    img.src = sampleImageUrl;
  }, [config, sampleImageUrl]);

  return (
    <AppCard variant="glass" padding="lg" className={cn('w-full', className)}>
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-neutral-900 dark:text-white mb-1">
          Preview
        </h3>
        <p className="text-sm text-neutral-500 dark:text-white/60">
          See how your watermark will look
        </p>
      </div>

      {/* Preview Canvas */}
      <div className="relative rounded-xl overflow-hidden bg-neutral-100 dark:bg-white/5 border border-neutral-200 dark:border-white/10">
        {/* Loading State */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-black/40 backdrop-blur-sm z-10">
            <div className="text-center">
              <LoaderIcon className="w-8 h-8 text-primary-500 mx-auto mb-2" />
              <p className="text-sm text-neutral-600 dark:text-white/70">
                Generating preview...
              </p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-black/40 backdrop-blur-sm z-10">
            <div className="text-center px-4">
              <AlertCircleIcon className="w-8 h-8 text-red-500 mx-auto mb-2" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        )}

        {/* Canvas */}
        <canvas
          ref={canvasRef}
          className="w-full h-auto max-h-[500px] object-contain"
          style={{ display: isLoading ? 'none' : 'block' }}
        />

        {/* Empty State */}
        {!isLoading && !error && !canvasRef.current && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <ImageIcon className="w-12 h-12 text-neutral-400 dark:text-white/30 mx-auto mb-3" />
              <p className="text-sm text-neutral-500 dark:text-white/50">
                No preview available
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Preview Info */}
      <div className="mt-4 p-3 rounded-lg bg-neutral-50 dark:bg-white/5 border border-neutral-200 dark:border-white/10">
        <div className="flex items-start gap-2">
          <div className="flex-shrink-0 mt-0.5">
            <svg
              className="w-4 h-4 text-primary-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
          </div>
          <div className="flex-1">
            <p className="text-xs text-neutral-600 dark:text-white/60 leading-relaxed">
              This is a preview only. The actual watermark will be applied to your photos when
              you click &quot;Apply to All Photos&quot;.
            </p>
          </div>
        </div>
      </div>
    </AppCard>
  );
}

export default WatermarkPreview;
