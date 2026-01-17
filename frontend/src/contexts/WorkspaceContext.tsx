/**
 * Workspace Context
 * Manages workspace state, navigation sidebar state, and workspace switching
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  workspaceApi,
  getCurrentWorkspaceFromStorage,
} from '../services/workspace-api';
import type {
  CurrentWorkspace,
  WorkspaceRole,
  WorkspaceContextValue,
} from '../types/workspace';
import { hasRolePermission } from '../types/workspace';

// ============================================================================
// CONSTANTS
// ============================================================================

const SIDEBAR_STORAGE_KEY = 'rawdrive-sidebar-collapsed';
const QUERY_KEY = ['workspaces'];

// ============================================================================
// CONTEXT
// ============================================================================

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(
  undefined
);

// ============================================================================
// PROVIDER PROPS
// ============================================================================

interface WorkspaceProviderProps {
  children: ReactNode;
}

// ============================================================================
// PROVIDER COMPONENT
// ============================================================================

export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  const queryClient = useQueryClient();

  // Sidebar state (persisted to localStorage)
  const [sidebarCollapsed, setSidebarCollapsedState] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true';
  });

  // Mobile drawer state
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  // Settings expanded state
  const [settingsExpanded, setSettingsExpanded] = useState(false);

  // Current workspace state
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>(
    () => {
      if (typeof window === 'undefined') return null;
      return localStorage.getItem('current_workspace_id');
    }
  );

  // Fetch workspaces with React Query
  const {
    data: workspaces = [],
    isLoading: isLoadingWorkspaces,
    error: workspacesError,
    refetch: refetchWorkspaces,
  } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: workspaceApi.getUserWorkspaces,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // Derive current workspace from fetched workspaces
  const currentWorkspace = useMemo<CurrentWorkspace | null>(() => {
    if (!currentWorkspaceId) {
      // Try to get from storage
      const stored = getCurrentWorkspaceFromStorage();
      if (stored) {
        return {
          ...stored,
          isOwner: stored.role === 'owner',
          isAdmin: stored.role === 'owner' || stored.role === 'admin',
          canEdit:
            stored.role === 'owner' ||
            stored.role === 'admin' ||
            stored.role === 'editor',
        };
      }
      return null;
    }

    const workspace = workspaces.find((w) => w.id === currentWorkspaceId);
    if (!workspace) {
      // Workspace not found in list, try storage
      const stored = getCurrentWorkspaceFromStorage();
      if (stored && stored.id === currentWorkspaceId) {
        return {
          ...stored,
          isOwner: stored.role === 'owner',
          isAdmin: stored.role === 'owner' || stored.role === 'admin',
          canEdit:
            stored.role === 'owner' ||
            stored.role === 'admin' ||
            stored.role === 'editor',
        };
      }
      return null;
    }

    return {
      ...workspace,
      isOwner: workspace.role === 'owner',
      isAdmin: workspace.role === 'owner' || workspace.role === 'admin',
      canEdit:
        workspace.role === 'owner' ||
        workspace.role === 'admin' ||
        workspace.role === 'editor',
    };
  }, [currentWorkspaceId, workspaces]);

  // User role (default to viewer if no workspace)
  const userRole = useMemo<WorkspaceRole>(() => {
    return currentWorkspace?.role ?? 'viewer';
  }, [currentWorkspace]);

  // Initialize current workspace from storage on mount
  useEffect(() => {
    if (!currentWorkspaceId) {
      const storedId = localStorage.getItem('current_workspace_id');
      if (storedId) {
        setCurrentWorkspaceId(storedId);
      }
    }
  }, [currentWorkspaceId]);

  // Sidebar collapse handlers
  const setSidebarCollapsed = useCallback((collapsed: boolean) => {
    setSidebarCollapsedState(collapsed);
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(!sidebarCollapsed);
  }, [sidebarCollapsed, setSidebarCollapsed]);

  // Mobile drawer handlers
  const toggleMobileDrawer = useCallback(() => {
    setMobileDrawerOpen((prev) => !prev);
  }, []);

  // Settings handlers
  const toggleSettings = useCallback(() => {
    setSettingsExpanded((prev) => !prev);
  }, []);

  // Permission check helper
  const hasPermission = useCallback(
    (requiredRole: WorkspaceRole): boolean => {
      return hasRolePermission(userRole, requiredRole);
    },
    [userRole]
  );

  // Switch workspace
  const switchWorkspace = useCallback(
    async (id: string): Promise<void> => {
      try {
        const workspace = await workspaceApi.switchWorkspace(id);
        setCurrentWorkspaceId(workspace.id);
        // Invalidate all workspace-specific queries
        queryClient.invalidateQueries({ queryKey: ['galleries'] });
        queryClient.invalidateQueries({ queryKey: ['clients'] });
        queryClient.invalidateQueries({ queryKey: ['invitations'] });
      } catch (error) {
        console.error('Failed to switch workspace:', error);
        throw error;
      }
    },
    [queryClient]
  );

  // Refresh workspaces
  const refreshWorkspaces = useCallback(async (): Promise<void> => {
    await refetchWorkspaces();
  }, [refetchWorkspaces]);

  // Context value
  const contextValue = useMemo<WorkspaceContextValue>(
    () => ({
      // Workspace data
      currentWorkspace,
      workspaces,
      isLoadingWorkspaces,
      workspacesError: workspacesError as Error | null,

      // Workspace operations
      switchWorkspace,
      refreshWorkspaces,

      // User role helpers
      userRole,
      hasPermission,

      // Sidebar state
      sidebarCollapsed,
      setSidebarCollapsed,
      toggleSidebar,

      // Mobile drawer state
      mobileDrawerOpen,
      setMobileDrawerOpen,
      toggleMobileDrawer,

      // Settings state
      settingsExpanded,
      setSettingsExpanded,
      toggleSettings,
    }),
    [
      currentWorkspace,
      workspaces,
      isLoadingWorkspaces,
      workspacesError,
      switchWorkspace,
      refreshWorkspaces,
      userRole,
      hasPermission,
      sidebarCollapsed,
      setSidebarCollapsed,
      toggleSidebar,
      mobileDrawerOpen,
      toggleMobileDrawer,
      settingsExpanded,
      toggleSettings,
    ]
  );

  return (
    <WorkspaceContext.Provider value={contextValue}>
      {children}
    </WorkspaceContext.Provider>
  );
}

// ============================================================================
// HOOK
// ============================================================================

/**
 * Hook to access workspace context
 * Must be used within WorkspaceProvider
 */
export function useWorkspaceContext(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error(
      'useWorkspaceContext must be used within a WorkspaceProvider'
    );
  }
  return context;
}

// ============================================================================
// EXPORTS
// ============================================================================

export { WorkspaceContext };
export default WorkspaceProvider;
