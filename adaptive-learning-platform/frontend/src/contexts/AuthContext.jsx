import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(null)

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem('access_token')
        const storedUser = localStorage.getItem('user')
        
        if (storedToken && storedUser) {
          const parsedUser = JSON.parse(storedUser)
          
          // Ensure user_type is set
          if (!parsedUser.user_type) {
            // Try to determine from token or other fields
            if (parsedUser.grade !== undefined) {
              parsedUser.user_type = 'student'
            } else if (parsedUser.subjects !== undefined) {
              parsedUser.user_type = 'teacher'
            }
          }
          
          setToken(storedToken)
          setUser(parsedUser)
          
          // Verify token is still valid
          try {
            const response = await authAPI.getCurrentUser()
            if (response.data.success) {
              const userData = response.data.user
              // Ensure user_type is set
              if (!userData.user_type) {
                if (userData.grade !== undefined) {
                  userData.user_type = 'student'
                } else if (userData.subjects !== undefined) {
                  userData.user_type = 'teacher'
                }
              }
              setUser(userData)
              localStorage.setItem('user', JSON.stringify(userData))
            } else {
              // Token is invalid, clear storage
              clearAuth()
            }
          } catch (error) {
            // Token is invalid, clear storage
            clearAuth()
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        clearAuth()
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const clearAuth = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setUser(null)
    setToken(null)
  }

  const login = async (credentials, userType) => {
    try {
      setLoading(true)
      console.log('🔐 Login attempt:', { userType, email: credentials.username })
      
      let response

      if (userType === 'student') {
        // Student login with email/password
        response = await authAPI.loginStudent(credentials)
      } else {
        // Teacher login with email/password
        response = await authAPI.loginTeacher(credentials)
      }

      console.log('📦 Login response:', response.data)

      if (response.data.success) {
        const { access_token, student, teacher } = response.data
        const userData = student || teacher
        
        if (!userData) {
          console.error('❌ No user data in response!')
          toast.error('Login failed: No user data received')
          return { success: false, error: 'No user data received' }
        }
        
        // Add user_type to the user object
        if (student) {
          userData.user_type = 'student'
        } else if (teacher) {
          userData.user_type = 'teacher'
        }
        
        console.log('✅ Login successful!')
        console.log('👤 User data:', userData)
        console.log('🎭 User type:', userData.user_type)
        
        // Store auth data
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('user', JSON.stringify(userData))
        
        setToken(access_token)
        setUser(userData)
        
        console.log('💾 Auth state updated in context')
        console.log('🔑 Token:', access_token.substring(0, 20) + '...')
        
        toast.success(`Welcome back, ${userData.name}!`)
        return { success: true, user: userData }
      } else {
        console.error('❌ Login failed: success = false')
        toast.error('Login failed')
        return { success: false, error: 'Login failed' }
      }
    } catch (error) {
      console.error('❌ Login error:', error)
      console.error('📊 Error response:', error.response)
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  const register = async (userData, userType) => {
    try {
      setLoading(true)
      let response

      if (userType === 'student') {
        response = await authAPI.registerStudent(userData)
      } else {
        response = await authAPI.registerTeacher(userData)
      }

      if (response.data.success) {
        const { access_token, student, teacher } = response.data
        const newUser = student || teacher
        
        // Add user_type to the user object
        if (student) {
          newUser.user_type = 'student'
        } else if (teacher) {
          newUser.user_type = 'teacher'
        }
        
        console.log('Registration successful - response:', response.data)
        console.log('Registration successful - newUser:', newUser)
        
        // Store auth data
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('user', JSON.stringify(newUser))
        
        setToken(access_token)
        setUser(newUser)
        
        toast.success('Registration successful!')
        return { success: true, user: newUser }
      } else {
        toast.error('Registration failed')
        return { success: false, error: 'Registration failed' }
      }
    } catch (error) {
      console.error('Registration error:', error)
      const errorMessage = error.response?.data?.detail || 'Registration failed'
      toast.error(errorMessage)
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
      toast.success('Logged out successfully')
    }
  }

  const updateUser = (updatedUser) => {
    setUser(updatedUser)
    localStorage.setItem('user', JSON.stringify(updatedUser))
  }

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user,
    isStudent: user?.user_type === 'student',
    isTeacher: user?.user_type === 'teacher',
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
