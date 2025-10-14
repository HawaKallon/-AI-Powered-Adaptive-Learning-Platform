# AI-Powered Adaptive Learning Platform for Sierra Leone

A comprehensive AI-powered adaptive learning platform that personalizes education for Sierra Leonean students in Mathematics, English, and Integrated Science (Grades 7-12). The system uses RAG (Retrieval-Augmented Generation) to generate personalized lessons, exercises, and provides an interactive chatbot for student questions.

## 🚀 Features

### Core Features
- **Personalized Learning**: AI-generated lessons tailored to each student's proficiency level, reading ability, and learning pace
- **Adaptive Assessments**: Dynamic difficulty adjustment based on student performance
- **RAG-Powered Chatbot**: Context-aware AI tutor with Sierra Leone-specific examples
- **Real-time Progress Tracking**: Mastery tracking and performance analytics
- **Teacher Dashboard**: Comprehensive monitoring and analytics for educators
- **Sierra Leone Context**: Local examples, currency (Leone), and cultural relevance

### Technical Features
- **Smart PDF Processing**: Intelligent chunking of curriculum documents
- **Vector Embeddings**: ChromaDB with sentence-transformers for semantic search
- **LLM Integration**: Content generation with fallback templates
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Modern Frontend**: React with Tailwind CSS and responsive design
- **Authentication**: JWT-based auth for students and teachers

## 🏗️ Architecture

```
adaptive-learning-platform/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── schemas/         # Pydantic schemas
│   │   └── utils/           # Helper functions
│   ├── scripts/             # Utility scripts
│   └── requirements.txt     # Python dependencies
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client
│   │   └── contexts/        # React contexts
│   └── package.json         # Node dependencies
└── data/                    # Curriculum PDFs
    ├── mathematics/
    ├── english/
    └── science/
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with pgvector extension
- **LLM**: Llama 3.2 8B-Instruct (via Hugging Face)
- **RAG**: sentence-transformers/all-MiniLM-L6-v2, ChromaDB
- **PDF Processing**: PyPDF2, pdfplumber
- **Authentication**: JWT with python-jose

### Frontend
- **Framework**: React 18.2.0
- **Styling**: Tailwind CSS 3.3.6
- **Routing**: React Router DOM 6.20.1
- **HTTP Client**: Axios 1.6.2
- **State Management**: React Query 3.39.3
- **Icons**: Lucide React 0.294.0

## 📋 Prerequisites

Before running the system, ensure you have:

1. **Python 3.11+** installed
2. **Node.js 18+** and npm installed
3. **PostgreSQL 14+** with pgvector extension
4. **Git** for version control

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd adaptive-learning-platform
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit .env file with your configuration
# Update DATABASE_URL, SECRET_KEY, etc.
```

### 3. Database Setup

```bash
# Install PostgreSQL and pgvector extension
# On Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-14-pgvector

# On macOS with Homebrew:
brew install postgresql
brew install pgvector

# Create database
sudo -u postgres psql
CREATE DATABASE adaptive_learning;
CREATE EXTENSION vector;
\q

# Run database setup script
python scripts/setup_database.py
```

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

### 5. Curriculum Data Setup

```bash
# Create data directories
mkdir -p data/mathematics data/english data/science

# Add your curriculum PDF files to the respective directories
# Example:
# data/mathematics/grade7_algebra.pdf
# data/english/grade8_grammar.pdf
# data/science/grade9_biology.pdf

# Ingest curriculum data
cd ../backend
python scripts/ingest_curriculum.py ingest --directory ../data
```

## 🏃‍♂️ Running the System

### 1. Start the Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 2. Start the Frontend

```bash
cd frontend

# Start the development server
npm run dev
```

The frontend will be available at: `http://localhost:3000`

### 3. Access the Application

1. **Student Login**: Use student ID to login
2. **Teacher Login**: Use email and password
3. **Registration**: Create new student or teacher accounts

## 📚 Usage Guide

### For Students

1. **Login**: Enter your student ID
2. **Dashboard**: View your learning progress and recommendations
3. **Lessons**: Access personalized lessons based on your level
4. **Assessments**: Take adaptive assessments to track progress
5. **AI Tutor**: Chat with the AI tutor for help and explanations

### For Teachers

1. **Login**: Use your email and password
2. **Dashboard**: Monitor class performance and analytics
3. **Students**: View individual student progress and mastery levels
4. **Content**: Manage lesson content and track usage
5. **Analytics**: Access detailed performance reports

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/adaptive_learning

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM
LLM_MODEL_NAME=microsoft/DialoGPT-medium
MAX_TOKENS=1000
TEMPERATURE=0.7

# RAG
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### Curriculum Ingestion

To add new curriculum content:

```bash
# Ingest single PDF
python scripts/ingest_curriculum.py ingest --file path/to/curriculum.pdf

# Ingest directory
python scripts/ingest_curriculum.py ingest --directory path/to/curriculum/

# Get ingestion statistics
python scripts/ingest_curriculum.py stats

# Reindex content
python scripts/ingest_curriculum.py reindex
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register/student` - Register student
- `POST /api/v1/auth/register/teacher` - Register teacher
- `POST /api/v1/auth/login/student` - Student login
- `POST /api/v1/auth/login/teacher` - Teacher login
- `GET /api/v1/auth/me` - Get current user

### Students
- `GET /api/v1/students/me` - Get student profile
- `PUT /api/v1/students/me` - Update student profile
- `GET /api/v1/students/me/mastery` - Get mastery levels
- `GET /api/v1/students/me/learning-path` - Get learning path

### Lessons
- `POST /api/v1/lessons/generate` - Generate personalized lesson
- `GET /api/v1/lessons/recommended` - Get recommended lessons
- `GET /api/v1/lessons/history` - Get lesson history

### Assessments
- `POST /api/v1/assessments/generate-exercise` - Generate exercises
- `POST /api/v1/assessments/submit` - Submit assessment
- `GET /api/v1/assessments/my-assessments` - Get assessment history

### Chatbot
- `POST /api/v1/chatbot/chat` - Send chat message
- `GET /api/v1/chatbot/history` - Get chat history
- `GET /api/v1/chatbot/suggested-questions` - Get suggested questions

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env
   - Verify pgvector extension is installed

2. **Port Already in Use**
   - Change ports in configuration
   - Kill existing processes: `lsof -ti:8000 | xargs kill`

3. **LLM Model Loading Error**
   - Check internet connection
   - Verify Hugging Face access
   - Fallback templates will be used automatically

4. **Frontend Build Error**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility

### Logs

- Backend logs: Check terminal output
- Frontend logs: Check browser console
- Database logs: Check PostgreSQL logs

## 🔒 Security Considerations

1. **Change default SECRET_KEY** in production
2. **Use HTTPS** in production
3. **Implement rate limiting** for API endpoints
4. **Validate file uploads** for curriculum PDFs
5. **Regular security updates** for dependencies

## 📈 Performance Optimization

1. **Database Indexing**: Ensure proper indexes on frequently queried columns
2. **Caching**: Implement Redis caching for frequently accessed data
3. **CDN**: Use CDN for static assets in production
4. **Load Balancing**: Implement load balancing for high traffic

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Sierra Leone Ministry of Education
- Hugging Face for LLM models
- FastAPI and React communities
- Open source contributors

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

---

**Built with ❤️ for Sierra Leone's education system**


