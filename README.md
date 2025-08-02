# SpotDL Web

## ⚠️ Warning

This project was developed using AI assistance (Claude + ChatGPT). While it has been manually reviewed, **do not blindly trust the code**. The SpotDL section currently doesn't work properly due to yt-dlp errors that I haven't been able to resolve (likely related to the spotdl library itself). I couldn't find a working version, so I left it as-is given my current needs. If someone needs this functionality, I might continue development and potentially build a version for Docker Hub or GitHub Container Registry.

## Description

SpotDL Web is a modern web application that provides a user-friendly interface for downloading music from Spotify and YouTube. It features:

- **Dual Download Methods**: Supports both Spotify (via spotdl) and YouTube (via yt-dlp)
- **Queue Management**: Cumulative queue system with detailed status tracking (waiting, in progress, completed, failed)
- **Cookie Support**: Upload and manage authentication cookies for premium content access
- **Real-time Status**: Live updates on download progress and queue status
- **Modern UI**: Dark mode interface with animations and responsive design
- **REST API**: Full API for programmatic access

The application automatically detects URL types and uses the appropriate download method:
- Spotify URLs (`open.spotify.com`) → spotdl
- YouTube URLs (`youtube.com`, `music.youtube.com`, `youtu.be`) → yt-dlp

## Features

- **Smart URL Detection**: Automatically chooses the right downloader based on URL type
- **High Quality Downloads**: Uses best available audio quality without artificial upsampling
- **Metadata & Thumbnails**: Full metadata embedding including cover art and track information
- **Queue System**: Add multiple URLs and track their download status
- **Cookie Management**: Support for YouTube Premium cookies to access premium content
- **Docker Ready**: Easy deployment with Docker and docker-compose

## Installation & Usage

### Prerequisites

- Docker and Docker Compose
- Git

### Quick Start

#### Production (Using Pre-built Image)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SamueleOrazioDurante/spotdl-web.git
   cd spotdl-web
   ```

2. **Start the application:**
   ```bash
   docker-compose up -d
   ```

3. **Access the web interface:**
   Open your browser and navigate to `http://localhost:8000`

#### Development (Build from Source)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SamueleOrazioDurante/spotdl-web.git
   cd spotdl-web
   ```

2. **Start in development mode:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

### Usage Commands

#### Production Operations

```bash
# Start the application (using pre-built image)
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Update to latest image
docker-compose pull && docker-compose up -d

# Remove everything (including volumes)
docker-compose down -v
```

#### Development Operations

```bash
# Start in development mode (build from source)
docker-compose -f docker-compose.dev.yml up -d

# Rebuild after code changes
docker-compose -f docker-compose.dev.yml up --build -d

# View development logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop development environment
docker-compose -f docker-compose.dev.yml down
```

#### API Testing

```bash
# Access backend API directly
curl http://localhost:8000/queue-status

# Upload cookies via API
curl -X POST -F "file=@cookies.txt" http://localhost:8000/upload-cookie
```

### Directory Structure

```
spotdl-web/
├── backend/           # FastAPI backend
│   ├── main.py       # Main application
│   └── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   └── package.json
├── config/          # Cookie storage (created at runtime)
├── music/           # Downloaded music files (created at runtime)
├── docker-compose.dev.yml
├── docker-compose.yml
└── Dockerfile
```

### API Endpoints

- `POST /add-downloads` - Add URLs to download queue
- `GET /queue-status` - Get current queue status
- `POST /upload-cookie` - Upload authentication cookies
- `GET /cookie-status` - Check cookie file status
- `DELETE /clear-queue` - Clear completed/failed items
- `DELETE /remove-item/{id}` - Remove specific item

### Configuration

#### Docker Images

- **Production**: Uses pre-built image from `ghcr.io/samueleoraziodurante/spotdl-web:latest`
- **Development**: Builds from source using `docker-compose.dev.yml`

```
services:
  app:
    image: ghcr.io/samueleoraziodurante/spotdl-web:latest
    ports:
      - "8000:8000"
    volumes:
      - ./config:/config
      - ./music:/music
    restart: unless-stopped
```

### Contributing

Feel free to submit issues, fork the repository, and create pull requests. Any contributions are welcome!

### License

This project is open source. Please check the LICENSE file for details.
