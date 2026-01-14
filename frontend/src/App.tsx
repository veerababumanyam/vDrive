/**
 * vDrive Frontend Application (app.vdrive.io)
 * Authenticated user application - No public pages
 *
 * Route Structure:
 * - Auth: Sign In (default), Register, Email Verification
 * - Onboarding: Workspace Setup
 * - Protected: Dashboard, Galleries, Clients, Settings
 *
 * Note: Public marketing pages are served by the Website service (vdrive.io)
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './hooks/useTheme';

// Auth Pages
import { RegisterPage } from './pages/Register';
import { LoginPage } from './pages/Login';
import { VerifyEmailPage } from './pages/VerifyEmail';

// Onboarding Pages
import { WorkspaceSetupPage } from './pages/WorkspaceSetup';

// Protected Pages
import { DashboardPage } from './pages/Dashboard';

// UI Components
import { PlaceholderPage } from './components/ui/PlaceholderPage';

// Create React Query client with optimized defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark">
        <BrowserRouter>
          <Routes>
            {/* ============================================
                Auth Routes - Sign In is the default
                ============================================ */}
            <Route path="/" element={<Navigate to="/sign-in" replace />} />
            <Route path="/sign-in" element={<LoginPage />} />
            <Route path="/login" element={<Navigate to="/sign-in" replace />} />
            <Route path="/sign-up" element={<RegisterPage />} />
            <Route path="/register" element={<Navigate to="/sign-up" replace />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />

            {/* ============================================
                Onboarding Flow
                ============================================ */}
            <Route path="/onboarding/workspace" element={<WorkspaceSetupPage />} />

            {/* ============================================
                Protected Application Routes
                ============================================ */}
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/galleries/*" element={<PlaceholderPage />} />
            <Route path="/upload" element={<PlaceholderPage />} />
            <Route path="/clients/*" element={<PlaceholderPage />} />
            <Route path="/settings" element={<PlaceholderPage />} />

            {/* ============================================
                Fallback Routes
                ============================================ */}
            {/* Unknown routes redirect to sign-in */}
            <Route path="*" element={<Navigate to="/sign-in" replace />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
