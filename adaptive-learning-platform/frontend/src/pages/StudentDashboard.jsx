import React, { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { LoadingSpinner } from '../components/Common/LoadingSpinner'
import { CurriculumTopics } from '../components/Student/CurriculumTopics'
import { lessonsAPI, chatbotAPI } from '../services/api'
import { 
  BookOpen, 
  Brain, 
  MessageCircle, 
  BarChart3, 
  Target,
  LogOut,
  User,
  Plus,
  Send,
  Search
} from 'lucide-react'

export const StudentDashboard = () => {
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedSubject, setSelectedSubject] = useState('mathematics')
  const [lessonRequest, setLessonRequest] = useState({
    subject: 'mathematics',
    topic: '',
    specificFocus: '',
    grade: user?.grade || 8
  })
  const [isGeneratingLesson, setIsGeneratingLesson] = useState(false)
  const [generatedLesson, setGeneratedLesson] = useState(null)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [isSendingMessage, setIsSendingMessage] = useState(false)

  // Debug logging
  console.log('StudentDashboard - user:', user)
  console.log('StudentDashboard - user type:', user?.user_type)

  const subjects = [
    { id: 'mathematics', name: 'Mathematics', color: 'primary' },
    { id: 'english', name: 'English', color: 'secondary' },
    { id: 'science', name: 'Science', color: 'accent' },
  ]

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'curriculum', name: 'Curriculum', icon: Search },
    { id: 'lessons', name: 'Lessons', icon: BookOpen },
    { id: 'assessments', name: 'Assessments', icon: Target },
    { id: 'chatbot', name: 'AI Tutor', icon: MessageCircle },
    { id: 'progress', name: 'Progress', icon: Brain },
  ]

  const handleLogout = () => {
    logout()
  }

  const handleLessonRequestChange = (e) => {
    const { name, value } = e.target
    setLessonRequest(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleGenerateLesson = async (e) => {
    e.preventDefault()
    setIsGeneratingLesson(true)
    
    try {
      console.log('Generating lesson for:', lessonRequest)
      
      // Call the API to generate lesson
      const response = await lessonsAPI.requestLesson({
        subject: lessonRequest.subject,
        topic: lessonRequest.topic,
        specific_focus: lessonRequest.specificFocus,
        grade: lessonRequest.grade
      })
      
      if (response.data.success) {
        const lesson = response.data.lesson
        // Transform the API response to match frontend expectations
        setGeneratedLesson({
          id: lesson.id,
          title: lesson.title,
          subject: lesson.subject,
          content: lesson.content,
          examples: lesson.examples.map(example => ({
            title: example.title,
            description: example.problem || example.description,
            details: example.explanation || example.details
          })),
          keyPoints: lesson.keyPoints || lesson.key_points || [],
          estimatedTime: `${lesson.estimatedTime || 25} minutes`
        })
        console.log('Lesson generated successfully:', response.data.lesson)
      } else {
        console.error('Failed to generate lesson:', response.data)
        // Fallback to mock data if API fails
        setGeneratedLesson({
          id: 'lesson-1',
          title: `${lessonRequest.topic} - Grade ${lessonRequest.grade}`,
          subject: lessonRequest.subject,
          content: `This is a generated lesson about ${lessonRequest.topic} for Grade ${lessonRequest.grade} students in Sierra Leone. The lesson includes local examples and context relevant to Sierra Leonean students.`,
          examples: [
            {
              title: "Sierra Leone Example",
              description: `A practical example using ${lessonRequest.topic} in a Sierra Leonean context.`,
              details: "This example shows how the concept applies to daily life in Sierra Leone."
            }
          ],
          keyPoints: [
            `Understanding ${lessonRequest.topic} fundamentals`,
            `Applying concepts to Sierra Leone context`,
            `Practical examples and exercises`
          ],
          estimatedTime: "25 minutes"
        })
      }
      
    } catch (error) {
      console.error('Error generating lesson:', error)
      // Fallback to mock data on error
      setGeneratedLesson({
        id: 'lesson-1',
        title: `${lessonRequest.topic} - Grade ${lessonRequest.grade}`,
        subject: lessonRequest.subject,
        content: `This is a generated lesson about ${lessonRequest.topic} for Grade ${lessonRequest.grade} students in Sierra Leone. The lesson includes local examples and context relevant to Sierra Leonean students.`,
        examples: [
          {
            title: "Sierra Leone Example",
            description: `A practical example using ${lessonRequest.topic} in a Sierra Leonean context.`,
            details: "This example shows how the concept applies to daily life in Sierra Leone."
          }
        ],
        keyPoints: [
          `Understanding ${lessonRequest.topic} fundamentals`,
          `Applying concepts to Sierra Leone context`,
          `Practical examples and exercises`
        ],
        estimatedTime: "25 minutes"
      })
    } finally {
      setIsGeneratingLesson(false)
    }
  }

  const handleChatSubmit = async (e) => {
    e.preventDefault()
    if (!chatInput.trim() || !generatedLesson) return

    const userMessage = chatInput.trim()
    setChatInput('')
    setIsSendingMessage(true)

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    }
    setChatMessages(prev => [...prev, newUserMessage])

    try {
      // Call chatbot API
      const response = await chatbotAPI.sendMessage(
        userMessage,
        `lesson-${generatedLesson.id}-${Date.now()}`
      )

      if (response.data.success) {
        const botMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: response.data.response.response,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, botMessage])
      } else {
        // Fallback response
        const botMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: "I'm here to help you understand this lesson! Can you ask me a specific question about the content?",
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, botMessage])
      }
    } catch (error) {
      console.error('Error sending chat message:', error)
      // Fallback response
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: "I'm here to help you understand this lesson! Can you ask me a specific question about the content?",
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, botMessage])
    } finally {
      setIsSendingMessage(false)
    }
  }

  const clearChat = () => {
    setChatMessages([])
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <BookOpen className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  Adaptive Learning Platform
                </h1>
                <p className="text-sm text-gray-600">Sierra Leone</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-gray-600" />
                </div>
                <div className="text-sm">
                  <p className="font-medium text-gray-900">{user?.name}</p>
                  <p className="text-gray-600">Grade {user?.grade}</p>
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

            {/* Subject Selector */}
            <div className="card mt-6">
              <div className="card-content">
                <h3 className="font-semibold text-gray-900 mb-4">Subjects</h3>
                <div className="space-y-2">
                  {subjects.map((subject) => (
                    <button
                      key={subject.id}
                      onClick={() => setSelectedSubject(subject.id)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        selectedSubject === subject.id
                          ? `bg-${subject.color}-100 text-${subject.color}-700`
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <span>{subject.name}</span>
                      <div className={`h-2 w-2 rounded-full bg-${subject.color}-500`}></div>
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
                  <p className="text-gray-600">Here's your learning overview for {selectedSubject}.</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Mastery Level</p>
                          <p className="text-2xl font-bold text-gray-900">75%</p>
                        </div>
                        <div className="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
                          <Target className="h-6 w-6 text-primary-600" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Lessons Completed</p>
                          <p className="text-2xl font-bold text-gray-900">12</p>
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
                          <p className="text-sm font-medium text-gray-600">AI Tutor Sessions</p>
                          <p className="text-2xl font-bold text-gray-900">8</p>
                        </div>
                        <div className="h-12 w-12 bg-accent-100 rounded-lg flex items-center justify-center">
                          <MessageCircle className="h-6 w-6 text-accent-600" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
                  </div>
                  <div className="card-content">
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                          <Target className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">Completed Algebra Assessment</p>
                          <p className="text-xs text-gray-600">2 hours ago • Score: 85%</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <BookOpen className="h-4 w-4 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">Finished Geometry Lesson</p>
                          <p className="text-xs text-gray-600">1 day ago • 25 minutes</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                          <MessageCircle className="h-4 w-4 text-purple-600" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">Chatted with AI Tutor</p>
                          <p className="text-xs text-gray-600">2 days ago • 15 minutes</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'curriculum' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Curriculum Explorer</h2>
                  <p className="text-gray-600">
                    Explore topics and subtopics from the Sierra Leone curriculum for {selectedSubject}.
                  </p>
                </div>
                
                <CurriculumTopics
                  subject={selectedSubject}
                  grade={user?.grade || 10}
                  onTopicSelect={(topic) => {
                    console.log('Topic selected:', topic)
                    // Set the selected topic in the lesson request form
                    setLessonRequest(prev => ({
                      ...prev,
                      subject: topic.subject || selectedSubject,
                      topic: topic.topic,
                      grade: topic.grade || user?.grade || 10
                    }))
                    // Switch to lessons tab to generate lesson
                    setActiveTab('lessons')
                  }}
                />
              </div>
            )}

            {activeTab === 'lessons' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Request a Lesson</h2>
                  <p className="text-gray-600">Tell us what you'd like to learn and we'll create a personalized lesson for you.</p>
                </div>
                
                {/* Lesson Request Form */}
                <div className="card">
                  <div className="card-content">
                    <form onSubmit={handleGenerateLesson} className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Subject Selection */}
                        <div>
                          <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
                            Subject
                          </label>
                          <select
                            id="subject"
                            name="subject"
                            value={lessonRequest.subject}
                            onChange={handleLessonRequestChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            required
                          >
                            <option value="mathematics">Mathematics</option>
                            <option value="english">English</option>
                            <option value="science">Science</option>
                          </select>
                        </div>

                        {/* Grade Level */}
                        <div>
                          <label htmlFor="grade" className="block text-sm font-medium text-gray-700 mb-2">
                            Grade Level
                          </label>
                          <select
                            id="grade"
                            name="grade"
                            value={lessonRequest.grade}
                            onChange={handleLessonRequestChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            required
                          >
                            <option value={7}>Grade 7</option>
                            <option value={8}>Grade 8</option>
                            <option value={9}>Grade 9</option>
                            <option value={10}>Grade 10</option>
                            <option value={11}>Grade 11</option>
                            <option value={12}>Grade 12</option>
                          </select>
                        </div>
                      </div>

                      {/* Topic */}
                      <div>
                        <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
                          Topic or Concept
                        </label>
                        <input
                          type="text"
                          id="topic"
                          name="topic"
                          value={lessonRequest.topic}
                          onChange={handleLessonRequestChange}
                          placeholder="e.g., Algebra, Grammar, Photosynthesis"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          required
                        />
                      </div>

                      {/* Specific Focus */}
                      <div>
                        <label htmlFor="specificFocus" className="block text-sm font-medium text-gray-700 mb-2">
                          Specific Focus (Optional)
                        </label>
                        <input
                          type="text"
                          id="specificFocus"
                          name="specificFocus"
                          value={lessonRequest.specificFocus}
                          onChange={handleLessonRequestChange}
                          placeholder="e.g., word problems, essay writing, chemical reactions"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      {/* Submit Button */}
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={isGeneratingLesson || !lessonRequest.topic.trim()}
                          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isGeneratingLesson ? (
                            <>
                              <LoadingSpinner size="sm" className="mr-2" />
                              Generating Lesson...
                            </>
                          ) : (
                            <>
                              <Send className="h-5 w-5 mr-2" />
                              Generate Lesson
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                  </div>
                </div>

                {/* Generated Lesson Display */}
                {generatedLesson && (
                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-xl font-semibold text-gray-900">{generatedLesson.title}</h3>
                        <span className="text-sm text-gray-500">⏱️ {generatedLesson.estimatedTime}</span>
                      </div>
                      
                      <div className="prose max-w-none">
                        {/* Lesson Content with proper markdown rendering */}
                        <div className="prose prose-sm max-w-none mb-6">
                          <div className="text-gray-700 whitespace-pre-line leading-relaxed">
                            {generatedLesson.content}
                          </div>
                        </div>
                        
                        {/* Objectives (if available) */}
                        {generatedLesson.objectives && generatedLesson.objectives.length > 0 && (
                          <div className="mb-6">
                            <h4 className="text-lg font-medium text-gray-900 mb-3">Learning Objectives</h4>
                            <ul className="list-disc list-inside space-y-2">
                              {generatedLesson.objectives.map((objective, index) => (
                                <li key={index} className="text-gray-700">{objective}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {/* Key Points */}
                        {generatedLesson.keyPoints && generatedLesson.keyPoints.length > 0 && (
                          <div className="mb-6">
                            <h4 className="text-lg font-medium text-gray-900 mb-3">Key Learning Points</h4>
                            <ul className="list-disc list-inside space-y-1 text-gray-700">
                              {generatedLesson.keyPoints.map((point, index) => (
                                <li key={index}>{point}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="mb-6">
                          <h4 className="text-lg font-medium text-gray-900 mb-3">Sierra Leone Examples</h4>
                          {generatedLesson.examples.map((example, index) => (
                            <div key={index} className="bg-blue-50 p-4 rounded-lg mb-3">
                              <h5 className="font-medium text-blue-900 mb-2">{example.title}</h5>
                              <p className="text-blue-800 mb-2">{example.description}</p>
                              <p className="text-blue-700 text-sm">{example.details}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Interactive Chatbot */}
                {generatedLesson && (
                  <div className="card">
                    <div className="card-content">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-xl font-semibold text-gray-900">Ask Questions</h3>
                        <button
                          onClick={clearChat}
                          className="text-sm text-gray-500 hover:text-gray-700"
                        >
                          Clear Chat
                        </button>
                      </div>
                      
                      {/* Chat Messages */}
                      <div className="mb-4 max-h-96 overflow-y-auto space-y-3">
                        {chatMessages.length === 0 ? (
                          <div className="text-center py-8 text-gray-500">
                            <MessageCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                            <p>Ask me anything about this lesson!</p>
                            <p className="text-sm">I can help explain concepts, provide examples, or answer your questions.</p>
                          </div>
                        ) : (
                          chatMessages.map((message) => (
                            <div
                              key={message.id}
                              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                              <div
                                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                                  message.type === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-200 text-gray-800'
                                }`}
                              >
                                <p className="text-sm">{message.content}</p>
                                <p className={`text-xs mt-1 ${
                                  message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                                }`}>
                                  {message.timestamp.toLocaleTimeString()}
                                </p>
                              </div>
                            </div>
                          ))
                        )}
                      </div>

                      {/* Chat Input */}
                      <form onSubmit={handleChatSubmit} className="flex space-x-2">
                        <input
                          type="text"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          placeholder="Ask a question about this lesson..."
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled={isSendingMessage}
                        />
                        <button
                          type="submit"
                          disabled={!chatInput.trim() || isSendingMessage}
                          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isSendingMessage ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            <Send className="h-4 w-4" />
                          )}
                        </button>
                      </form>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'assessments' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Assessments</h2>
                  <p className="text-gray-600">Test your knowledge and track your progress.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Assessments Coming Soon</h3>
                      <p className="text-gray-600">Interactive assessments will be available here.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'chatbot' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">AI Tutor</h2>
                  <p className="text-gray-600">Get help and ask questions about {selectedSubject}.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">AI Tutor Coming Soon</h3>
                      <p className="text-gray-600">Your intelligent learning assistant will be available here.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'progress' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Progress Tracking</h2>
                  <p className="text-gray-600">Monitor your learning progress and achievements.</p>
                </div>
                
                <div className="card">
                  <div className="card-content">
                    <div className="text-center py-12">
                      <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Progress Analytics Coming Soon</h3>
                      <p className="text-gray-600">Detailed progress tracking will be available here.</p>
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
