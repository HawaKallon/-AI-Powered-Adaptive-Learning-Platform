import axios from 'axios'
import toast from 'react-hot-toast'

// Create axios instance
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    } else if (error.response?.status >= 500) {
      // Server error
      toast.error('Server error. Please try again later.')
    } else if (error.response?.data?.detail) {
      // API error with detail
      toast.error(error.response.data.detail)
    } else if (error.message) {
      // Network or other error
      toast.error(error.message)
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  // Student registration
  registerStudent: (studentData) =>
    api.post('/auth/register/student', studentData),
  
  // Teacher registration
  registerTeacher: (teacherData) =>
    api.post('/auth/register/teacher', teacherData),
  
  // Teacher login
  loginTeacher: (credentials) =>
    api.post('/auth/login/teacher', new URLSearchParams(credentials), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  
  // Student login
  loginStudent: (credentials) =>
    api.post('/auth/login/student', new URLSearchParams(credentials), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  
  // Get current user
  getCurrentUser: () =>
    api.get('/auth/me'),
  
  // Logout
  logout: () =>
    api.post('/auth/logout'),
}

// Student API
export const studentAPI = {
  // Get student profile
  getProfile: () =>
    api.get('/students/me'),
  
  // Update student profile
  updateProfile: (profileData) =>
    api.put('/students/me', profileData),
  
  // Get mastery levels
  getMastery: (subject) =>
    api.get('/students/me/mastery', { params: { subject } }),
  
  // Get assessments
  getAssessments: (subject, topic) =>
    api.get('/students/me/assessments', { params: { subject, topic } }),
  
  // Get learning path
  getLearningPath: (subject) =>
    api.get('/students/me/learning-path', { params: { subject } }),
  
  // Get performance analytics
  getPerformance: (subject) =>
    api.get('/students/me/performance', { params: { subject } }),
  
  // Get interventions
  getInterventions: (subject) =>
    api.get('/students/me/interventions', { params: { subject } }),
}

// Lessons API
export const lessonsAPI = {
  // Request a personalized lesson
  requestLesson: (lessonRequest) =>
    api.post('/lessons/request', lessonRequest, { timeout: 60000 }), // 60 second timeout for lesson generation
  
  // Generate personalized lesson
  generateLesson: (subject, topic) =>
    api.post('/lessons/generate', null, { params: { subject, topic }, timeout: 60000 }),
  
  // Get lesson content
  getLessonContent: (contentId) =>
    api.get(`/lessons/content/${contentId}`),
  
  // Get recommended lessons
  getRecommendedLessons: (subject) =>
    api.get('/lessons/recommended', { params: { subject } }),
  
  // Get lesson history
  getLessonHistory: (subject, topic) =>
    api.get('/lessons/history', { params: { subject, topic } }),
  
  // Submit lesson feedback
  submitFeedback: (contentId, rating, feedback) =>
    api.post('/lessons/feedback', null, {
      params: { content_id: contentId, rating, feedback }
    }),
  
  // Get curriculum topics and subtopics
  getCurriculumTopics: (subject, grade) =>
    api.get('/lessons/curriculum/topics', { params: { subject, grade } }),
  
  // Get topic details
  getTopicDetails: (topic, subject, grade) =>
    api.get(`/lessons/curriculum/topic/${encodeURIComponent(topic)}`, { 
      params: { subject, grade } 
    }),
  
  // Search curriculum content
  searchCurriculum: (query, subject, grade, nResults = 5) =>
    api.get('/lessons/curriculum/search', { 
      params: { query, subject, grade, n_results: nResults } 
    }),
}

// Assessments API
export const assessmentsAPI = {
  // Generate exercise set
  generateExercise: (subject, topic, difficulty, questionCount = 5) =>
    api.post('/assessments/generate-exercise', null, {
      params: { subject, topic, difficulty, question_count: questionCount },
      timeout: 60000 // 60 second timeout for exercise generation
    }),
  
  // Submit assessment
  submitAssessment: (subject, topic, answers, timeTaken) =>
    api.post('/assessments/submit', {
      subject,
      topic,
      answers,
      time_taken: timeTaken
    }),
  
  // Get assessment history
  getAssessments: (subject, topic) =>
    api.get('/assessments/my-assessments', { params: { subject, topic } }),
  
  // Get performance summary
  getPerformance: (subject) =>
    api.get('/assessments/my-performance', { params: { subject } }),
  
  // Create diagnostic assessment
  createDiagnostic: (grade, subject) =>
    api.post('/assessments/diagnostic', null, { params: { grade, subject } }),
  
  // Submit diagnostic assessment
  submitDiagnostic: (subject, answers) =>
    api.post('/assessments/diagnostic/submit', { subject, answers }),
}

// Chatbot API
export const chatbotAPI = {
  // Send chat message
  sendMessage: (message, sessionId) =>
    api.post('/chatbot/chat', null, {
      params: { message, session_id: sessionId },
      timeout: 30000 // 30 second timeout for chatbot
    }),
  
  // Get suggested questions
  getSuggestedQuestions: (subject, topic) =>
    api.get('/chatbot/suggested-questions', { params: { subject, topic } }),
  
  // Get chat history
  getChatHistory: (sessionId, limit = 50) =>
    api.get('/chatbot/history', { params: { session_id: sessionId, limit } }),
  
  // Get chat sessions
  getChatSessions: () =>
    api.get('/chatbot/sessions'),
  
  // Get chat analytics
  getChatAnalytics: () =>
    api.get('/chatbot/analytics'),
  
  // Create new session
  createNewSession: () =>
    api.post('/chatbot/new-session'),
}

// Teacher API (for teacher dashboard)
export const teacherAPI = {
  // Get all students
  getStudents: (grade) =>
    api.get('/students', { params: { grade } }),
  
  // Get student details
  getStudent: (studentId) =>
    api.get(`/students/${studentId}`),
  
  // Get student mastery
  getStudentMastery: (studentId, subject) =>
    api.get(`/students/${studentId}/mastery`, { params: { subject } }),
  
  // Get student assessments
  getStudentAssessments: (studentId, subject, topic) =>
    api.get(`/students/${studentId}/assessments`, { params: { subject, topic } }),
  
  // Get student performance
  getStudentPerformance: (studentId, subject) =>
    api.get(`/students/${studentId}/performance`, { params: { subject } }),
  
  // Get all lesson content
  getAllLessonContent: (subject, grade) =>
    api.get('/lessons/content/all', { params: { subject, grade } }),
  
  // Get lesson analytics
  getLessonAnalytics: (subject, grade) =>
    api.get('/lessons/analytics', { params: { subject, grade } }),
  
  // Delete lesson content
  deleteLessonContent: (contentId) =>
    api.delete(`/lessons/content/${contentId}`),
  
  // Get assessment analytics
  getAssessmentAnalytics: (subject, grade) =>
    api.get('/assessments/analytics', { params: { subject, grade } }),
  
  // Get student chat history
  getStudentChatHistory: (studentId, sessionId, limit) =>
    api.get(`/chatbot/student/${studentId}/history`, {
      params: { session_id: sessionId, limit }
    }),
  
  // Get student chat analytics
  getStudentChatAnalytics: (studentId) =>
    api.get(`/chatbot/student/${studentId}/analytics`),
}

export default api

