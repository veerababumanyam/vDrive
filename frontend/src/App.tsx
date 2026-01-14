/**
 * vDrive Frontend Application
 * Main app component with routing and providers
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './hooks/useTheme';

// Pages
import { RegisterPage } from './pages/Register';
import { LoginPage } from './pages/Login';
import { VerifyEmailPage } from './pages/VerifyEmail';
import { WorkspaceSetupPage } from './pages/WorkspaceSetup';
import { DashboardPage } from './pages/Dashboard';

import { PlaceholderPage } from './components/ui/PlaceholderPage';

// Create React Query client
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
            {/* Public Routes */}
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />

            {/* Onboarding Routes */}
            <Route path="/onboarding/workspace" element={<WorkspaceSetupPage />} />

            {/* Protected Routes */}
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/galleries/*" element={<PlaceholderPage />} />
            <Route path="/upload" element={<PlaceholderPage />} />
            <Route path="/clients/*" element={<PlaceholderPage />} />
            <Route path="/settings" element={<PlaceholderPage />} />

            {/* Auth Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Default redirects */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
