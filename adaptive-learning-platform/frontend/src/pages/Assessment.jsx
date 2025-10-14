import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { LoadingSpinner } from '../components/Common/LoadingSpinner'
import { ArrowLeft, Clock, CheckCircle, XCircle } from 'lucide-react'

export const Assessment = () => {
  const { subject, topic } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState({})
  const [timeRemaining, setTimeRemaining] = useState(600) // 10 minutes
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [results, setResults] = useState(null)

  // Mock questions for demonstration
  const questions = [
    {
      id: 1,
      type: 'mcq',
      question: 'What is 15 + 27?',
      options: ['40', '42', '44', '46'],
      correct: '42',
      points: 1
    },
    {
      id: 2,
      type: 'short_answer',
      question: 'Solve for x: 2x + 5 = 13',
      correct: '4',
      points: 2
    },
    {
      id: 3,
      type: 'problem_solving',
      question: 'A student in Freetown has 500 Leone. If a notebook costs 75 Leone, how many notebooks can they buy?',
      correct: '6',
      points: 3
    }
  ]

  const handleAnswerChange = (questionId, answer) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }))
  }

  const handleSubmit = async () => {
    setLoading(true)
    
    // Simulate API call
    setTimeout(() => {
      const score = Math.floor(Math.random() * 40) + 60 // Random score between 60-100
      setResults({
        score,
        totalQuestions: questions.length,
        correctAnswers: Math.floor((score / 100) * questions.length),
        timeTaken: 600 - timeRemaining
      })
      setIsSubmitted(true)
      setLoading(false)
    }, 2000)
  }

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1)
    }
  }

  // Timer effect
  React.useEffect(() => {
    if (timeRemaining > 0 && !isSubmitted) {
      const timer = setTimeout(() => {
        setTimeRemaining(prev => prev - 1)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [timeRemaining, isSubmitted])

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (isSubmitted && results) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="card">
            <div className="card-content text-center py-12">
              <div className="mb-6">
                {results.score >= 80 ? (
                  <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                ) : (
                  <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                )}
              </div>
              
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Assessment Complete!
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-primary-50 rounded-lg p-6">
                  <p className="text-2xl font-bold text-primary-600">{results.score}%</p>
                  <p className="text-sm text-gray-600">Final Score</p>
                </div>
                
                <div className="bg-secondary-50 rounded-lg p-6">
                  <p className="text-2xl font-bold text-secondary-600">{results.correctAnswers}/{results.totalQuestions}</p>
                  <p className="text-sm text-gray-600">Correct Answers</p>
                </div>
                
                <div className="bg-accent-50 rounded-lg p-6">
                  <p className="text-2xl font-bold text-accent-600">{formatTime(results.timeTaken)}</p>
                  <p className="text-sm text-gray-600">Time Taken</p>
                </div>
              </div>
              
              <div className="space-y-4">
                <button
                  onClick={() => navigate('/student')}
                  className="btn-primary btn-lg"
                >
                  Back to Dashboard
                </button>
                
                <button
                  onClick={() => {
                    setCurrentQuestion(0)
                    setAnswers({})
                    setTimeRemaining(600)
                    setIsSubmitted(false)
                    setResults(null)
                  }}
                  className="btn-outline btn-lg ml-4"
                >
                  Retake Assessment
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/student')}
              className="btn-ghost btn-sm flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back</span>
            </button>
            
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {subject} Assessment
              </h1>
              <p className="text-gray-600">Topic: {topic}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-red-50 px-3 py-2 rounded-lg">
              <Clock className="h-4 w-4 text-red-600" />
              <span className="text-sm font-medium text-red-600">
                {formatTime(timeRemaining)}
              </span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentQuestion + 1} of {questions.length}</span>
            <span>{Math.round(((currentQuestion + 1) / questions.length) * 100)}% Complete</span>
          </div>
          <div className="progress">
            <div 
              className="progress-bar" 
              style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question Card */}
        <div className="card mb-8">
          <div className="card-content">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {questions[currentQuestion].question}
              </h3>
              
              {questions[currentQuestion].type === 'mcq' && (
                <div className="space-y-3">
                  {questions[currentQuestion].options.map((option, index) => (
                    <label key={index} className="flex items-center space-x-3 cursor-pointer">
                      <input
                        type="radio"
                        name={`question-${questions[currentQuestion].id}`}
                        value={option}
                        checked={answers[questions[currentQuestion].id] === option}
                        onChange={(e) => handleAnswerChange(questions[currentQuestion].id, e.target.value)}
                        className="h-4 w-4 text-primary-600"
                      />
                      <span className="text-gray-700">{option}</span>
                    </label>
                  ))}
                </div>
              )}
              
              {questions[currentQuestion].type === 'short_answer' && (
                <textarea
                  value={answers[questions[currentQuestion].id] || ''}
                  onChange={(e) => handleAnswerChange(questions[currentQuestion].id, e.target.value)}
                  className="textarea"
                  rows={3}
                  placeholder="Enter your answer..."
                />
              )}
              
              {questions[currentQuestion].type === 'problem_solving' && (
                <textarea
                  value={answers[questions[currentQuestion].id] || ''}
                  onChange={(e) => handleAnswerChange(questions[currentQuestion].id, e.target.value)}
                  className="textarea"
                  rows={5}
                  placeholder="Show your work and provide the final answer..."
                />
              )}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <button
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            className="btn-outline btn-md"
          >
            Previous
          </button>
          
          <div className="flex space-x-4">
            {currentQuestion === questions.length - 1 ? (
              <button
                onClick={handleSubmit}
                disabled={loading || Object.keys(answers).length < questions.length}
                className="btn-primary btn-md"
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <LoadingSpinner size="sm" />
                    <span>Submitting...</span>
                  </div>
                ) : (
                  'Submit Assessment'
                )}
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="btn-primary btn-md"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


