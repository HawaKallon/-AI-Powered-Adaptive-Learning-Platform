import React, { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, BookOpen, Search, Loader2 } from 'lucide-react'
import { lessonsAPI } from '../../services/api'

export const CurriculumTopics = ({ subject, grade, onTopicSelect }) => {
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedTopics, setExpandedTopics] = useState({})
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTopic, setSelectedTopic] = useState(null)
  const [topicDetails, setTopicDetails] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  // Load topics when subject or grade changes
  useEffect(() => {
    if (subject && grade) {
      loadTopics()
    }
  }, [subject, grade])

  const loadTopics = async () => {
    setLoading(true)
    try {
      const response = await lessonsAPI.getCurriculumTopics(subject, grade)
      if (response.data.success) {
        setTopics(response.data.topics)
        console.log(`Loaded ${response.data.topics.length} topics for ${subject} Grade ${grade}`)
      } else {
        console.error('Failed to load topics:', response.data.error)
        setTopics([])
      }
    } catch (error) {
      console.error('Error loading topics:', error)
      setTopics([])
    } finally {
      setLoading(false)
    }
  }

  const loadTopicDetails = async (topic) => {
    setLoadingDetails(true)
    try {
      const response = await lessonsAPI.getTopicDetails(topic, subject, grade)
      if (response.data.success) {
        setTopicDetails(response.data)
        console.log(`Loaded details for topic: ${topic}`)
      } else {
        console.error('Failed to load topic details:', response.data.error)
        setTopicDetails(null)
      }
    } catch (error) {
      console.error('Error loading topic details:', error)
      setTopicDetails(null)
    } finally {
      setLoadingDetails(false)
    }
  }

  const toggleTopicExpansion = (topicName) => {
    setExpandedTopics(prev => ({
      ...prev,
      [topicName]: !prev[topicName]
    }))
  }

  const handleTopicClick = (topic) => {
    setSelectedTopic(topic)
    loadTopicDetails(topic.topic)
    if (onTopicSelect) {
      onTopicSelect(topic)
    }
  }

  const handleSubtopicClick = (subtopic) => {
    if (onTopicSelect) {
      onTopicSelect({
        topic: subtopic,
        parentTopic: selectedTopic?.topic,
        subject,
        grade
      })
    }
  }

  // Filter topics based on search query
  const filteredTopics = topics.filter(topic => 
    topic.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
    topic.subtopics.some(subtopic => 
      subtopic.toLowerCase().includes(searchQuery.toLowerCase())
    )
  )

  if (loading) {
    return (
      <div className="card">
        <div className="card-content">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600 mr-2" />
            <span className="text-gray-600">Loading curriculum topics...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="card">
        <div className="card-content">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder={`Search ${subject} topics...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Topics List */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">
            {subject.charAt(0).toUpperCase() + subject.slice(1)} Topics - Grade {grade}
          </h3>
          <p className="text-sm text-gray-600">
            {filteredTopics.length} topics available
          </p>
        </div>
        <div className="card-content">
          {filteredTopics.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p>No topics found for {subject} Grade {grade}</p>
              <p className="text-sm">Try adjusting your search or check back later.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredTopics.map((topic, index) => (
                <div key={index} className="border border-gray-200 rounded-lg">
                  {/* Main Topic */}
                  <div
                    className={`p-4 cursor-pointer transition-colors ${
                      selectedTopic?.topic === topic.topic
                        ? 'bg-blue-50 border-blue-200'
                        : 'hover:bg-gray-50'
                    }`}
                    onClick={() => handleTopicClick(topic)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleTopicExpansion(topic.topic)
                          }}
                          className="p-1 hover:bg-gray-200 rounded"
                        >
                          {expandedTopics[topic.topic] ? (
                            <ChevronDown className="h-4 w-4 text-gray-600" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-gray-600" />
                          )}
                        </button>
                        <BookOpen className="h-4 w-4 text-blue-600" />
                        <div>
                          <h4 className="font-medium text-gray-900">{topic.topic}</h4>
                          {topic.description && (
                            <p className="text-sm text-gray-600 mt-1">
                              {topic.description.length > 100 
                                ? topic.description.substring(0, 100) + '...'
                                : topic.description
                              }
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        {topic.subtopics.length} subtopics
                      </div>
                    </div>
                  </div>

                  {/* Subtopics */}
                  {expandedTopics[topic.topic] && (
                    <div className="border-t border-gray-200 bg-gray-50">
                      <div className="p-4 space-y-2">
                        {topic.subtopics.map((subtopic, subIndex) => (
                          <div
                            key={subIndex}
                            className="flex items-center space-x-3 p-2 hover:bg-white rounded cursor-pointer transition-colors"
                            onClick={() => handleSubtopicClick(subtopic)}
                          >
                            <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                            <span className="text-sm text-gray-700">{subtopic}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Topic Details */}
      {selectedTopic && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedTopic.topic} Details
            </h3>
          </div>
          <div className="card-content">
            {loadingDetails ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-blue-600 mr-2" />
                <span className="text-gray-600">Loading topic details...</span>
              </div>
            ) : topicDetails ? (
              <div className="space-y-6">
                {/* Learning Objectives */}
                {topicDetails.objectives && topicDetails.objectives.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Learning Objectives</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                      {topicDetails.objectives.map((objective, index) => (
                        <li key={index}>{objective}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Key Concepts */}
                {topicDetails.key_concepts && topicDetails.key_concepts.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Key Concepts</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                      {topicDetails.key_concepts.map((concept, index) => (
                        <li key={index}>{concept}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Subtopics */}
                {topicDetails.subtopics && topicDetails.subtopics.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Subtopics</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {topicDetails.subtopics.map((subtopic, index) => (
                        <div
                          key={index}
                          className="p-2 bg-blue-50 rounded text-sm text-blue-800 cursor-pointer hover:bg-blue-100"
                          onClick={() => handleSubtopicClick(subtopic)}
                        >
                          {subtopic}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Content Preview */}
                {topicDetails.content_preview && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Content Preview</h4>
                    <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                      {topicDetails.content_preview}
                    </div>
                  </div>
                )}

                {/* Action Button */}
                <div className="pt-4 border-t">
                  <button
                    onClick={() => onTopicSelect && onTopicSelect(selectedTopic)}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Start Learning This Topic
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>Failed to load topic details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
