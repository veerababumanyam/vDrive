/**
 * Google OAuth Utilities
 *
 * Helper functions for handling Google OAuth authentication flow.
 * Separated from component file to maintain React Fast Refresh compatibility.
 */

import { onboardingApi } from './onboarding-api';

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
