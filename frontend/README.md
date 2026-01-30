# TrendRadar.Sol Frontend

React frontend for TrendRadar.Sol - Real-time Solana meme coin intelligence. Built with Vite, React, and TailwindCSS.

## Tech Stack

- React 18.2
- Vite 5.0 - Fast build tool and dev server
- React Router DOM - Client-side routing
- TanStack Query (React Query) - Data fetching and caching
- Recharts - Data visualization
- TailwindCSS - Utility-first CSS framework
- Lucide React - Icon library

## Prerequisites

- Node.js 18+ and npm/yarn/pnpm

## Installation

```bash
cd frontend
npm install
```

## Environment Variables

Create a `.env` file in the frontend directory (optional):

```bash
# API endpoint - defaults to http://localhost:8000 if not set
VITE_API_URL=http://localhost:8000
```

## Development

Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` by default.

## Build

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Linting

Run ESLint:

```bash
npm run lint
```

## Project Structure

```
src/
├── api/          # API client and data fetching functions
├── components/   # Reusable React components
├── pages/        # Page components (routes)
├── hooks/        # Custom React hooks
├── utils/        # Utility functions
└── mock/         # Mock data for development
```

## Features

- Real-time trend tracking with automatic updates
- Visual category emojis for quick identification
- Interactive charts and visualizations using Recharts
- Category-based trend filtering with acceleration scores
- Responsive design with TailwindCSS
- Graceful fallback to mock data when API is unavailable
- Client-side routing with React Router

## API Integration

The frontend connects to the FastAPI backend at the URL specified in `VITE_API_URL`. If the backend is unavailable, it automatically falls back to mock data for development purposes.

Key API endpoints used:
- `GET /api/trends` - Get trending categories with emojis and acceleration scores
- `GET /api/trends/{category}/{sub_category}/coins` - Get coins for a trend
- `GET /api/history/{category}/{sub_category}` - Get historical trend data
- `GET /api/acceleration/top` - Get top accelerating trends
- `POST /api/trigger-snapshot` - Manually trigger data snapshot and aggregation
