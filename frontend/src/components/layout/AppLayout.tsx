/**
 * AppLayout Component
 * Main application layout wrapper with persistent SyncStatus indicator
 *
 * Phase 5: Integration and End-to-End Testing
 * Subtask 5-1: Integrate offline components into app routing and navigation
 */

import { ReactNode } from 'react';
import { SyncStatus } from '../SyncStatus';
import { cn } from '../../lib/utils';

export interface AppLayoutProps {
  /** Child components to render */
  children: ReactNode;
  /** Additional class names */
  className?: string;
}

/**
 * AppLayout - Main application layout with SyncStatus
 *
 * Wraps protected routes and provides:
 * - Persistent SyncStatus indicator in top-right
 * - Consistent layout structure
 *
 * @example
 * ```tsx
 * <AppLayout>
 *   <DashboardPage />
 * </AppLayout>
 * ```
 */
export function AppLayout({ children, className }: AppLayoutProps) {
  return (
    <div className={cn('relative min-h-screen', className)}>
      {/* Persistent SyncStatus - Fixed to top-right */}
      <div className="fixed top-4 right-4 z-50">
        <SyncStatus variant="compact" showSyncButton />
      </div>

      {/* Main content */}
      {children}
    </div>
  );
}

export default AppLayout;
