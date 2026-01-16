/**
 * ShareModal Component
 *
 * Premium modal for sharing galleries via magic links.
 * Features QR code generation, link copying, and share options.
 *
 * Mobile-first with glass morphism design and haptic feedback.
 */

import {
  forwardRef,
  useState,
  useCallback,
  useEffect,
  type HTMLAttributes,
} from 'react';
import { cn } from '../../lib/utils';
import { useHaptic } from '../../hooks';
import {
  createShareLink,
  listShareLinks,
  revokeShareLink,
  generateQRCode,
} from '../../services/gallery-api';
import type { ShareLink, QRCodeResponse } from '../../types/gallery';

export interface ShareModalProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onClose'> {
  /** Is modal open */
  isOpen: boolean;
  /** Close handler */
  onClose: () => void;
  /** Gallery ID to share */
  galleryId: string;
  /** Gallery title for display */
  galleryTitle: string;
}

/**
 * Icons
 */
function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

function QRCodeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 11h8V3H3v8zm2-6h4v4H5V5zm8-2v8h8V3h-8zm6 6h-4V5h4v4zM3 21h8v-8H3v8zm2-6h4v4H5v-4zm13 2h-2v2h2v-2zm0-6h2v2h-2v-2zm2 4h-2v2h2v-2zm-4 4h2v2h-2v-2zm2-2h-2v2h2v-2zm-2 4h2v2h-2v-2z" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14zM10 11v6M14 11v6" />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
    </svg>
  );
}

/**
 * Format date for display
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * ShareModal - Premium sharing modal with QR codes
 */
