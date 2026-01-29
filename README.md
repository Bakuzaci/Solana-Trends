# Solana Meme Coin Trend Dashboard

A real-time dashboard for tracking and analyzing trends in Solana meme coins. Automatically categorizes new tokens, detects emerging trends, and identifies breakout metas using advanced acceleration metrics and clustering algorithms.

## Overview

This project monitors Solana tokens (primarily from PumpFun exchange), categorizes them using fuzzy string matching, tracks their market metrics over time, and detects trending categories and breakout metas. It consists of:

- **Backend**: FastAPI application with SQLite database, background job scheduler, and Moralis API integration
- **Frontend**: React SPA with real-time trend visualization and interactive charts

## Features

- **Automatic Token Categorization**: Uses fuzzy string matching (rapidfuzz) to categorize tokens into themes like Animals, Meme Culture, Pop Culture, Technology, Finance, etc.
- **Trend Acceleration Scoring**: Calculates acceleration metrics based on coin count growth, market cap velocity, and statistical breakout detection
- **Breakout Meta Detection**: Identifies emerging trend clusters using DBSCAN algorithm
- **Real-time Updates**: Background scheduler fetches new tokens every 15 minutes (configurable)
- **Historical Tracking**: Stores snapshots for trend analysis over multiple time windows (12h, 24h, 7d)
- **Mock Data Mode**: Works without Moralis API key using generated mock data for development

## Project Structure

```
Solana-Trends/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API endpoints (trends, acceleration, history)
│   │   ├── services/  # Business logic (data collection, categorization, acceleration)
│   │   ├── tasks/     # Background jobs (scheduler, aggregation)
│   │   ├── models.py  # SQLAlchemy models
│   │   ├── schemas.py # Pydantic schemas
│   │   ├── config.py  # Configuration settings
│   │   ├── database.py # Database setup
│   │   └── main.py    # FastAPI application
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/          # React frontend
    ├── src/
    │   ├── api/       # API client
    │   ├── components/# React components
    │   ├── hooks/     # React Query hooks
    │   └── mock/      # Mock data
    ├── package.json
    └── vite.config.js
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- Moralis API key (optional - uses mock data if not provided)

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Moralis API key (optional)
uvicorn app.main:app --reload
```

API available at http://localhost:8000 (docs at /docs)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at http://localhost:5173

## Environment Variables

### Backend (.env)
```bash
MORALIS_API_KEY=your_moralis_api_key_here  # Optional
DATABASE_URL=sqlite+aiosqlite:///./solana_trends.db
SNAPSHOT_INTERVAL_MINUTES=15
FRONTEND_URL=http://localhost:5173
DEBUG=false
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

## API Endpoints

- `GET /api/trends` - Get all trending categories
- `GET /api/trends/{category}/{sub_category}/coins` - Get coins for a specific trend
- `GET /api/acceleration/top` - Get top accelerating trends
- `GET /api/history/{category}/{sub_category}` - Get historical trend data
- `GET /health` - Health check

## Technology Stack

### Backend
- FastAPI, SQLAlchemy, Pydantic, APScheduler
- httpx, rapidfuzz, scikit-learn

### Frontend
- React 18, Vite, TailwindCSS
- TanStack Query, Recharts, React Router

## License

MIT
