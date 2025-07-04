# AI Personal Trainer

An AI-powered personal training application that helps users create customized workout plans and track their fitness progress.

## Project Structure

```
ai-personal-trainer/
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend service
├── database/          # Database schemas and migrations
├── scripts/           # Utility scripts
├── tests/             # Test suites
├── docs/              # Documentation
├── LICENSE            # MIT License
└── README.md          # This file
```

## Getting Started

This is a monorepo containing both frontend and backend components of the AI Personal Trainer application.

### Frontend (Next.js)
- Located in `/frontend`
- React-based user interface
- TypeScript support

### Backend (FastAPI)
- Located in `/backend`
- Python-based API service
- Async/await support

### Development

1. Clone the repository
2. Copy the environment template: `cp .env.example .env`
3. Edit `.env` and populate with your actual values
4. Set up frontend dependencies in `/frontend`
5. Set up backend dependencies in `/backend`
6. Configure database connection
7. Run development servers

## License

This project is licensed under the MIT License - see the LICENSE file for details.
