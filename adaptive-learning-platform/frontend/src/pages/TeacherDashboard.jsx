import React, { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { LoadingSpinner } from '../components/Common/LoadingSpinner'
import { 
  Users, 
  BarChart3, 
  BookOpen, 
  MessageCircle, 
  Settings,
  LogOut,
  User,
  TrendingUp,
  AlertTriangle
} from 'lucide-react'

export const TeacherDashboard = () => {
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedGrade, setSelectedGrade] = useState('all')

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'students', name: 'Students', icon: Users },
    { id: 'lessons', name: 'Lessons', icon: BookOpen },
    { id: 'chatbot', name: 'AI Tutor', icon: MessageCircle },
    { id: 'analytics', name: 'Analytics', icon: TrendingUp },
    { id: 'settings', name: 'Settings', icon: Settings },
  ]

  const grades = [
    { id: 'all', name: 'All Grades' },
    { id: '7', name: 'Grade 7' },
    { id: '8', name: 'Grade 8' },
    { id: '9', name: 'Grade 9' },
    { id: '10', name: 'Grade 10' },
    { id: '11', name: 'Grade 11' },
    { id: '12', name: 'Grade 12' },
  ]

  const handleLogout = () => {
    logout()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Users className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  Teacher Dashboard
                </h1>
                <p className="text-sm text-gray-600">Adaptive Learning Platform</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-gray-600" />
                </div>
                <div className="text-sm">
                  <p className="font-medium text-gray-900">{user?.name}</p>
                  <p className="text-gray-600">Teacher</p>
                </div>
              </div>
              
              <button
                onClick={handleLogout}
                className="btn-ghost btn-sm flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="lg:w-64 flex-shrink-0">
            <div className="card">
              <div className="card-content">
                <h3 className="font-semibold text-gray-900 mb-4">Navigation</h3>
                <nav className="space-y-2">
                  {tabs.map((tab) => {
                    const Icon = tab.icon
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                          activeTab === tab.id
                            ? 'bg-primary-100 text-primary-700'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{tab.name}</span>
                      </button>
                    )
                  })}
                </nav>
              </div>
            </div>

            {/* Grade Filter */}
            <div className="card mt-6">
              <div className="card-content">
                <h3 className="font-semibold text-gray-900 mb-4">Filter by Grade</h3>
                <div className="space-y-2">
                  {grades.map((grade) => (
                    <button
                      key={grade.id}
                      onClick={() => setSelectedGrade(grade.id)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        selectedGrade === grade.id
                          ? 'bg-primary-100 text-primary-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {grade.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Welcome back, {user?.name}!</h2>
                  <p className="text-gray-600">Here's your teaching overview.</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Total Students</p>
                          <p className="text-2xl font-bold text-gray-900">156</p>
                        </div>
                        <div className="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
                          <Users className="h-6 w-6 text-primary-600" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Active Lessons</p>
                          <p className="text-2xl font-bold text-gray-900">24</p>
                        </div>
                        <div className="h-12 w-12 bg-secondary-100 rounded-lg flex items-center justify-center">
                          <BookOpen className="h-6 w-6 text-secondary-600" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Avg. Performance</p>
                          <p className="text-2xl font-bold text-gray-900">78%</p>
                        </div>
                        <div className="h-12 w-12 bg-accent-100 rounded-lg flex items-center justify-center">
                          <TrendingUp className="h-6 w-6 text-accent-600" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Need Help</p>
                          <p className="text-2xl font-bold text-gray-900">12</p>
                        </div>
                        <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
                          <AlertTriangle className="h-6 w-6 text-red-600" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="text-lg font-semibold text-gray-900">Recent Student Activity</h3>
                    </div>
                    <div className="card-content">
                      <div className="space-y-4">
                        <div className="flex items-center space-x-3">
                          <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                            <TrendingUp className="h-4 w-4 text-green-600" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">Fatmata Kamara improved in Algebra</p>
                            <p className="text-xs text-gray-600">Grade 8 • 2 hours ago</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <BookOpen className="h-4 w-4 text-blue-600" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">Mohamed Sesay completed Geometry lesson</p>
                            <p className="text-xs text-gray-600">Grade 9 • 4 hours ago</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <div className="h-8 w-8 bg-red-100 rounded-full flex items-center justify-center">
                            <AlertTriangle className="h-4 w-4 text-red-600" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">Aminata Bangura needs help with Fractions</p>
                            <p className="text-xs text-gray-600">Grade 7 • 1 day ago</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-header">
                      <h3 className="text-lg font-semibold text-gray-900">Class Performance</h3>
                    </div>
                    <div className="card-content">
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Mathematics</span>
                            <span className="font-medium">82%</span>
                          </div>
                          <div className="progress">
                            <div className="progress-bar" style={{ width: '82%' }}></div>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">English</span>
                            <span className="font-medium">76%</span>
                          </div>
                          <div className="progress">
                            <div className="progress-bar" style={{ width: '76%' }}></div>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Science</span>
                            <span className="font-medium">71%</span>
                          </div>
                          <div className="progress">
                            <div className="progress-bar" style={{ width: '71%' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'students' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Students</h2>
                  <p className="text-gray-600">Manage and monitor your students' progress.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Student Management Coming Soon</h3>
                      <p className="text-gray-600">Detailed student management will be available here.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'lessons' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Lessons</h2>
                  <p className="text-gray-600">Manage lesson content and track usage.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Lesson Management Coming Soon</h3>
                      <p className="text-gray-600">Lesson content management will be available here.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'chatbot' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">AI Tutor</h2>
                  <p className="text-gray-600">Monitor student interactions with the AI tutor.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">AI Tutor Analytics Coming Soon</h3>
                      <p className="text-gray-600">AI tutor monitoring and analytics will be available here.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
                  <p className="text-gray-600">Detailed analytics and insights about your class.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Coming Soon</h3>
                      <p className="text-gray-600">Comprehensive analytics will be available here.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
                  <p className="text-gray-600">Manage your account and preferences.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Settings Coming Soon</h3>
                      <p className="text-gray-600">Account settings will be available here.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


