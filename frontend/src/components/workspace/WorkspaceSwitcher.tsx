/**
 * WorkspaceSwitcher Component
 * Dropdown for switching between workspaces
 * iOS-inspired design with glassmorphism
 */

import { useState, useRef, useEffect, useCallback, type FC } from 'react';
import { cn } from '../../lib/utils';
import { usePrefersReducedMotion, useHaptic } from '../../hooks/useMobile';
import {
  ChevronDownIcon,
  CheckIcon,
  PlusIcon,
} from '../../hooks/useWorkspace';
import type { WorkspaceSwitcherProps } from '../../types/workspace';

// ============================================================================
// COMPONENT
// ============================================================================

export const WorkspaceSwitcher: FC<WorkspaceSwitcherProps> = ({
  currentWorkspace,
  workspaces,
  onSelect,
  compact = false,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const prefersReducedMotion = usePrefersReducedMotion();
  const haptic = useHaptic();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () =>
        document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        buttonRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // Toggle dropdown
  const handleToggle = useCallback(() => {
    if (haptic.isSupported) {
      haptic.light();
    }
    setIsOpen((prev) => !prev);
  }, [haptic]);

  // Select workspace
  const handleSelect = useCallback(
    (workspaceId: string) => {
      if (haptic.isSupported) {
        haptic.medium();
      }
      onSelect(workspaceId);
      setIsOpen(false);
    },
    [onSelect, haptic]
  );

  // Get initials for avatar
  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map((word) => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Trigger button styles
  const triggerStyles = cn(
    'group flex items-center gap-2',
    'min-h-[40px]',
    compact ? 'px-2' : 'px-3',
    'rounded-xl',

    // Background
    'bg-white/50 dark:bg-white/[0.06]',
    'hover:bg-neutral-100 dark:hover:bg-white/[0.1]',

    // Border
    'border border-neutral-200/60 dark:border-white/10',
    'hover:border-neutral-300 dark:hover:border-white/20',

    // Transitions
    !prefersReducedMotion && 'transition-all duration-200',

    // Focus
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',

    // Touch
    'active:scale-[0.98]',

    className
  );

  // Avatar styles
  const avatarStyles = cn(
    'flex items-center justify-center',
    'w-7 h-7 rounded-lg',
    'bg-gradient-to-br from-primary-400 to-primary-600',
    'text-white text-xs font-semibold',
    'shadow-sm'
  );

  // Dropdown panel styles
  const dropdownStyles = cn(
    'absolute top-full left-0 mt-2 z-50',
    'min-w-[240px] max-w-[300px]',
    'p-2',

    // Glass effect
    'bg-white/95 dark:bg-warm-950/95',
    'backdrop-blur-2xl',
    '[backdrop-filter:blur(40px)_saturate(180%)]',
    '[-webkit-backdrop-filter:blur(40px)_saturate(180%)]',

    // Border & shadow
    'border border-neutral-200/60 dark:border-white/15',
    'rounded-2xl',
    'shadow-2xl shadow-neutral-300/30 dark:shadow-black/40',

    // Animation
    !prefersReducedMotion && [
      'animate-fade-in-up',
      'origin-top-left',
    ]
  );

  // Workspace item styles
  const getItemStyles = (isSelected: boolean) =>
    cn(
      'flex items-center gap-3 w-full',
      'min-h-[48px] px-3',
      'rounded-xl',

      // Hover & active
      'hover:bg-neutral-100 dark:hover:bg-white/[0.08]',
      'active:scale-[0.98]',

      // Selected state
      isSelected && [
        'bg-primary-500/10 dark:bg-primary-500/20',
      ],

      // Transitions
      !prefersReducedMotion && 'transition-all duration-150',

      // Focus
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
    );

  if (!currentWorkspace) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-2',
          'text-neutral-400 dark:text-neutral-500 text-sm',
          className
        )}
      >
        <div className={cn(avatarStyles, 'bg-neutral-300 dark:bg-neutral-700')}>
          ?
        </div>
        {!compact && <span>No workspace</span>}
      </div>
    );
  }

  return (
    <div ref={dropdownRef} className="relative">
      {/* Trigger Button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        className={triggerStyles}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label={`Current workspace: ${currentWorkspace.name}. Click to switch.`}
      >
        {/* Workspace Avatar */}
        {currentWorkspace.logoUrl ? (
          <img
            src={currentWorkspace.logoUrl}
            alt=""
            className="w-7 h-7 rounded-lg object-cover"
          />
        ) : (
          <div className={avatarStyles}>
            {getInitials(currentWorkspace.name)}
          </div>
        )}

        {/* Workspace Name */}
        {!compact && (
          <span className="flex-1 text-left text-sm font-medium text-neutral-700 dark:text-neutral-200 truncate max-w-[140px]">
            {currentWorkspace.name}
          </span>
        )}

        {/* Chevron */}
        <ChevronDownIcon
          className={cn(
            'w-4 h-4 text-neutral-400 dark:text-neutral-500',
            !prefersReducedMotion && 'transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className={dropdownStyles} role="listbox" aria-label="Select workspace">
          {/* Header */}
          <div className="px-3 py-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
              Workspaces
            </span>
          </div>

          {/* Workspace List */}
          <ul className="space-y-0.5">
            {workspaces.map((workspace) => {
              const isSelected = workspace.id === currentWorkspace.id;

              return (
                <li key={workspace.id}>
                  <button
                    type="button"
                    onClick={() => handleSelect(workspace.id)}
                    className={getItemStyles(isSelected)}
                    role="option"
                    aria-selected={isSelected}
                  >
                    {/* Workspace Avatar */}
                    {workspace.logoUrl ? (
                      <img
                        src={workspace.logoUrl}
                        alt=""
                        className="w-8 h-8 rounded-lg object-cover"
                      />
                    ) : (
                      <div
                        className={cn(
                          'flex items-center justify-center',
                          'w-8 h-8 rounded-lg',
                          isSelected
                            ? 'bg-gradient-to-br from-primary-400 to-primary-600'
                            : 'bg-neutral-200 dark:bg-white/20',
                          'text-xs font-semibold',
                          isSelected
                            ? 'text-white'
                            : 'text-neutral-600 dark:text-neutral-300'
                        )}
                      >
                        {getInitials(workspace.name)}
                      </div>
                    )}

                    {/* Workspace Info */}
                    <div className="flex-1 min-w-0 text-left">
                      <div className="text-sm font-medium text-neutral-800 dark:text-neutral-100 truncate">
                        {workspace.name}
                      </div>
                      <div className="text-xs text-neutral-500 dark:text-neutral-400 capitalize">
                        {workspace.role}
                      </div>
                    </div>

                    {/* Selected Check */}
                    {isSelected && (
                      <CheckIcon className="w-5 h-5 text-primary-500 flex-shrink-0" />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>

          {/* Divider */}
          <div className="my-2 border-t border-neutral-200/60 dark:border-white/10" />

          {/* Create New Workspace */}
          <button
            type="button"
            className={cn(
              'flex items-center gap-3 w-full',
              'min-h-[44px] px-3',
              'rounded-xl',
              'text-primary-600 dark:text-primary-400',
              'hover:bg-primary-500/10 dark:hover:bg-primary-500/20',
              'active:scale-[0.98]',
              !prefersReducedMotion && 'transition-all duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
            )}
            onClick={() => {
              // TODO: Navigate to workspace creation
              setIsOpen(false);
            }}
          >
            <div
              className={cn(
                'flex items-center justify-center',
                'w-8 h-8 rounded-lg',
                'bg-primary-500/10 dark:bg-primary-500/20'
              )}
            >
              <PlusIcon className="w-4 h-4" />
            </div>
            <span className="text-sm font-medium">Create Workspace</span>
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// DISPLAY NAME
// ============================================================================

WorkspaceSwitcher.displayName = 'WorkspaceSwitcher';

// ============================================================================
// EXPORTS
// ============================================================================

export default WorkspaceSwitcher;
