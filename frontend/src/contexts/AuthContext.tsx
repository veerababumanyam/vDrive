/**
 * Authentication Context
 * Manages global authentication state and provides auth methods
 *
 * T014: Create AuthContext.tsx with token state management
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, type LoginRequest, type LoginResponse, handleAuthError } from '../services/authService';

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

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const initializeAuth = () => {
      try {
        const storedToken = localStorage.getItem('access_token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
          setAccessToken(storedToken);
          setUser(JSON.parse(storedUser));
        }
      } catch (error) {
        console.error('Failed to initialize auth state:', error);
        // Clear corrupted data
        localStorage.removeItem('access_token');
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

      // Store token in localStorage (access token) and memory (user)
      // Refresh token is stored in HttpOnly cookie by backend
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      setAccessToken(response.access_token);
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
      // Clear local state
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setAccessToken(null);
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
      // Clear local state
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setAccessToken(null);
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

      // Update access token
      localStorage.setItem('access_token', response.access_token);
      setAccessToken(response.access_token);
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, clear auth state and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setAccessToken(null);
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
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
