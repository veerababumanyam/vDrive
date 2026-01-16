/**
 * useTheme Hook
 * Manages theme state with system preference detection
 *
 * T054: Create useTheme hook with system preference detection
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { isBrowser } from '../lib/utils';

// ============================================
// Types
// ============================================

export type Theme = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

export interface ThemeContextValue {
  /** Current theme setting (light, dark, or system) */
  theme: Theme;
  /** Resolved theme (light or dark) after system preference */
  resolvedTheme: ResolvedTheme;
  /** Update the theme */
  setTheme: (theme: Theme) => void;
  /** Toggle between light and dark */
  toggleTheme: () => void;
  /** Whether we're currently matching system preference */
  isSystem: boolean;
}

// ============================================
// Context
// ============================================

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = 'RawDrive-theme';

/**
 * Get system color scheme preference
 */
function getSystemTheme(): ResolvedTheme {
  if (!isBrowser) return 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

/**
 * Get stored theme from localStorage
 */
function getStoredTheme(): Theme {
  if (!isBrowser) return 'system';
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored;
  }
  return 'system';
}

/**
 * Resolve theme to light or dark
 */
function resolveTheme(theme: Theme): ResolvedTheme {
  if (theme === 'system') {
    return getSystemTheme();
  }
  return theme;
}

/**
 * Apply theme to document
 */
function applyTheme(resolvedTheme: ResolvedTheme): void {
  if (!isBrowser) return;

  const root = document.documentElement;

  // Remove both classes first
  root.classList.remove('light', 'dark');

  // Add the resolved theme class
  root.classList.add(resolvedTheme);

  // Set data attribute for CSS
  root.setAttribute('data-theme', resolvedTheme);

  // Update color-scheme for native elements
  root.style.colorScheme = resolvedTheme;
}

// ============================================
// Provider Component
// ============================================

export interface ThemeProviderProps {
  children: ReactNode;
  /** Default theme if no stored preference */
  defaultTheme?: Theme;
  /** Force a specific theme (overrides all) */
  forcedTheme?: ResolvedTheme;
}

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  forcedTheme,
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (forcedTheme) return forcedTheme;
    return getStoredTheme() || defaultTheme;
  });

  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() => {
    if (forcedTheme) return forcedTheme;
    return resolveTheme(theme);
  });

  // Set theme and persist to storage
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    if (isBrowser) {
      localStorage.setItem(STORAGE_KEY, newTheme);
    }
  }, []);

  // Toggle between light and dark
  const toggleTheme = useCallback(() => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  }, [resolvedTheme, setTheme]);

  // Update resolved theme when theme changes
  useEffect(() => {
    // Use requestAnimationFrame to avoid sync setState in effect
    const frame = requestAnimationFrame(() => {
      if (forcedTheme) {
        setResolvedTheme(forcedTheme);
        applyTheme(forcedTheme);
        return;
      }

      const resolved = resolveTheme(theme);
      setResolvedTheme(resolved);
      applyTheme(resolved);
    });

    return () => cancelAnimationFrame(frame);
  }, [theme, forcedTheme]);

  // Listen for system preference changes
  useEffect(() => {
    if (!isBrowser || theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = () => {
      const resolved = getSystemTheme();
      setResolvedTheme(resolved);
      applyTheme(resolved);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  // Apply theme on initial mount (handle SSR)
  useEffect(() => {
    applyTheme(resolvedTheme);
  }, [resolvedTheme]);

  const value: ThemeContextValue = {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
    isSystem: theme === 'system',
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

// ============================================
// Hook
// ============================================

/**
 * Use the theme context
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { theme, resolvedTheme, toggleTheme } = useTheme();
 *
 *   return (
 *     <button onClick={toggleTheme}>
 *       Current: {resolvedTheme}
 *     </button>
 *   );
 * }
 * ```
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}

// ============================================
// Utility Hook: Reduced Motion
// ============================================

/**
 * Check if user prefers reduced motion
 */
// eslint-disable-next-line react-refresh/only-export-components
export function usePrefersReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState(() => {
    if (!isBrowser) return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    if (!isBrowser) return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    // Use requestAnimationFrame to avoid sync setState in effect
    const frame = requestAnimationFrame(() =>
      setPrefersReduced(mediaQuery.matches)
    );

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReduced(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => {
      cancelAnimationFrame(frame);
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return prefersReduced;
}

// eslint-disable-next-line react-refresh/only-export-components
export default useTheme;
