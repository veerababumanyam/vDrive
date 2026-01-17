/**
 * SyncStatus Demo Page
 * Test page to verify SyncStatus component functionality
 * Temporary file for development/testing purposes
 */

import { SyncStatus } from '../components/SyncStatus';
import { AppCard } from '../components/ui/AppCard';

export function SyncStatusDemo() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-warm-950 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white mb-2">
            SyncStatus Component Demo
          </h1>
          <p className="text-neutral-600 dark:text-white/70">
            Testing the offline sync status indicator component
          </p>
        </div>

        {/* Compact Variant */}
        <AppCard variant="glass" padding="lg">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
            Compact Variant (Icon Only)
          </h2>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-600 dark:text-white/70">Basic:</span>
              <SyncStatus variant="compact" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-600 dark:text-white/70">With Sync Button:</span>
              <SyncStatus variant="compact" showSyncButton />
            </div>
          </div>
        </AppCard>

        {/* Full Variant */}
        <AppCard variant="glass" padding="lg">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
            Full Variant (With Text)
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-600 dark:text-white/70 w-32">Basic:</span>
              <SyncStatus variant="full" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-600 dark:text-white/70 w-32">With Sync Button:</span>
              <SyncStatus variant="full" showSyncButton />
            </div>
          </div>
        </AppCard>

        {/* Usage Instructions */}
        <AppCard variant="outline" padding="lg">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
            Usage Instructions
          </h2>
          <div className="space-y-4 text-sm">
            <div>
              <h3 className="font-medium text-neutral-900 dark:text-white mb-2">
                What to Verify:
              </h3>
              <ul className="list-disc list-inside space-y-1 text-neutral-600 dark:text-white/70">
                <li>Status indicator is visible</li>
                <li>Shows online/offline state (wifi icon)</li>
                <li>Shows pending sync count (badge on icon)</li>
                <li>Sync button appears when enabled</li>
                <li>Animations work (pulse effect when syncing)</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-neutral-900 dark:text-white mb-2">
                How to Test:
              </h3>
              <ul className="list-disc list-inside space-y-1 text-neutral-600 dark:text-white/70">
                <li>Toggle browser offline mode in DevTools (Network tab)</li>
                <li>Add items to sync queue (favorite photos offline)</li>
                <li>Trigger manual sync with the sync button</li>
                <li>Watch status updates in real-time</li>
              </ul>
            </div>
          </div>
        </AppCard>

        {/* Integration Example */}
        <AppCard variant="glass" padding="lg">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
            Integration Example
          </h2>
          <pre className="bg-neutral-100 dark:bg-white/5 p-4 rounded-lg overflow-x-auto text-xs">
            <code className="text-neutral-800 dark:text-white/90">
{`// In App Header/Navigation:
import { SyncStatus } from './components/SyncStatus';

function AppHeader() {
  return (
    <header>
      <nav>
        {/* ... other nav items ... */}
        <SyncStatus variant="compact" showSyncButton />
      </nav>
    </header>
  );
}

// In Settings Page:
<SyncStatus variant="full" showSyncButton />
`}
            </code>
          </pre>
        </AppCard>
      </div>
    </div>
  );
}

export default SyncStatusDemo;
