# AI Personal Finance Tracker

An AI-powered personal finance tracking and analytics platform built with FastAPI, Next.js, PostgreSQL, and Redis.

## 🚀 Features

- **Smart Upload**: Upload PDF, CSV, or Excel bank statements
- **AI Categorization**: Automatic transaction categorization using ML
- **Visual Analytics**: Beautiful charts and spending insights
- **Budget Tracking**: Set and monitor budgets by category
- **AI Insights**: Personalized recommendations to optimize spending
- **Bank-Level Security**: Encrypted data with JWT authentication

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Cache**: Redis
- **Authentication**: JWT tokens with refresh mechanism
- **ML**: scikit-learn for categorization

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React Query + Zustand
- **Charts**: Recharts

## 📁 Project Structure

```
finance-tracker/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── parsers/       # File parsers
│   │   ├── ml/            # ML components
│   │   ├── security/      # Auth & encryption
│   │   └── middleware/    # Custom middleware
│   ├── alembic/           # Database migrations
│   └── tests/             # Backend tests
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities
│   │   ├── hooks/         # Custom hooks
│   │   └── types/         # TypeScript types
│   └── public/            # Static assets
└── docker-compose.yml     # Container orchestration
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/finance-tracker.git
cd finance-tracker
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
# Edit .env with your settings
```

3. Start all services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your local settings

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

## 📝 API Documentation

Once the backend is running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/auth/login` | POST | User authentication |
| `/api/v1/transactions` | GET | List transactions |
| `/api/v1/transactions` | POST | Create transaction |
| `/api/v1/upload` | POST | Upload statement |
| `/api/v1/analytics/summary` | GET | Spending summary |
| `/api/v1/analytics/insights` | GET | AI insights |

## 🔒 Security

- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- Sensitive data encryption with AES
- Rate limiting on API endpoints
- CORS configuration
- Input validation with Pydantic

## 🧪 Testing

### Backend
```bash
cd backend
pytest --cov=app tests/
```

### Frontend
```bash
cd frontend
npm run test
```

## 📊 Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Reset database
docker-compose down -v
docker-compose up -d
```
