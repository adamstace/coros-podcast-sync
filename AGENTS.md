# AGENTS.md instructions for /Users/adams/repos/coros-podcast-sync

<INSTRUCTIONS>
## Project Overview
Coros Podcast Sync is a web app that lets users subscribe to podcasts via RSS, auto-download episodes, convert to MP3, and sync to Coros watches over USB mass storage.

## Tech Stack
- Backend: Python 3.9–3.13, FastAPI, SQLite + SQLAlchemy, httpx, feedparser, APScheduler
- Frontend: React 18 + TypeScript, Vite 5, React Router v6, TanStack React Query, Axios, Recharts
- Audio: ffmpeg-python + external FFmpeg install
- Realtime: WebSocket for download/sync progress

## Important Constraints
- Python 3.14 is not supported (pydantic-core/PyO3). Use 3.9–3.13.
- Backend/Frontend are separate: FastAPI on `http://localhost:8000`, UI on `http://localhost:5173`.
- Watch detection is USB mass storage scanning (no proprietary protocol).

## Architecture (High Level)
Browser (React UI) → REST + WebSocket → FastAPI → Services → SQLite + local files + watch USB drive.

## Key Features (All Implemented)
- RSS management, episode limits, auto-download
- Download queue with progress, cancel, resume
- MP3 conversion, configurable bitrate
- USB watch detection and sync with cleanup
- Storage monitoring and cleanup
- Settings UI and API

## Default Paths & Settings
- DB: `backend/data/database.db`
- Episode files: `backend/data/episodes/`
- Converted files: `backend/data/converted/`
- Logs: `backend/logs/app.log`
- Default episode limit: 5
- Default bitrate: 128kbps
- Check interval: 60 minutes

## Development Commands
Backend:
```bash
cd backend
source venv/bin/activate
python -m app.main
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```

## API Overview
Podcasts: `/api/podcasts` (CRUD + refresh)  
Episodes: `/api/episodes` (list/detail/download/cancel/delete/convert)  
Sync: `/api/sync/*` (status, start, history, watch detect/info)  
Storage: `/api/storage/*` (local, by-podcast, cleanup)  
Settings: `/api/settings` (get/update/reset)  
WebSocket: `/ws/downloads`, `/ws/sync`

## Status
All feature phases complete; testing with real hardware remains optional.
</INSTRUCTIONS>
