# Coros Podcast Sync

A web-based podcast synchronization application for Coros running watches. Subscribe to podcasts, automatically download and convert episodes, and sync them to your watch via USB.

## Features

- **RSS Feed Management**: Subscribe to podcasts via RSS URL
- **Automatic Downloads**: Background downloads of new episodes
- **Audio Conversion**: Convert episodes to MP3 format (requires FFmpeg)
- **Smart Sync**: Auto-detect watch and sync with episode limits
- **Storage Management**: Monitor and manage local and watch storage
- **Web Interface**: Modern, responsive browser-based UI

## Prerequisites

- **Python 3.9-3.13**: Backend runtime (Note: Python 3.14+ is not yet supported due to dependency limitations)
- **Node.js 18+**: Frontend development
- **FFmpeg**: Audio conversion (install separately)
- **Coros Watch**: Connected via USB

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/adamstace/coros-podcast-sync.git
cd coros-podcast-sync/
```

### 2. Backend Setup

```bash
# Create virtual environment (use Python 3.13 or lower)
cd backend
python3.13 -m venv venv  # or python3.12, python3.11, etc.

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file (optional)
cp ../.env.example .env

# Run backend server
python -m app.main
```

The backend will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Project Structure

```
coros-podcast-sync/
├── backend/           # Python FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── models/   # Database models
│   │   ├── services/ # Business logic
│   │   ├── tasks/    # Background tasks
│   │   └── utils/    # Helper functions
│   └── requirements.txt
├── frontend/          # React TypeScript frontend
│   ├── src/
│   │   ├── api/      # API client
│   │   ├── components/
│   │   ├── pages/
│   │   └── types/
│   └── package.json
├── data/              # Runtime data (created automatically)
│   ├── episodes/     # Downloaded episodes
│   ├── converted/    # Converted MP3s
│   └── database.db   # SQLite database
└── logs/              # Application logs
```

## Usage

1. **Add Podcast**: Go to Podcasts page and enter an RSS feed URL
2. **Download Episodes**: Episodes will auto-download based on settings
3. **Connect Watch**: Plug in your Coros watch via USB
4. **Sync**: Episodes will automatically sync to watch Music folder
5. **Manage**: Configure episode limits, storage, and sync settings

## Watch Detection

The app automatically detects your Coros watch when connected via USB. The watch appears as a mass storage device with a "Music" folder.

**Supported Detection:**
- macOS: Scans `/Volumes`
- Windows: Scans drive letters
- Linux: Scans `/media`

You can also manually configure the watch mount path in Settings.

## Configuration

Edit `.env` file or configure via Settings page:

- **Episode Limit**: Number of episodes to keep per podcast (default: 5)
- **Auto Download**: Automatically download new episodes
- **Check Interval**: How often to check for new episodes (minutes)
- **Audio Bitrate**: MP3 conversion bitrate (default: 128k)
- **Auto Sync**: Automatically sync when watch is connected

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
python -m app.main
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

```bash
# Frontend
cd frontend
npm run build

# Backend (standalone)
cd backend
pip install pyinstaller
pyinstaller --onefile app/main.py
```

## Troubleshooting

**Watch not detected:**
- Ensure watch is connected via USB and mounted
- Check that Music folder exists on the watch
- Try manually setting watch path in Settings

**Audio conversion fails:**
- Verify FFmpeg is installed: `ffmpeg -version`
- Check FFmpeg is in system PATH

**Downloads fail:**
- Check internet connection
- Verify RSS feed URL is valid
- Check available disk space

## API Documentation

When the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## License

MIT

## Contributing

This is a personal project for Coros watch users. Contributions welcome!
