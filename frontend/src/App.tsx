import { Navigate, Route, Routes } from 'react-router-dom'

import AppShell from './components/layout/AppShell'
import AnalysisDetailsPage from './pages/AnalysisDetailsPage'
import DashboardPage from './pages/DashboardPage'
import DatasetsPage from './pages/DatasetsPage'
import NewAnalysisPage from './pages/NewAnalysisPage'

function App() {
  return (
    <Routes>
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
    </Routes>
  )
}

export default App