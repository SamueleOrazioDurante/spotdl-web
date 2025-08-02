from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import subprocess
import threading
import os
import time
import json
import uuid
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import re

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Download queue with detailed tracking
download_queue = []
queue_lock = threading.Lock()

# Directory configuration
CONFIG_DIR = "/config"
MUSIC_DIR = "/music"

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

class DownloadItem:
    def __init__(self, url, download_type):
        self.id = str(uuid.uuid4())
        self.url = url
        self.download_type = download_type  # 'spotify' or 'youtube'
        self.status = 'waiting'  # waiting, in_progress, completed, failed
        self.track_name = ''
        self.artist_name = ''
        self.error_message = ''
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

def detect_url_type(url):
    """Detect if URL is Spotify or YouTube"""
    if 'open.spotify.com' in url:
        return 'spotify'
    elif 'music.youtube.com' in url or 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    else:
        return 'unknown'

def extract_track_info(url, download_type):
    """Extract track information from URL"""
    if download_type == 'spotify':
        # For Spotify, we'll get the info during download
        return "Spotify Track", "Unknown Artist"
    elif download_type == 'youtube':
        # For YouTube, we could extract from title or get during download
        return "YouTube Video", "Unknown Artist"
    return "Unknown Track", "Unknown Artist"

def download_with_spotdl(item):
    """Download using spotdl for Spotify links"""
    try:
        cmd = [
            "spotdl",
            "--cookie-file", os.path.join(CONFIG_DIR, "cookies.txt"),
            "--format", "m4a",
            "--bitrate", "auto",
            "--lyrics", "genius",
            "--output", MUSIC_DIR,
            item.url
        ]
        
        result = subprocess.run(cmd, check=True, timeout=600, capture_output=True, text=True)
        
        # Try to extract track info from output if possible
        if result.stdout:
            # Parse spotdl output to get track name
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Downloaded' in line or 'Downloading' in line:
                    # Extract track info from line
                    parts = line.split(' - ')
                    if len(parts) >= 2:
                        item.artist_name = parts[0].strip()
                        item.track_name = parts[1].strip()
                    break
        
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Download timeout (10 minutes)"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        return False, f"SpotDL error: {error_msg}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def download_with_ytdlp(item):
    """Download using yt-dlp for YouTube links with full metadata"""
    try:
        cmd = [
            "yt-dlp",
            "-f", "140",  # Best audio quality format
            "--embed-metadata",
            "--embed-thumbnail", 
            "--add-metadata",
            "--metadata-from-title", "%(artist)s - %(title)s",
            "--output", os.path.join(MUSIC_DIR, "%(artist)s - %(title)s.%(ext)s"),
            item.url
        ]
        
        # Add cookies if available
        cookie_file = os.path.join(CONFIG_DIR, "cookies.txt")
        if os.path.exists(cookie_file):
            cmd.extend(["--cookies", cookie_file])
        
        result = subprocess.run(cmd, check=True, timeout=600, capture_output=True, text=True)
        
        # Try to extract track info
        try:
            info_cmd = ["yt-dlp", "--print", "%(artist)s", "--print", "%(title)s", "--quiet", item.url]
            info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
            if info_result.returncode == 0:
                lines = info_result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    item.artist_name = lines[0] or "Unknown Artist"
                    item.track_name = lines[1] or "Unknown Track"
                elif len(lines) == 1:
                    item.track_name = lines[0] or "Unknown Track"
        except:
            pass
            pass
        
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Download timeout (10 minutes)"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        return False, f"YT-DLP error: {error_msg}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def process_download_queue():
    """Background task to process the download queue"""
    global download_queue
    
    while True:
        current_item = None
        
        # Get next item from queue
        with queue_lock:
            waiting_items = [item for item in download_queue if item.status == 'waiting']
            if waiting_items:
                current_item = waiting_items[0]
                current_item.status = 'in_progress'
                current_item.started_at = datetime.now()
        
        if current_item:
            # Process the download
            success = False
            error_message = ""
            
            if current_item.download_type == 'spotify':
                success, error_message = download_with_spotdl(current_item)
            elif current_item.download_type == 'youtube':
                success, error_message = download_with_ytdlp(current_item)
            else:
                error_message = "Unknown URL type"
            
            # Update item status
            with queue_lock:
                if success:
                    current_item.status = 'completed'
                    current_item.completed_at = datetime.now()
                else:
                    current_item.status = 'failed'
                    current_item.error_message = error_message
                    current_item.completed_at = datetime.now()
        
        else:
            # No items to process, sleep for a bit
            time.sleep(2)

