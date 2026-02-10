import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import LoginPage from './pages/Auth/LoginPage'
import DashboardPage from './pages/Dashboard/DashboardPage'
import CompaniesPage from './pages/Companies/CompaniesPage'
import EngineersPage from './pages/Engineers/EngineersPage'
import ProjectsPage from './pages/Projects/ProjectsPage'
import QuotationsPage from './pages/Quotations/QuotationsPage'
import OrdersPage from './pages/Orders/OrdersPage'
import ContractsPage from './pages/Contracts/ContractsPage'
import InvoicesPage from './pages/Invoices/InvoicesPage'
import JobsPage from './pages/Jobs/JobsPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen">読み込み中...</div>
  if (!user) return <Navigate to="/login" />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="companies" element={<CompaniesPage />} />
          <Route path="engineers" element={<EngineersPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="quotations" element={<QuotationsPage />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="contracts" element={<ContractsPage />} />
          <Route path="invoices" element={<InvoicesPage />} />
          <Route path="jobs" element={<JobsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
