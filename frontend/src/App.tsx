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

// Auth Context & Components
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Auth Pages
import { RegisterPage } from './pages/Register';
import { LoginPage } from './pages/Login';

import { VerifyEmailPage } from './pages/VerifyEmail';

// Onboarding Pages
import { WorkspaceSetupPage } from './pages/WorkspaceSetup';

// Protected Pages
import { DashboardPage } from './pages/Dashboard';
import { ExportPage } from './pages/Export';
import { MigrationPage } from './pages/Migration';

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
          {/* T076: Wrap app with AuthProvider for authentication state */}
          <AuthProvider>
            <Routes>
              {/* ============================================
                  Auth Routes - Sign In is the default
                  ============================================ */}
              <Route path="/" element={<Navigate to="/signin" replace />} />
              <Route path="/signin" element={<LoginPage />} />
              <Route path="/sign-in" element={<Navigate to="/signin" replace />} />
              <Route path="/login" element={<Navigate to="/signin" replace />} />
              <Route path="/sign-up" element={<RegisterPage />} />
              <Route path="/register" element={<Navigate to="/sign-up" replace />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />

              {/* ============================================
                  Onboarding Flow (Protected)
                  ============================================ */}
              <Route
                path="/onboarding/workspace"
                element={
                  <ProtectedRoute>
                    <WorkspaceSetupPage />
                  </ProtectedRoute>
                }
              />

              {/* ============================================
                  Protected Application Routes
                  ============================================ */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/export"
                element={
                  <ProtectedRoute>
                    <ExportPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/migration"
                element={
                  <ProtectedRoute>
                    <MigrationPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/galleries/*"
                element={
                  <ProtectedRoute>
                    <PlaceholderPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/upload"
                element={
                  <ProtectedRoute>
                    <PlaceholderPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/clients/*"
                element={
                  <ProtectedRoute>
                    <PlaceholderPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <PlaceholderPage />
                  </ProtectedRoute>
                }
              />

              {/* ============================================
                  Fallback Routes
                  ============================================ */}
              {/* Unknown routes redirect to sign-in */}
              <Route path="*" element={<Navigate to="/signin" replace />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