export const ShareModal = forwardRef<HTMLDivElement, ShareModalProps>(
  ({ isOpen, onClose, galleryId, galleryTitle, className, ...props }, ref) => {
    const haptic = useHaptic();
    const [shareLinks, setShareLinks] = useState<ShareLink[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [copiedLinkId, setCopiedLinkId] = useState<string | null>(null);
    const [activeQR, setActiveQR] = useState<{
      linkId: string;
      qrData: QRCodeResponse;
    } | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Fetch existing share links
    useEffect(() => {
      if (!isOpen || !galleryId) return;

      const fetchLinks = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const links = await listShareLinks(galleryId);
          setShareLinks(links.filter((l) => l.status === 'active'));
        } catch (err) {
          setError('Failed to load share links');
          console.error('Failed to fetch share links:', err);
        } finally {
          setIsLoading(false);
        }
      };

      fetchLinks();
    }, [isOpen, galleryId]);

    // Create new share link
    const handleCreateLink = useCallback(async () => {
      setIsCreating(true);
      setError(null);
      try {
        const newLink = await createShareLink(galleryId, {
          label: `Share Link ${shareLinks.length + 1}`,
          allowed_actions: ['view', 'favorite', 'select'],
        });
        setShareLinks((prev) => [newLink, ...prev]);
        haptic.success();
      } catch (err) {
        setError('Failed to create share link');
        haptic.error();
        console.error('Failed to create share link:', err);
      } finally {
        setIsCreating(false);
      }
    }, [galleryId, shareLinks.length, haptic]);

    // Copy link to clipboard
    const handleCopyLink = useCallback(
      async (link: ShareLink) => {
        const url = `${window.location.origin}/share/${link.link_id}`;
        try {
          await navigator.clipboard.writeText(url);
          setCopiedLinkId(link.link_id);
          haptic.success();
          setTimeout(() => setCopiedLinkId(null), 2000);
        } catch {
          // Fallback for older browsers
          const textArea = document.createElement('textarea');
          textArea.value = url;
          textArea.style.position = 'fixed';
          textArea.style.opacity = '0';
          document.body.appendChild(textArea);
          textArea.select();
          try {
            document.execCommand('copy');
            setCopiedLinkId(link.link_id);
            haptic.success();
            setTimeout(() => setCopiedLinkId(null), 2000);
          } catch {
            haptic.error();
          }
          document.body.removeChild(textArea);
        }
      },
      [haptic]
    );

    // Generate and show QR code
    const handleShowQR = useCallback(
      async (link: ShareLink) => {
        try {
          const qrData = await generateQRCode(link.link_id, {
            size: 300,
          });
          setActiveQR({ linkId: link.link_id, qrData });
          haptic.medium();
        } catch (err) {
          setError('Failed to generate QR code');
          haptic.error();
          console.error('Failed to generate QR code:', err);
        }
      },
      [haptic]
    );

    // Download QR code
    const handleDownloadQR = useCallback(() => {
      if (!activeQR) return;

      const link = document.createElement('a');
      link.href = activeQR.qrData.qr_code_url;
      link.download = `${galleryTitle.replace(/\s+/g, '-')}-qr-code.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      haptic.success();
    }, [activeQR, galleryTitle, haptic]);

    // Revoke share link
    const handleRevokeLink = useCallback(
      async (linkId: string) => {
        try {
          await revokeShareLink(galleryId, linkId);
          setShareLinks((prev) => prev.filter((l) => l.link_id !== linkId));
          haptic.medium();
        } catch (err) {
          setError('Failed to revoke link');
          haptic.error();
          console.error('Failed to revoke share link:', err);
        }
      },
      [galleryId, haptic]
    );

    if (!isOpen) return null;

    return (
      <div
        ref={ref}
        className={cn(
          'fixed inset-0 z-50',
          'flex items-end sm:items-center justify-center',
          'overlay-frosted',
          'p-0 sm:p-4',
          className
        )}
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
        {...props}
      >
        <div
          className={cn(
            'w-full sm:max-w-lg',
            'max-h-[90vh] sm:max-h-[80vh]',
            'bg-white dark:bg-neutral-900',
            'sm:rounded-2xl rounded-t-3xl',
            'shadow-2xl dark:shadow-black/50',
            'overflow-hidden',
            'animate-slide-up sm:animate-fade-in-scale',
            'flex flex-col'
          )}
          style={{
            paddingBottom: 'env(safe-area-inset-bottom, 0px)',
          }}
        >
          {/* Header */}
          <header
            className={cn(
              'flex items-center justify-between',
              'px-5 py-4 sm:px-6',
              'border-b border-neutral-200 dark:border-white/10'
            )}
          >
            {/* Drag handle (mobile) */}
            <div className="absolute top-2 left-1/2 -translate-x-1/2 w-10 h-1 rounded-full bg-neutral-300 dark:bg-white/20 sm:hidden" />

            <div className="flex items-center gap-3">
              <div
                className={cn(
                  'w-10 h-10 rounded-full',
                  'bg-primary-100 dark:bg-primary-500/20',
                  'flex items-center justify-center'
                )}
              >
                <LinkIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  Share Gallery
                </h2>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 truncate max-w-[200px]">
                  {galleryTitle}
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className={cn(
                'p-2 rounded-full',
                'text-neutral-400 hover:text-neutral-600',
                'dark:hover:text-white',
                'hover:bg-neutral-100 dark:hover:bg-white/10',
                'transition-colors'
              )}
              aria-label="Close"
            >
              <CloseIcon className="w-5 h-5" />
            </button>
          </header>

          {/* QR Code View */}
          {activeQR && (
            <div className="flex-1 flex flex-col items-center justify-center p-6 animate-fade-in">
              <div
                className={cn(
                  'p-4 bg-white rounded-2xl mb-4',
                  'shadow-lg'
                )}
              >
                <img
                  src={activeQR.qrData.qr_code_url}
                  alt="QR Code"
                  className="w-48 h-48 sm:w-64 sm:h-64"
                />
              </div>

              <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-4 text-center">
                Scan this QR code to access the gallery
              </p>

              <div className="flex gap-3">
                <button
                  onClick={handleDownloadQR}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2.5 rounded-xl',
                    'bg-primary-500 text-white',
                    'hover:bg-primary-600',
                    'transition-colors'
                  )}
                >
                  <DownloadIcon className="w-4 h-4" />
                  <span>Download</span>
                </button>
                <button
                  onClick={() => setActiveQR(null)}
                  className={cn(
                    'px-4 py-2.5 rounded-xl',
                    'bg-neutral-100 dark:bg-white/10',
                    'text-neutral-700 dark:text-white',
                    'hover:bg-neutral-200 dark:hover:bg-white/20',
                    'transition-colors'
                  )}
                >
                  Back
                </button>
              </div>
            </div>
          )}

          {/* Links List View */}
          {!activeQR && (
            <>
              {/* Content */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6">
                {/* Error message */}
                {error && (
                  <div
                    className={cn(
                      'mb-4 p-3 rounded-xl',
                      'bg-error-50 dark:bg-error-500/10',
                      'text-error-700 dark:text-error-400',
                      'text-sm'
                    )}
                  >
                    {error}
                  </div>
                )}

                {/* Loading */}
                {isLoading && (
                  <div className="flex items-center justify-center py-12">
                    <div className="w-8 h-8 rounded-full border-2 border-primary-500/30 border-t-primary-500 animate-spin" />
                  </div>
                )}

                {/* Empty state */}
                {!isLoading && shareLinks.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div
                      className={cn(
                        'w-16 h-16 rounded-full mb-4',
                        'bg-neutral-100 dark:bg-white/5',
                        'flex items-center justify-center',
                        'animate-float'
                      )}
                    >
                      <LinkIcon className="w-8 h-8 text-neutral-400" />
                    </div>
                    <h3 className="text-lg font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                      No share links yet
                    </h3>
                    <p className="text-sm text-neutral-500 dark:text-neutral-400 max-w-xs">
                      Create a link to share this gallery with clients
                    </p>
                  </div>
                )}

                {/* Links list */}
                {!isLoading && shareLinks.length > 0 && (
                  <div className="space-y-3">
                    {shareLinks.map((link) => (
                      <div
                        key={link.link_id}
                        className={cn(
                          'p-4 rounded-xl',
                          'bg-neutral-50 dark:bg-white/5',
                          'border border-neutral-200 dark:border-white/10',
                          'group'
                        )}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0 mr-3">
                            <p className="font-medium text-neutral-900 dark:text-white truncate">
                              {link.label || 'Share Link'}
                            </p>
                            <p className="text-sm text-neutral-500 dark:text-neutral-400">
                              Created {formatDate(link.created_at)}
                              {link.expires_at && ` • Expires ${formatDate(link.expires_at)}`}
                            </p>
                          </div>

                          {/* Delete button */}
                          <button
                            onClick={() => handleRevokeLink(link.link_id)}
                            className={cn(
                              'p-2 rounded-lg',
                              'text-neutral-400 hover:text-error-500',
                              'hover:bg-error-50 dark:hover:bg-error-500/10',
                              'opacity-0 group-hover:opacity-100',
                              'transition-all'
                            )}
                            aria-label="Revoke link"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleCopyLink(link)}
                            className={cn(
                              'flex-1 flex items-center justify-center gap-2',
                              'px-3 py-2.5 rounded-xl',
                              copiedLinkId === link.link_id
                                ? 'bg-success-500 text-white'
                                : 'bg-white dark:bg-white/10 text-neutral-700 dark:text-white',
                              'border border-neutral-200 dark:border-white/10',
                              'hover:border-neutral-300 dark:hover:border-white/20',
                              'transition-all text-sm font-medium'
                            )}
                          >
                            {copiedLinkId === link.link_id ? (
                              <>
                                <CheckIcon className="w-4 h-4" />
                                <span>Copied!</span>
                              </>
                            ) : (
                              <>
                                <CopyIcon className="w-4 h-4" />
                                <span>Copy Link</span>
                              </>
                            )}
                          </button>

                          <button
                            onClick={() => handleShowQR(link)}
                            className={cn(
                              'flex items-center justify-center gap-2',
                              'px-3 py-2.5 rounded-xl',
                              'bg-white dark:bg-white/10',
                              'text-neutral-700 dark:text-white',
                              'border border-neutral-200 dark:border-white/10',
                              'hover:border-neutral-300 dark:hover:border-white/20',
                              'transition-colors text-sm font-medium'
                            )}
                          >
                            <QRCodeIcon className="w-4 h-4" />
                            <span className="hidden sm:inline">QR Code</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer with create button */}
              <footer
                className={cn(
                  'px-4 py-4 sm:px-6',
                  'border-t border-neutral-200 dark:border-white/10',
                  'bg-neutral-50 dark:bg-white/5'
                )}
              >
                <button
                  onClick={handleCreateLink}
                  disabled={isCreating}
                  className={cn(
                    'w-full flex items-center justify-center gap-2',
                    'px-4 py-3 rounded-xl',
                    'bg-primary-500 text-white',
                    'hover:bg-primary-600',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                    'transition-colors font-medium'
                  )}
                >
                  {isCreating ? (
                    <div className="w-5 h-5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  ) : (
                    <>
                      <PlusIcon className="w-5 h-5" />
                      <span>Create New Link</span>
                    </>
                  )}
                </button>
              </footer>
            </>
          )}
        </div>
      </div>
    );
  }
);

ShareModal.displayName = 'ShareModal';

export default ShareModal;
