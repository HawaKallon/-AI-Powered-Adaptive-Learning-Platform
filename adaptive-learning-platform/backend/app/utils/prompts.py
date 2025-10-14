"""
LLM Prompt Templates for Content Generation
Contains all prompt templates for different types of content generation
"""

from typing import Dict, Any, List
from datetime import datetime


class PromptTemplates:
    """Collection of prompt templates for different content generation tasks"""
    
    # Base system prompt for Sierra Leone context
    BASE_SYSTEM_PROMPT = """You are an AI tutor for Sierra Leonean students. You create educational content that is:
1. Culturally relevant to Sierra Leone (use local names, places, currency - Leone, examples from Freetown, Bo, Kenema, etc.)
2. Age-appropriate for the specified grade level
3. Clear and engaging
4. Aligned with the Sierra Leone curriculum
5. Encouraging and supportive in tone

Always use examples that students in Sierra Leone can relate to, such as local markets, traditional foods, local landmarks, and cultural practices."""

    @staticmethod
    def lesson_generation_prompt(student_profile: Dict[str, Any], topic: str, 
                               curriculum_context: str) -> str:
        """Generate a prompt for creating personalized lessons"""
        
        grade = student_profile.get('grade', 8)
        reading_level = student_profile.get('reading_level', 'intermediate')
        learning_pace = student_profile.get('learning_pace', 'moderate')
        subject = student_profile.get('subject', 'mathematics')
        
        # Adjust complexity based on reading level
        complexity_map = {
            'basic': 'Use simple words and short sentences. Include many examples.',
            'intermediate': 'Use clear explanations with some technical terms explained.',
            'advanced': 'Can use more sophisticated language and concepts.'
        }
        
        # Adjust pace based on learning pace
        pace_map = {
            'slow': 'Break concepts into smaller steps. Provide more practice examples.',
            'moderate': 'Provide balanced explanation and examples.',
            'fast': 'Can cover more ground but ensure understanding is maintained.'
        }
        
        return f"""{PromptTemplates.BASE_SYSTEM_PROMPT}

Create a personalized lesson for a Grade {grade} student in {subject} on the topic: "{topic}"

Student Profile:
- Grade: {grade}
- Reading Level: {reading_level} ({complexity_map.get(reading_level, 'intermediate')})
- Learning Pace: {learning_pace} ({pace_map.get(learning_pace, 'moderate')})
- Subject: {subject}

Curriculum Context:
{curriculum_context}

Please create a lesson that includes:
1. A clear, engaging title
2. Learning objectives (2-3 specific goals)
3. Main content explanation with Sierra Leone examples
4. 2-3 worked examples relevant to Sierra Leone
5. Key points summary
6. Estimated time to complete (in minutes)

Format your response as JSON with this structure:
{{
    "title": "Lesson title",
    "objectives": ["objective1", "objective2", "objective3"],
    "content": "Main lesson content with Sierra Leone examples",
    "examples": [
        {{
            "title": "Example 1 title",
            "problem": "Problem statement with Sierra Leone context",
            "solution": "Step-by-step solution",
            "explanation": "Why this approach works"
        }}
    ],
    "key_points": ["point1", "point2", "point3"],
    "estimated_time": 25
}}"""

    @staticmethod
    def exercise_generation_prompt(student_profile: Dict[str, Any], topic: str, 
                                 difficulty: str, curriculum_context: str) -> str:
        """Generate a prompt for creating exercises"""
        
        grade = student_profile.get('grade', 8)
        subject = student_profile.get('subject', 'mathematics')
        mastery_level = student_profile.get('mastery_level', 50)
        
        # Adjust difficulty based on mastery level
        if mastery_level < 40:
            difficulty_adjustment = "Create easier questions with more scaffolding and hints."
        elif mastery_level > 80:
            difficulty_adjustment = "Create challenging questions that extend understanding."
        else:
            difficulty_adjustment = "Create questions at the student's current level with some challenge."
        
        return f"""{PromptTemplates.BASE_SYSTEM_PROMPT}

Create {difficulty} difficulty exercises for a Grade {grade} student in {subject} on the topic: "{topic}"

Student Profile:
- Grade: {grade}
- Subject: {subject}
- Current Mastery Level: {mastery_level}%
- Difficulty: {difficulty}

Curriculum Context:
{curriculum_context}

{difficulty_adjustment}

Create 5 exercises with these question types:
1. Multiple Choice (1 question)
2. Short Answer (2 questions)
3. Problem Solving (2 questions)

Each question should:
- Use Sierra Leone context and examples
- Be appropriate for the grade level
- Include clear instructions
- Have a detailed solution with explanation
- Include hints for struggling students

Format your response as JSON:
{{
    "exercises": [
        {{
            "question": "Question text with Sierra Leone context",
            "type": "mcq|short_answer|problem_solving",
            "options": ["A", "B", "C", "D"] (only for MCQ),
            "correct_answer": "Correct answer",
            "explanation": "Detailed explanation of the solution",
            "hints": ["hint1", "hint2"],
            "difficulty": "{difficulty}",
            "points": 1
        }}
    ],
    "total_points": 5,
    "estimated_time": 20
}}"""

    @staticmethod
    def chatbot_response_prompt(student_profile: Dict[str, Any], user_message: str,
                              context: Dict[str, Any], relevant_content: List[str]) -> str:
        """Generate a prompt for chatbot responses"""
        
        grade = student_profile.get('grade', 8)
        subject = context.get('current_subject', 'mathematics')
        topic = context.get('current_topic', 'general')
        recent_mistakes = context.get('recent_mistakes', [])
        
        # Build context about recent mistakes
        mistakes_context = ""
        if recent_mistakes:
            mistakes_context = f"\nRecent areas where the student struggled: {', '.join(recent_mistakes)}"
        
        # Build relevant content context
        content_context = "\n".join([f"- {content}" for content in relevant_content[:3]])
        
        return f"""{PromptTemplates.BASE_SYSTEM_PROMPT}

You are a helpful AI tutor chatting with a Grade {grade} student in Sierra Leone.

Student Context:
- Grade: {grade}
- Current Subject: {subject}
- Current Topic: {topic}
{mistakes_context}

Relevant Curriculum Content:
{content_context}

Student's Question: "{user_message}"

Please provide a helpful, encouraging response that:
1. Directly answers the student's question
2. Uses Sierra Leone examples when relevant
3. Explains concepts in simple, age-appropriate language
4. Offers additional help or related topics
5. Is encouraging and supportive

If the student seems confused, offer to break down the concept further or provide more examples.

Format your response as JSON:
{{
    "response": "Your helpful response to the student",
    "suggested_actions": ["action1", "action2"],
    "related_topics": ["topic1", "topic2"],
    "confidence_score": 0.85
}}"""

    @staticmethod
    def diagnostic_assessment_prompt(grade: int, subject: str) -> str:
        """Generate a prompt for diagnostic assessments"""
        
        return f"""{PromptTemplates.BASE_SYSTEM_PROMPT}

Create a diagnostic assessment for a Grade {grade} student in {subject} to determine their baseline proficiency level.

The assessment should:
1. Cover fundamental concepts for Grade {grade} {subject}
2. Include questions of varying difficulty (easy, medium, hard)
3. Use Sierra Leone context and examples
4. Help identify the student's reading level and learning pace
5. Take approximately 15-20 minutes to complete

Create 10 questions with this distribution:
- 4 Easy questions (basic concepts)
- 4 Medium questions (intermediate concepts)  
- 2 Hard questions (advanced concepts)

Question types should include:
- Multiple choice (4 questions)
- Short answer (4 questions)
- Problem solving (2 questions)

Format your response as JSON:
{{
    "assessment_title": "Grade {grade} {subject} Diagnostic Assessment",
    "instructions": "Clear instructions for the student",
    "questions": [
        {{
            "question": "Question text with Sierra Leone context",
            "type": "mcq|short_answer|problem_solving",
            "options": ["A", "B", "C", "D"] (only for MCQ),
            "correct_answer": "Correct answer",
            "explanation": "Brief explanation",
            "difficulty": "easy|medium|hard",
            "points": 1
        }}
    ],
    "total_points": 10,
    "time_limit": 20
}}"""

    @staticmethod
    def adaptive_difficulty_prompt(performance_data: Dict[str, Any], 
                                 current_topic: str) -> str:
        """Generate a prompt for adaptive difficulty adjustment"""
        
        recent_scores = performance_data.get('recent_scores', [])
        average_score = sum(recent_scores) / len(recent_scores) if recent_scores else 50
        attempt_count = performance_data.get('attempt_count', 1)
        
        return f"""{PromptTemplates.BASE_SYSTEM_PROMPT}

Analyze the student's performance and recommend appropriate next steps.

Performance Data:
- Recent Scores: {recent_scores}
- Average Score: {average_score:.1f}%
- Attempt Count: {attempt_count}
- Current Topic: {current_topic}

Based on this performance, recommend:
1. Next difficulty level (easier, same, harder)
2. Specific areas that need remediation
3. Suggested learning activities
4. Estimated time for next session

Format your response as JSON:
{{
    "recommended_difficulty": "easier|same|harder",
    "remediation_areas": ["area1", "area2"],
    "suggested_activities": ["activity1", "activity2"],
    "next_session_time": 25,
    "reasoning": "Explanation of the recommendation"
}}"""

    @staticmethod
    def content_explanation_prompt(concept: str, grade: int, subject: str,
                                 student_question: str = "") -> str:
        """Generate a prompt for explaining concepts"""
        
        return f"""{PromptTemplates.BASE_SYSTEM_PROMPT}

Explain the concept "{concept}" to a Grade {grade} student in {subject}.

Student's specific question: "{student_question}" (if provided)

Your explanation should:
1. Start with a simple, relatable definition
2. Use Sierra Leone examples and analogies
3. Break down complex ideas into smaller parts
4. Include a practical example the student can relate to
5. End with a summary of key points
6. Be encouraging and supportive

Format your response as JSON:
{{
    "explanation": "Clear, step-by-step explanation with Sierra Leone context",
    "example": "Practical example from Sierra Leone",
    "key_points": ["point1", "point2", "point3"],
    "follow_up_questions": ["question1", "question2"]
}}"""


# Utility function to get the appropriate prompt
def get_prompt(prompt_type: str, **kwargs) -> str:
    """Get a specific prompt template with parameters"""
    
    prompt_map = {
        'lesson_generation': PromptTemplates.lesson_generation_prompt,
        'exercise_generation': PromptTemplates.exercise_generation_prompt,
        'chatbot_response': PromptTemplates.chatbot_response_prompt,
        'diagnostic_assessment': PromptTemplates.diagnostic_assessment_prompt,
        'adaptive_difficulty': PromptTemplates.adaptive_difficulty_prompt,
        'content_explanation': PromptTemplates.content_explanation_prompt
    }
    
    if prompt_type not in prompt_map:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    return prompt_map[prompt_type](**kwargs)

