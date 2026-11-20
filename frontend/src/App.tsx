import { Navigate, Route, Routes } from 'react-router-dom'

import AppShell from './components/layout/AppShell'
import ProtectedRoute from './components/auth/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import AnalysisDetailsPage from './pages/AnalysisDetailsPage'
import DashboardPage from './pages/DashboardPage'
import DatasetsPage from './pages/DatasetsPage'
import LoginPage from './pages/LoginPage'
import NewAnalysisPage from './pages/NewAnalysisPage'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Application Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route
              path="/"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route
              path="/dashboard"
              element={<DashboardPage />}
            />

            <Route
              path="/new-analysis"
              element={<NewAnalysisPage />}
            />

            <Route
              path="/analyses/:analysisId"
              element={<AnalysisDetailsPage />}
            />

            <Route
              path="/datasets"
              element={<DatasetsPage />}
            />
          </Route>
        </Route>

        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
