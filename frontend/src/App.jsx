import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'
import DocumentsPage from './pages/DocumentsPage'
import AuditPage from './pages/AuditPage'
import Navbar from './components/Navbar'
import { Loader2 } from 'lucide-react'

// Protected Route wrapper component
function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-zinc-500">
        <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/chat" replace />
  }

  return children
}

// Layout wrapper component to conditionally show Navbar
function AppLayout() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-surface-950 text-zinc-100 flex flex-col">
      {isAuthenticated && <Navbar />}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route
            path="/"
            element={
              isAuthenticated ? <Navigate to="/chat" replace /> : <Navigate to="/login" replace />
            }
          />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <ProtectedRoute adminOnly>
                <DocumentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit"
            element={
              <ProtectedRoute adminOnly>
                <AuditPage />
              </ProtectedRoute>
            }
          />
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  )
}
