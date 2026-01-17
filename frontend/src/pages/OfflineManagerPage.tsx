/**
 * Offline Manager Page
 * Page wrapper for the OfflineManager component
 * Allows users to manage offline gallery downloads
 *
 * Phase 4: Offline UI Components
 * Subtask 4-1: Create OfflineManager component for gallery selection
 */

import { OfflineManager } from '../components/OfflineManager';

export function OfflineManagerPage() {
  // TODO: Get workspace ID from context/auth when available
  const workspaceId = 'mock-workspace-id';

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-warm-950 py-8 px-4 sm:px-6 lg:px-8">
      <OfflineManager workspaceId={workspaceId} />
    </div>
  );
}

export default OfflineManagerPage;
