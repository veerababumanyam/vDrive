/**
 * ThemeToggle Component
 * Toggle button for switching between light, dark, and system themes
 *
 * T055: Create ThemeToggle component
 */

import { useState, useRef, useEffect } from 'react';
import { useTheme, type Theme } from '../../hooks/useTheme';
import { cn } from '../../lib/utils';

// ============================================
// Icons
// ============================================

function SunIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </svg>
  );
}

function MoonIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function MonitorIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
      <line x1="8" y1="21" x2="16" y2="21" />
      <line x1="12" y1="17" x2="12" y2="21" />
    </svg>
  );
}

// ============================================
// Component
// ============================================

export interface ThemeToggleProps {
  /** Additional class names */
  className?: string;
  /** Show dropdown with all options (default: true) */
  showDropdown?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
}

const sizes = {
  sm: 'p-2',
  md: 'p-2.5',
  lg: 'p-3',
};

const iconSizes = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

/**
 * Theme toggle component with dropdown for theme selection
 *
 * @example
 * ```tsx
 * <ThemeToggle />
 * ```
 */
export function ThemeToggle({
  className,
  showDropdown = true,
  size = 'md',
}: ThemeToggleProps) {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Close dropdown on escape
  useEffect(() => {
    if (!isOpen) return;

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // Get current icon
  const CurrentIcon = resolvedTheme === 'dark' ? MoonIcon : SunIcon;

  // If not showing dropdown, just toggle
  if (!showDropdown) {
    return (
      <button
        onClick={toggleTheme}
        className={cn(
          'rounded-xl bg-white/10 backdrop-blur-sm border border-white/20',
          'hover:bg-white/20 transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
          sizes[size],
          className
        )}
        aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
      >
        <CurrentIcon className={iconSizes[size]} />
      </button>
    );
  }

  const options: { value: Theme; label: string; icon: typeof SunIcon }[] = [
    { value: 'light', label: 'Light', icon: SunIcon },
    { value: 'dark', label: 'Dark', icon: MoonIcon },
    { value: 'system', label: 'System', icon: MonitorIcon },
  ];

  return (
    <div ref={dropdownRef} className={cn('relative', className)}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'rounded-xl bg-white/10 backdrop-blur-sm border border-white/20',
          'hover:bg-white/20 transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
          sizes[size]
        )}
        aria-label="Toggle theme"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <CurrentIcon className={iconSizes[size]} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={cn(
            'absolute right-0 mt-2 w-36 z-50',
            'bg-neutral-900/90 backdrop-blur-xl border border-white/20',
            'rounded-xl shadow-2xl shadow-black/20',
            'animate-fade-up'
          )}
          role="listbox"
          aria-label="Theme options"
        >
          {options.map((option) => {
            const Icon = option.icon;
            const isSelected = theme === option.value;

            return (
              <button
                key={option.value}
                onClick={() => {
                  setTheme(option.value);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-2.5',
                  'text-left text-sm transition-colors duration-150',
                  'first:rounded-t-xl last:rounded-b-xl',
                  isSelected
                    ? 'bg-primary-500/20 text-primary-400'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                )}
                role="option"
                aria-selected={isSelected}
              >
                <Icon className="w-4 h-4" />
                <span>{option.label}</span>
                {isSelected && (
                  <svg
                    className="w-4 h-4 ml-auto text-primary-400"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ThemeToggle;
