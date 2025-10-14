import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { LoadingSpinner } from '../components/Common/LoadingSpinner'
import { BookOpen, GraduationCap, Users } from 'lucide-react'

export const Login = () => {
  const { login, register, loading } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [userType, setUserType] = useState('student') // 'student' or 'teacher'

  // Debug function to clear localStorage
  const clearStorage = () => {
    localStorage.clear()
    window.location.reload()
  }
  const [formData, setFormData] = useState({
    // Common fields
    name: '',
    email: '',
    password: '',
    // Student fields
    grade: '',
    readingLevel: 'intermediate',
    learningPace: 'moderate',
    // Teacher fields
    subjects: [],
  })

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      if (mode === 'login') {
        // Both students and teachers now use email/password
        const result = await login({
          username: formData.email,
          password: formData.password
        }, userType)
        
        if (result.success) {
          // Redirect based on user type
          const redirectPath = userType === 'student' ? '/student' : '/teacher'
          navigate(redirectPath, { replace: true })
        }
      } else {
        const userData = userType === 'student' 
          ? {
              name: formData.name,
              email: formData.email,
              password: formData.password,
              grade: parseInt(formData.grade),
              reading_level: formData.readingLevel,
              learning_pace: formData.learningPace
            }
          : {
              name: formData.name,
              email: formData.email,
              password: formData.password,
              subjects: ['mathematics', 'english', 'science'] // Default subjects
            }
        
        const result = await register(userData, userType)
        
        if (result.success) {
          // Redirect based on user type
          const redirectPath = userType === 'student' ? '/student' : '/teacher'
          navigate(redirectPath, { replace: true })
        }
      }
    } catch (error) {
      console.error('Authentication error:', error)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-primary-600 rounded-full flex items-center justify-center">
            <BookOpen className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Adaptive Learning Platform
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Personalized education for Sierra Leone
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="flex rounded-lg bg-gray-100 p-1">
          <button
            type="button"
            onClick={() => setMode('login')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
              mode === 'login'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
              mode === 'register'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Register
          </button>
        </div>

        {/* User Type Toggle */}
        <div className="flex rounded-lg bg-gray-100 p-1">
          <button
            type="button"
            onClick={() => setUserType('student')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors flex items-center justify-center space-x-2 ${
              userType === 'student'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <GraduationCap className="h-4 w-4" />
            <span>Student</span>
          </button>
          <button
            type="button"
            onClick={() => setUserType('teacher')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors flex items-center justify-center space-x-2 ${
              userType === 'teacher'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Teacher</span>
          </button>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="card">
            <div className="card-content space-y-4">
              {mode === 'register' && (
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Full Name
                  </label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    className="input mt-1"
                    placeholder="Enter your full name"
                    value={formData.name}
                    onChange={handleInputChange}
                  />
                </div>
              )}

              {/* Email field for both login and register */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="input mt-1"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                />
              </div>

              {/* Password field for both login and register */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="input mt-1"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleInputChange}
                />
              </div>

              {userType === 'student' && mode === 'register' && (
                <>
                  <div>
                    <label htmlFor="grade" className="block text-sm font-medium text-gray-700">
                      Grade Level
                    </label>
                    <select
                      id="grade"
                      name="grade"
                      required
                      className="select mt-1"
                      value={formData.grade}
                      onChange={handleInputChange}
                    >
                      <option value="">Select grade</option>
                      {[7, 8, 9, 10, 11, 12].map(grade => (
                        <option key={grade} value={grade}>
                          Grade {grade}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="readingLevel" className="block text-sm font-medium text-gray-700">
                      Reading Level
                    </label>
                    <select
                      id="readingLevel"
                      name="readingLevel"
                      className="select mt-1"
                      value={formData.readingLevel}
                      onChange={handleInputChange}
                    >
                      <option value="basic">Basic</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="learningPace" className="block text-sm font-medium text-gray-700">
                      Learning Pace
                    </label>
                    <select
                      id="learningPace"
                      name="learningPace"
                      className="select mt-1"
                      value={formData.learningPace}
                      onChange={handleInputChange}
                    >
                      <option value="slow">Slow</option>
                      <option value="moderate">Moderate</option>
                      <option value="fast">Fast</option>
                    </select>
                  </div>
                </>
              )}

            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary btn-lg w-full"
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-2">
                  <LoadingSpinner size="sm" />
                  <span>Processing...</span>
                </div>
              ) : (
                mode === 'login' ? 'Sign In' : 'Create Account'
              )}
            </button>
            
            {/* Debug button */}
            <button
              type="button"
              onClick={clearStorage}
              className="mt-4 text-xs text-gray-500 hover:text-gray-700"
            >
              Clear Storage & Reload (Debug)
            </button>
          </div>
        </form>

        {/* Footer */}
        <div className="text-center text-sm text-gray-600">
          <p>© 2024 Adaptive Learning Platform</p>
          <p className="mt-1">Empowering education in Sierra Leone</p>
        </div>
      </div>
    </div>
  )
}
