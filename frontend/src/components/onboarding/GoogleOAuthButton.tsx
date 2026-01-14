/**
 * GoogleOAuthButton Component
 * Button to initiate Google OAuth authentication
 *
 * T068: Create GoogleOAuthButton component
 */

import { useState } from 'react';
import { onboardingApi } from '../../services/onboarding-api';
import { AppButton } from '../ui/AppButton';
import { cn } from '../../lib/utils';

// ============================================
// Google Icon
// ============================================

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

// ============================================
// Component
// ============================================

export interface GoogleOAuthButtonProps {
  /** Button text */
  text?: string;
  /** Full width button */
  fullWidth?: boolean;
  /** Additional class names */
  className?: string;
  /** Callback when OAuth starts */
  onStart?: () => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

/**
 * Google OAuth sign-in/sign-up button
 *
 * @example
 * ```tsx
 * <GoogleOAuthButton
 *   text="Sign up with Google"
 *   onError={(error) => console.error(error)}
 * />
 * ```
 */
export function GoogleOAuthButton({
  text = 'Continue with Google',
  fullWidth = false,
  className,
  onStart,
  onError,
}: GoogleOAuthButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    try {
      setIsLoading(true);
      onStart?.();

      // Get the authorization URL from the backend
      const { authorization_url, state } = await onboardingApi.getGoogleAuthUrl();

      // Store state for CSRF protection
      sessionStorage.setItem('oauth_state', state);

      // Redirect to Google
      window.location.href = authorization_url;
    } catch (error) {
      setIsLoading(false);
      const err = error instanceof Error ? error : new Error('OAuth failed');
      onError?.(err);
    }
  };

  return (
    <AppButton
      type="button"
      variant="outline"
      size="lg"
      fullWidth={fullWidth}
      isLoading={isLoading}
      onClick={handleClick}
      className={cn(
        // Override default outline styles for Google button
        'bg-white/5 hover:bg-white/10',
        'border-white/20 hover:border-white/30',
        className
      )}
      leftIcon={<GoogleIcon className="w-5 h-5" />}
    >
      {text}
    </AppButton>
  );
}

// ============================================
// OAuth Callback Handler
// ============================================

/**
 * Handle OAuth callback from Google
 * Call this on the callback page to exchange code for tokens
 */
export async function handleGoogleCallback(): Promise<{
  success: boolean;
  isNewUser?: boolean;
  error?: string;
}> {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    // Check for OAuth error
    if (error) {
      return {
        success: false,
        error: `OAuth error: ${error}`,
      };
    }

    // Validate required params
    if (!code || !state) {
      return {
        success: false,
        error: 'Missing authorization code or state',
      };
    }

    // Validate state for CSRF protection
    const storedState = sessionStorage.getItem('oauth_state');
    if (state !== storedState) {
      return {
        success: false,
        error: 'Invalid state parameter',
      };
    }

    // Clear stored state
    sessionStorage.removeItem('oauth_state');

    // Exchange code for tokens
    const response = await onboardingApi.handleGoogleCallback(code, state);

    return {
      success: true,
      isNewUser: response.is_new_user,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'OAuth callback failed';
    return {
      success: false,
      error: message,
    };
  }
}

export default GoogleOAuthButton;
