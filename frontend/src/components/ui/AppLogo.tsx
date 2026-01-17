import { useTheme } from '../../hooks/useTheme';

interface AppLogoProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * AppLogo - Theme-aware logo component
 *
 * Automatically switches between light and dark mode logos based on the current theme.
 * Uses the useTheme hook to detect the active theme.
 *
 * @example
 * ```tsx
 * <AppLogo size="md" />
 * <AppLogo size="lg" className="mx-auto" />
 * ```
 */
export function AppLogo({ size = 'md', className = '' }: AppLogoProps) {
  const { resolvedTheme } = useTheme();

  const sizeMap = {
    sm: 32,
    md: 48,
    lg: 64
  };

  const logoSrc = resolvedTheme === 'dark'
    ? '/logo-dark-192x192.png'
    : '/logo-light-192x192.png';

  const dimensions = sizeMap[size];

  return (
    <img
      src={logoSrc}
      alt="RawDrive Logo"
      width={dimensions}
      height={dimensions}
      className={className}
    />
  );
}
