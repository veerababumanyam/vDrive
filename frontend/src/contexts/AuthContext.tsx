/**
 * Authentication Context
 * Manages global authentication state and provides auth methods
 *
 * T014: Create AuthContext.tsx with token state management
 */

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { authApi, type LoginRequest, type LoginResponse, handleAuthError, setTokenInMemory } from '../services/authService';

/**
 * User type from API
 */
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
  email_verified: boolean;
}

/**
 * Auth context value type
 */
interface AuthContextValue {
  // State
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Methods
  login: (request: LoginRequest) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshToken: () => Promise<void>;
  setUser: (user: User | null) => void;
  setAccessToken: (token: string | null) => void;
}

/**
 * Create auth context with undefined default
 * This ensures we can detect if provider is missing
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Auth Provider Props
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Auth Provider Component
 * Wraps the app and provides authentication state/methods
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize auth state on mount
  // T041: Handle OAuth callback token extraction from URL fragment
  // SECURITY: Access tokens stored ONLY in memory, never localStorage
  // Refresh tokens stored in HttpOnly cookies by backend
  useEffect(() => {
    const initializeAuth = () => {
      try {
        // Check for OAuth callback tokens in URL fragment (from backend redirect)
        const fragment = window.location.hash.substring(1);
        const params = new URLSearchParams(fragment);
        const oauthToken = params.get('access_token');
        const oauthUser = params.get('user');

        if (oauthToken && oauthUser) {
          // OAuth callback - store in MEMORY ONLY (not localStorage)
          const userData = JSON.parse(decodeURIComponent(oauthUser));
          localStorage.setItem('user', JSON.stringify(userData)); // User data OK (not sensitive)
          setAccessToken(oauthToken); // React state
          setTokenInMemory(oauthToken); // Axios interceptor access
          setUser(userData);

          // Clean URL (remove fragment)
          window.history.replaceState(null, '', window.location.pathname);
        } else {
          // Normal initialization from storage
          const storedUser = localStorage.getItem('user');

          if (storedUser) {
            setUser(JSON.parse(storedUser));
            // Access token will be automatically refreshed if needed by interceptor
          }
        }
      } catch (error) {
        console.error('Failed to initialize auth state:', error);
        // Clear corrupted data
        localStorage.removeItem('user');
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  /**
   * Login method
   * Phase 3: Email/password signin
   * Phase 4: Will handle Google OAuth callback tokens
   */
  const login = async (request: LoginRequest): Promise<LoginResponse> => {
    try {
      const response = await authApi.login(request);

      // SECURITY: Store access token ONLY in memory (React state), never localStorage
      // Refresh token is automatically stored in HttpOnly cookie by backend
      // User data (non-sensitive) can be stored in localStorage for convenience
      localStorage.setItem('user', JSON.stringify(response.user));

      setAccessToken(response.access_token); // React state
      setTokenInMemory(response.access_token); // Axios interceptor access
      setUser(response.user);

      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error(handleAuthError(error));
    }
  };

  /**
   * Logout method (current device)
   * Phase 6: User Story 4 - Logout
   */
  const logout = async (): Promise<void> => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local cleanup even if API fails
    } finally {
      // Clear local state (access token in memory, user data in localStorage)
      localStorage.removeItem('user');
      setAccessToken(null); // Clear React state
      setTokenInMemory(null); // Clear axios interceptor token
      setUser(null);
    }
  };

  /**
   * Logout all devices
   * Phase 6: User Story 4 - Logout
   */
  const logoutAll = async (): Promise<void> => {
    try {
      await authApi.logoutAll();
    } catch (error) {
      console.error('Logout all devices failed:', error);
      // Continue with local cleanup even if API fails
    } finally {
      // Clear local state (access token in memory, user data in localStorage)
      localStorage.removeItem('user');
      setAccessToken(null); // Clear React state
      setTokenInMemory(null); // Clear axios interceptor token
      setUser(null);
    }
  };

  /**
   * Refresh access token
   * Phase 5: User Story 3 - Session Refresh
   * Called automatically by axios interceptor when token expires
   */
  const refreshToken = async (): Promise<void> => {
    try {
      const response = await authApi.refreshToken();

      // SECURITY: Update access token in memory only (never localStorage)
      setAccessToken(response.access_token); // React state
      setTokenInMemory(response.access_token); // Axios interceptor access
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, clear auth state and redirect to login
      localStorage.removeItem('user');
      setAccessToken(null); // Clear React state
      setTokenInMemory(null); // Clear axios interceptor token
      setUser(null);
      throw error;
    }
  };

  /**
   * Context value
   */
  const value: AuthContextValue = {
    user,
    accessToken,
    isAuthenticated: !!user && !!accessToken,
    isLoading,
    login,
    logout,
    logoutAll,
    refreshToken,
    setUser,
    setAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * useAuth hook
 * Access auth context from any component
 *
 * @throws Error if used outside AuthProvider
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
