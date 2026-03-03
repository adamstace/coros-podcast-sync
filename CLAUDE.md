# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Coros Podcast Sync is a web application that allows users to subscribe to podcasts via RSS feeds, automatically download episodes, convert them to MP3 format, and sync them to Coros watches over USB mass storage.

## Tech Stack

**Backend:**
- Python 3.9–3.13 (3.14 not supported due to pydantic-core/PyO3 incompatibility)
- FastAPI for REST API
- SQLite + SQLAlchemy for database
- httpx for HTTP requests
- feedparser for RSS parsing
- APScheduler for background tasks
- ffmpeg-python + external FFmpeg for audio conversion

**Frontend:**
- React 18 + TypeScript
- Vite 5 for build tooling
- React Router v6 for routing
- TanStack React Query for data fetching
- Axios for HTTP client
- Recharts for data visualization

**Real-time Communication:**
- WebSocket for download/sync progress updates

## Architecture

Browser (React UI) → REST + WebSocket → FastAPI → Services → SQLite + local files + watch USB drive

**Important Constraints:**
- Backend and Frontend are separate applications
- Backend runs on `http://localhost:8000`
- Frontend UI runs on `http://localhost:5173`
- Watch detection uses USB mass storage scanning (no proprietary protocol)

## Key Features (All Implemented)

- RSS feed management with episode limits
- Auto-download of new episodes
- Download queue with progress tracking, cancel, and resume
- MP3 conversion with configurable bitrate
- USB watch detection and sync with cleanup
- Storage monitoring and cleanup
- Settings UI and API

## Default Paths & Settings

- Database: `backend/data/database.db`
- Episode files: `backend/data/episodes/`
- Converted files: `backend/data/converted/`
- Logs: `backend/logs/app.log`
- Default episode limit: 5 episodes per podcast
- Default bitrate: 128kbps
- Check interval: 60 minutes

## Development Commands

**Backend:**
```bash
cd backend
source venv/bin/activate
python -m app.main
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Overview

- **Podcasts**: `/api/podcasts` (CRUD operations + refresh)
- **Episodes**: `/api/episodes` (list/detail/download/cancel/delete/convert)
- **Sync**: `/api/sync/*` (status, start, history, watch detect/info)
- **Storage**: `/api/storage/*` (local storage, by-podcast, cleanup)
- **Settings**: `/api/settings` (get/update/reset)
- **WebSocket**: `/ws/downloads`, `/ws/sync`

## Project Status

All feature phases are complete. Testing with real Coros hardware remains optional.
