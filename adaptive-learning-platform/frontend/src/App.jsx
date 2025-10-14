import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { AuthProvider } from './contexts/AuthContext'
import { LoadingSpinner } from './components/Common/LoadingSpinner'
import { Login } from './pages/Login'
import { StudentDashboard } from './pages/StudentDashboard'
import { TeacherDashboard } from './pages/TeacherDashboard'
import { Assessment } from './pages/Assessment'
import { NotFound } from './pages/NotFound'

// Protected Route component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth()
  
  console.log('ProtectedRoute - user:', user, 'requiredRole:', requiredRole, 'loading:', loading)
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  if (!user) {
    console.log('ProtectedRoute - No user, redirecting to login')
    return <Navigate to="/login" replace />
  }
  
  if (requiredRole && user.user_type !== requiredRole) {
    console.log('ProtectedRoute - Role mismatch, redirecting to home')
    return <Navigate to="/" replace />
  }
  
  console.log('ProtectedRoute - Access granted')
  return children
}

// Public Route component (redirects to dashboard if already logged in)
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  if (user) {
    console.log('PublicRoute - User exists, redirecting to:', user.user_type === 'student' ? '/student' : '/teacher')
    const redirectTo = user.user_type === 'student' ? '/student' : '/teacher'
    return <Navigate to={redirectTo} replace />
  }
  
  return children
}

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Public routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          
          {/* Student routes */}
          <Route
            path="/student"
            element={
              <ProtectedRoute requiredRole="student">
                <StudentDashboard />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/student/assessment/:subject/:topic"
            element={
              <ProtectedRoute requiredRole="student">
                <Assessment />
              </ProtectedRoute>
            }
          />
          
          {/* Teacher routes */}
          <Route
            path="/teacher"
            element={
              <ProtectedRoute requiredRole="teacher">
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />
          
          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* 404 page */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </AuthProvider>
  )
}

export default App
