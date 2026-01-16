/**
 * CredentialsForm Component
 * Form to collect platform credentials for migration
 *
 * Subtask-5-4: Create migration wizard UI component
 */

import { useState } from 'react';
import { cn } from '../../lib/utils';
import { AppInput } from '../ui/AppInput';
import type { MigrationPlatform, MigrationCredentials } from '../../services/migration-api';
import { getPlatformDisplayName } from '../../services/migration-api';

// ============================================
// Icons
// ============================================

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

function EyeIcon({ className }: { className?: string }) {
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
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon({ className }: { className?: string }) {
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
      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
      <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
      <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
      <line x1="2" x2="22" y1="2" y2="22" />
    </svg>
  );
}

// ============================================
// Types
// ============================================

export interface CredentialsFormProps {
  /** Selected platform */
  platform: MigrationPlatform;
  /** Current credentials */
  credentials: Partial<MigrationCredentials>;
  /** Callback when credentials change */
  onCredentialsChange: (credentials: Partial<MigrationCredentials>) => void;
  /** Validation errors */
  errors?: Record<string, string>;
  /** Additional class names */
  className?: string;
}

// ============================================
// Component
// ============================================

export function CredentialsForm({
  platform,
  credentials,
  onCredentialsChange,
  errors = {},
  className,
}: CredentialsFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [showApiSecret, setShowApiSecret] = useState(false);

  const platformName = getPlatformDisplayName(platform);

  const handleChange = (field: keyof MigrationCredentials, value: string) => {
    onCredentialsChange({
      ...credentials,
      [field]: value,
    });
  };

  // Platform-specific field configurations
  const getFieldsForPlatform = () => {
    switch (platform) {
      case 'pixieset':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                API Key <span className="text-red-400">*</span>
              </label>
              <AppInput
                type="text"
                value={credentials.api_key || ''}
                onChange={(e) => handleChange('api_key', e.target.value)}
                placeholder="Enter your Pixieset API key"
                error={errors.api_key}
              />
            </div>
          </>
        );

      case 'pictime':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Username <span className="text-red-400">*</span>
              </label>
              <AppInput
                type="text"
                value={credentials.username || ''}
                onChange={(e) => handleChange('username', e.target.value)}
                placeholder="Enter your Pic-Time username"
                error={errors.username}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Password <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <AppInput
                  type={showPassword ? 'text' : 'password'}
                  value={credentials.password || ''}
                  onChange={(e) => handleChange('password', e.target.value)}
                  placeholder="Enter your Pic-Time password"
                  error={errors.password}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                >
                  {showPassword ? (
                    <EyeOffIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </>
        );

      case 'shootproof':
      case 'zenfolio':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                API Key <span className="text-red-400">*</span>
              </label>
              <AppInput
                type="text"
                value={credentials.api_key || ''}
                onChange={(e) => handleChange('api_key', e.target.value)}
                placeholder={`Enter your ${platformName} API key`}
                error={errors.api_key}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                API Secret <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <AppInput
                  type={showApiSecret ? 'text' : 'password'}
                  value={credentials.api_secret || ''}
                  onChange={(e) => handleChange('api_secret', e.target.value)}
                  placeholder={`Enter your ${platformName} API secret`}
                  error={errors.api_secret}
                />
                <button
                  type="button"
                  onClick={() => setShowApiSecret(!showApiSecret)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                >
                  {showApiSecret ? (
                    <EyeOffIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </>
        );

      case 'smugmug':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Access Token <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <AppInput
                  type={showApiSecret ? 'text' : 'password'}
                  value={credentials.access_token || ''}
                  onChange={(e) => handleChange('access_token', e.target.value)}
                  placeholder="Enter your SmugMug access token"
                  error={errors.access_token}
                />
                <button
                  type="button"
                  onClick={() => setShowApiSecret(!showApiSecret)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                >
                  {showApiSecret ? (
                    <EyeOffIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  // Platform-specific help text
  const getHelpTextForPlatform = () => {
    switch (platform) {
      case 'pixieset':
        return (
          <>
            <p className="font-medium text-white mb-2">How to find your Pixieset API key:</p>
            <ol className="space-y-1 text-xs list-decimal list-inside">
              <li>Log in to your Pixieset account</li>
              <li>Go to Settings → API Access</li>
              <li>Generate a new API key or copy your existing one</li>
            </ol>
          </>
        );

      case 'pictime':
        return (
          <>
            <p className="font-medium text-white mb-2">Authentication:</p>
            <p className="text-xs">
              Use your Pic-Time account credentials. Your password is securely transmitted and never stored.
            </p>
          </>
        );

      case 'shootproof':
        return (
          <>
            <p className="font-medium text-white mb-2">How to get ShootProof API credentials:</p>
            <ol className="space-y-1 text-xs list-decimal list-inside">
              <li>Log in to your ShootProof account</li>
              <li>Go to Account → API Settings</li>
              <li>Create new API credentials</li>
              <li>Copy both the API Key and API Secret</li>
            </ol>
          </>
        );

      case 'zenfolio':
        return (
          <>
            <p className="font-medium text-white mb-2">How to get Zenfolio API credentials:</p>
            <ol className="space-y-1 text-xs list-decimal list-inside">
              <li>Log in to your Zenfolio account</li>
              <li>Go to Tools → API Access</li>
              <li>Request API access if you haven't already</li>
              <li>Copy your API Key and Secret</li>
            </ol>
          </>
        );

      case 'smugmug':
        return (
          <>
            <p className="font-medium text-white mb-2">How to get SmugMug access token:</p>
            <ol className="space-y-1 text-xs list-decimal list-inside">
              <li>Log in to your SmugMug account</li>
              <li>Go to Account Settings → API Keys</li>
              <li>Create a new application or use existing one</li>
              <li>Generate an access token with read permissions</li>
            </ol>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          Enter your {platformName} credentials
        </h3>
        <div className="space-y-4">
          {getFieldsForPlatform()}
        </div>
      </div>

      {/* Help section */}
      <div className="p-4 rounded-xl bg-primary-500/10 border border-primary-500/20">
        <div className="flex gap-3">
          <InfoIcon className="w-5 h-5 text-primary-400 shrink-0 mt-0.5" />
          <div className="text-sm text-white/70">
            {getHelpTextForPlatform()}
          </div>
        </div>
      </div>

      {/* Security note */}
      <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20">
        <p className="text-xs text-white/70">
          <span className="font-medium text-green-400">🔒 Secure:</span> Your credentials are
          encrypted in transit and used only for this migration. They are never stored permanently.
        </p>
      </div>
    </div>
  );
}

export default CredentialsForm;