# Start background processor
import threading
processor_thread = threading.Thread(target=process_download_queue, daemon=True)
processor_thread.start()

@app.post("/upload-cookie")
async def upload_cookie(file: UploadFile = File(...)):
    """Upload cookie file for authentication"""
    content = await file.read()
    cookie_path = os.path.join(CONFIG_DIR, "cookies.txt")
    with open(cookie_path, "wb") as f:
        f.write(content)
    return {"message": "Cookie file uploaded successfully"}

@app.get("/cookie-status")
async def cookie_status():
    """Check if cookie file exists"""
    cookie_path = os.path.join(CONFIG_DIR, "cookies.txt")
    exists = os.path.exists(cookie_path)
    size = os.path.getsize(cookie_path) if exists else 0
    modified = datetime.fromtimestamp(os.path.getmtime(cookie_path)).isoformat() if exists else None
    
    return {
        "exists": exists,
        "size": size,
        "modified": modified
    }

@app.post("/add-downloads")
async def add_downloads(urls: list[str]):
    """Add URLs to download queue"""
    added_items = []
    
    with queue_lock:
        for url in urls:
            url = url.strip()
            if not url:
                continue
                
            download_type = detect_url_type(url)
            if download_type == 'unknown':
                continue
            
            # Check if URL is already in queue
            existing = any(item.url == url and item.status in ['waiting', 'in_progress'] for item in download_queue)
            if existing:
                continue
            
            item = DownloadItem(url, download_type)
            item.track_name, item.artist_name = extract_track_info(url, download_type)
            download_queue.append(item)
            added_items.append({
                "id": item.id,
                "url": item.url,
                "type": item.download_type,
                "track_name": item.track_name,
                "artist_name": item.artist_name
            })
    
    return {
        "message": f"Added {len(added_items)} downloads to queue",
        "added": added_items
    }

@app.get("/queue-status")
async def queue_status():
    """Get current queue status"""
    with queue_lock:
        items = []
        for item in download_queue:
            items.append({
                "id": item.id,
                "url": item.url,
                "download_type": item.download_type,
                "status": item.status,
                "track_name": item.track_name,
                "artist_name": item.artist_name,
                "error_message": item.error_message,
                "created_at": item.created_at.isoformat(),
                "started_at": item.started_at.isoformat() if item.started_at else None,
                "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            })
        
        # Sort by creation time
        items.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Get counts
        waiting_count = len([item for item in download_queue if item.status == 'waiting'])
        in_progress_count = len([item for item in download_queue if item.status == 'in_progress'])
        completed_count = len([item for item in download_queue if item.status == 'completed'])
        failed_count = len([item for item in download_queue if item.status == 'failed'])
        
        return {
            "items": items,
            "counts": {
                "waiting": waiting_count,
                "in_progress": in_progress_count,
                "completed": completed_count,
                "failed": failed_count,
                "total": len(download_queue)
            }
        }

@app.delete("/clear-queue")
async def clear_queue():
    """Clear completed and failed items from queue"""
    with queue_lock:
        original_count = len(download_queue)
        download_queue[:] = [item for item in download_queue if item.status in ['waiting', 'in_progress']]
        removed_count = original_count - len(download_queue)
    
    return {"message": f"Removed {removed_count} completed/failed items from queue"}

@app.delete("/remove-item/{item_id}")
async def remove_item(item_id: str):
    """Remove specific item from queue"""
    with queue_lock:
        original_count = len(download_queue)
        download_queue[:] = [item for item in download_queue if item.id != item_id]
        removed = original_count > len(download_queue)
    
    if removed:
        return {"message": "Item removed from queue"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")