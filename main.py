from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import os
import uuid
import shutil
from typing import Optional, Dict, Any, List
import time
import json
import subprocess
import re

# Import reverbed functionality
from reverbed import download_audio, slowed_reverb, download_video, combine_audio_video

# Define a simple YouTube search function using yt-dlp
def search_youtube_videos(query, limit=5):
    try:
        # Use yt-dlp to search for videos
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            "--default-search", "ytsearch",
            f"ytsearch{limit}:{query}"
        ]

        print(f"Running search command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"yt-dlp search error: {result.stderr}")
            return []

        # Parse the JSON output
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue

            try:
                video_data = json.loads(line)
                videos.append({
                    'id': video_data.get('id', ''),
                    'title': video_data.get('title', ''),
                    'thumbnail': video_data.get('thumbnail', ''),
                    'duration': str(video_data.get('duration_string', 'Unknown')),
                    'channel': video_data.get('channel', 'Unknown'),
                    'url': video_data.get('webpage_url', f"https://www.youtube.com/watch?v={video_data.get('id', '')}")
                })
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                continue

        return videos
    except Exception as e:
        print(f"Error searching YouTube: {str(e)}")
        return []

# Set YouTube search availability flag
YOUTUBE_SEARCH_AVAILABLE = True

app = FastAPI(title="Reverbed API", description="API for creating slowed and reverbed versions of YouTube videos")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for storing files in user's home directory
import tempfile
from pathlib import Path

# Use user's home directory for storage
USER_HOME = str(Path.home())
APP_DIR = os.path.join(USER_HOME, "reverbed_app_data")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
OUTPUT_DIR = os.path.join(APP_DIR, "outputs")
TEMP_DIR = os.path.join(APP_DIR, "temp")

print(f"Using app directory: {APP_DIR}")

# Ensure directories exist with proper permissions
for directory in [APP_DIR, UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
        # Make sure the directory is writable
        test_file = os.path.join(directory, ".write_test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"Directory {directory} is writable")
    except Exception as e:
        print(f"Error creating or writing to directory {directory}: {str(e)}")

        # If we can't create the directory, try using system temp directory
        if directory == TEMP_DIR:
            TEMP_DIR = tempfile.gettempdir()
            print(f"Falling back to system temp directory: {TEMP_DIR}")

# Store job status
jobs = {}

# Cache for downloaded YouTube videos
# Structure: { "youtube_url": {"audio_file": "path/to/file.wav", "last_used": timestamp} }
youtube_cache = {}

# Maximum number of items to keep in cache
MAX_CACHE_SIZE = 50

# Cache expiration time in seconds (24 hours)
CACHE_EXPIRATION = 24 * 60 * 60

def cleanup_cache():
    """Clean up old cache entries to prevent the cache from growing too large"""
    if len(youtube_cache) <= MAX_CACHE_SIZE:
        return

    # Remove expired entries first
    current_time = time.time()
    expired_urls = [
        url for url, info in youtube_cache.items()
        if current_time - info["last_used"] > CACHE_EXPIRATION
    ]

    for url in expired_urls:
        print(f"Removing expired cache entry for {url}")
        del youtube_cache[url]

    # If still too many entries, remove oldest ones
    if len(youtube_cache) > MAX_CACHE_SIZE:
        # Sort by last_used timestamp
        sorted_cache = sorted(
            youtube_cache.items(),
            key=lambda x: x[1]["last_used"]
        )

        # Remove oldest entries until we're under the limit
        to_remove = len(youtube_cache) - MAX_CACHE_SIZE
        for i in range(to_remove):
            url, _ = sorted_cache[i]
            print(f"Removing old cache entry for {url}")
            del youtube_cache[url]

class VideoProcessRequest(BaseModel):
    youtube_url: str
    video_url: Optional[str] = None  # Optional separate video URL for video processing
    audio_speed: float = 0.8
    room_size: float = 0.75
    damping: float = 0.5
    wet_level: float = 0.08
    dry_level: float = 0.2
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    loop_video: bool = False

class PreviewRequest(BaseModel):
    youtube_url: str
    audio_speed: float = 0.8
    room_size: float = 0.75
    damping: float = 0.5
    wet_level: float = 0.08
    dry_level: float = 0.2

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    result_file: Optional[str] = None
    error: Optional[str] = None
    used_cache: bool = False

class YouTubeVideo(BaseModel):
    id: str
    title: str
    thumbnail: str
    duration: str
    channel: str
    url: str

class YouTubeSearchResponse(BaseModel):
    videos: List[YouTubeVideo]

@app.get("/")
async def root():
    return {"message": "Welcome to Reverbed API"}

@app.post("/process", response_model=JobStatus)
async def process_video(request: VideoProcessRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    # Initialize job status
    jobs[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "result_file": None,
        "error": None
    }

    # Start processing in background
    background_tasks.add_task(
        process_video_task,
        job_id,
        request.youtube_url,
        request.audio_speed,
        request.room_size,
        request.damping,
        request.wet_level,
        request.dry_level,
        request.start_time,
        request.end_time,
        request.loop_video,
        request.video_url
    )

    return JobStatus(job_id=job_id, status="queued")

def process_video_task(
    job_id: str,
    youtube_url: str,
    audio_speed: float,
    room_size: float,
    damping: float,
    wet_level: float,
    dry_level: float,
    start_time: Optional[str],
    end_time: Optional[str],
    loop_video: bool,
    video_url: Optional[str] = None
):
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 0.1

        # Create job directory with proper permissions
        job_dir = os.path.join(TEMP_DIR, job_id)
        try:
            os.makedirs(job_dir, exist_ok=True)
            # Test if directory is writable
            test_file = os.path.join(job_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"Job directory {job_dir} is writable")
        except Exception as e:
            print(f"Error with job directory {job_dir}: {str(e)}")
            raise Exception(f"Cannot create or write to job directory: {str(e)}")

        # Download audio using yt-dlp directly
        try:
            audio_file = os.path.join(job_dir, "audio.wav")
            print(f"Downloading audio from {youtube_url} to {job_dir}")

            # Try direct yt-dlp approach
            import subprocess

            # Create a unique filename for the audio
            audio_filename = f"audio_{job_id}.wav"
            audio_file = os.path.join(job_dir, audio_filename)

            # Use yt-dlp to download the audio
            cmd = [
                "yt-dlp",
                "-x",
                "--audio-format", "wav",
                "--audio-quality", "0",
                "-o", audio_file,
                youtube_url
            ]

            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"yt-dlp error: {result.stderr}")
                # Fall back to the reverbed function
                print("Falling back to reverbed download_audio function")
                download_audio(youtube_url, job_dir, audio_format='wav')

            # Verify the file exists
            if not os.path.exists(audio_file):
                # Try to find any wav file in the directory
                wav_files = [f for f in os.listdir(job_dir) if f.endswith('.wav')]
                if wav_files:
                    audio_file = os.path.join(job_dir, wav_files[0])
                    print(f"Found audio file: {audio_file}")
                else:
                    raise Exception("Audio file not found after download")

            jobs[job_id]["progress"] = 0.4
        except Exception as e:
            print(f"Error downloading audio: {str(e)}")
            raise Exception(f"Error downloading audio: {str(e)}")

        # Apply effects
        try:
            processed_audio = os.path.join(job_dir, "processed_audio.wav")
            print(f"Applying effects to {audio_file}, saving to {processed_audio}")
            slowed_reverb(
                audio_file,
                processed_audio,
                speed=audio_speed,
                room_size=room_size,
                damping=damping,
                wet_level=wet_level,
                dry_level=dry_level
            )
            jobs[job_id]["progress"] = 0.7
        except Exception as e:
            print(f"Error applying effects: {str(e)}")
            raise Exception(f"Error applying effects: {str(e)}")

        # Handle video if needed
        output_file = os.path.join(OUTPUT_DIR, f"{job_id}.mp3")

        try:
            # Determine which URL to use for video
            video_source_url = video_url if video_url else youtube_url

            if loop_video and start_time and end_time:
                # Download and trim video
                video_file = os.path.join(job_dir, "video.mp4")
                print(f"Downloading video from {video_source_url} with time range {start_time}-{end_time}")
                download_video(video_source_url, video_file, start_time, end_time)

                # Combine audio and video
                # Remove extension from job_id to prevent double extension
                output_file = os.path.join(OUTPUT_DIR, f"{job_id}")
                print(f"Combining audio and video to {output_file}")

                try:
                    # Make sure the output directory exists
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)

                    # Combine the audio and video
                    combine_audio_video(processed_audio, video_file, output_file)

                    # Verify the file exists - check for both with and without extension
                    # The combine_audio_video function might add .mp4 extension
                    if os.path.exists(output_file):
                        print(f"Successfully created video file: {output_file}")
                        print(f"File size: {os.path.getsize(output_file)} bytes")
                    elif os.path.exists(output_file + ".mp4"):
                        # If the file exists with .mp4 extension, update the output_file variable
                        output_file = output_file + ".mp4"
                        print(f"Found video file with .mp4 extension: {output_file}")
                        print(f"File size: {os.path.getsize(output_file)} bytes")
                    else:
                        # Check for any file in the output directory that starts with the job_id
                        matching_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(job_id)]
                        if matching_files:
                            output_file = os.path.join(OUTPUT_DIR, matching_files[0])
                            print(f"Found matching output file: {output_file}")
                            print(f"File size: {os.path.getsize(output_file)} bytes")
                        else:
                            print(f"No matching output files found for job_id: {job_id}")
                            print(f"WARNING: Output video file was not created at {output_file}")
                            raise Exception(f"Failed to create output video file at {output_file}")

                    # Ensure file has proper permissions
                    try:
                        import stat
                        os.chmod(output_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                        print(f"Set permissions on {output_file}")
                    except Exception as e:
                        print(f"Warning: Could not set permissions on output file: {str(e)}")
                except Exception as e:
                    print(f"Error combining audio and video: {str(e)}")
                    # Fallback to just using the audio file
                    output_file = os.path.join(OUTPUT_DIR, f"{job_id}.mp3")
                    print(f"Falling back to audio-only output: {output_file}")
                    shutil.copy(processed_audio, output_file)
            else:
                # Just copy the processed audio to output
                print(f"Copying processed audio to {output_file}")
                shutil.copy(processed_audio, output_file)

                # Ensure file has proper permissions
                try:
                    import stat
                    os.chmod(output_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                    print(f"Set permissions on {output_file}")
                except Exception as e:
                    print(f"Warning: Could not set permissions on output file: {str(e)}")
        except Exception as e:
            print(f"Error in final processing: {str(e)}")
            raise Exception(f"Error in final processing: {str(e)}")

        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["result_file"] = os.path.basename(output_file)
        print(f"Job {job_id} completed successfully")
        print(f"Result file: {jobs[job_id]['result_file']}")

    except Exception as e:
        # Update job status with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"Error processing job {job_id}: {str(e)}")

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        result_file=job["result_file"],
        error=job["error"],
        used_cache=job.get("used_cache", False)
    )

@app.get("/download/{job_id}")
async def download_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job["result_file"]:
        raise HTTPException(status_code=404, detail="Result file not found")

    file_path = os.path.join(OUTPUT_DIR, job["result_file"])
    print(f"Attempting to download file: {file_path}")

    if not os.path.exists(file_path):
        print(f"ERROR: File not found at path: {file_path}")
        print(f"OUTPUT_DIR: {OUTPUT_DIR}")
        print(f"Result file name: {job['result_file']}")
        print(f"Files in OUTPUT_DIR: {os.listdir(OUTPUT_DIR)}")
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    # Set appropriate media type based on file extension
    media_type = "application/octet-stream"
    if file_path.endswith(".mp4"):
        media_type = "video/mp4"
    elif file_path.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif file_path.endswith(".wav"):
        media_type = "audio/wav"

    return FileResponse(
        path=file_path,
        filename=job["result_file"],
        media_type=media_type
    )

@app.get("/jobs", response_model=List[JobStatus])
async def list_jobs():
    return [
        JobStatus(
            job_id=job_id,
            status=job["status"],
            progress=job["progress"],
            result_file=job["result_file"],
            error=job["error"],
            used_cache=job.get("used_cache", False)
        )
        for job_id, job in jobs.items()
    ]

@app.get("/cache-status")
async def get_cache_status():
    """Get the status of the YouTube audio cache (for debugging)"""
    cache_entries = []
    current_time = time.time()

    for url, info in youtube_cache.items():
        cache_entries.append({
            "url": url,
            "file": info["audio_file"],
            "last_used": info["last_used"],
            "age_seconds": int(current_time - info["last_used"]),
            "file_exists": os.path.exists(info["audio_file"])
        })

    return {
        "cache_size": len(youtube_cache),
        "max_cache_size": MAX_CACHE_SIZE,
        "cache_expiration_seconds": CACHE_EXPIRATION,
        "entries": cache_entries
    }

@app.get("/search", response_model=YouTubeSearchResponse)
async def search_youtube(query: str, limit: int = 5):
    """
    Search for YouTube videos by query string.
    Returns a list of videos with thumbnails, duration, and titles.
    """
    if not YOUTUBE_SEARCH_AVAILABLE:
        raise HTTPException(status_code=501, detail="YouTube search functionality not available")

    try:
        # Use our custom search function
        video_results = search_youtube_videos(query, limit)

        # Debug thumbnails
        for video in video_results:
            print(f"Video ID: {video.get('id')}, Thumbnail: {video.get('thumbnail')}")

            # Ensure thumbnail is a valid URL
            thumbnail = video.get('thumbnail', '')
            if not thumbnail.startswith(('http://', 'https://')):
                # Use YouTube's thumbnail URL format if we only have the ID
                video_id = video.get('id', '')
                if video_id:
                    video['thumbnail'] = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
                    print(f"Fixed thumbnail URL: {video['thumbnail']}")

        videos = []
        for video in video_results:
            videos.append(YouTubeVideo(
                id=video.get('id', ''),
                title=video.get('title', ''),
                thumbnail=video.get('thumbnail', ''),
                duration=video.get('duration', 'Unknown'),
                channel=video.get('channel', 'Unknown'),
                url=video.get('url', '')
            ))

        return YouTubeSearchResponse(videos=videos)
    except Exception as e:
        print(f"Error searching YouTube: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching YouTube: {str(e)}")

@app.post("/preview", response_model=JobStatus)
async def preview_audio(request: PreviewRequest, background_tasks: BackgroundTasks):
    """
    Create a preview of the audio with effects applied.
    This processes only a 20-second clip (from 15s to 35s) of the video.
    """
    job_id = str(uuid.uuid4())

    # Initialize job status
    jobs[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "result_file": None,
        "error": None,
        "used_cache": False
    }

    # Start processing in background
    background_tasks.add_task(
        process_preview_task,
        job_id,
        request.youtube_url,
        request.audio_speed,
        request.room_size,
        request.damping,
        request.wet_level,
        request.dry_level
    )

    return JobStatus(job_id=job_id, status="queued")

def process_preview_task(
    job_id: str,
    youtube_url: str,
    audio_speed: float,
    room_size: float,
    damping: float,
    wet_level: float,
    dry_level: float
):
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 0.1

        # Create job directory with proper permissions
        job_dir = os.path.join(TEMP_DIR, job_id)
        try:
            os.makedirs(job_dir, exist_ok=True)
            # Test if directory is writable
            test_file = os.path.join(job_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"Job directory {job_dir} is writable")
        except Exception as e:
            print(f"Error with job directory {job_dir}: {str(e)}")
            raise Exception(f"Cannot create or write to job directory: {str(e)}")

        # Check if we already have this YouTube video in cache
        audio_file = None
        is_cached = False

        if youtube_url in youtube_cache:
            cached_info = youtube_cache[youtube_url]
            cached_file = cached_info["audio_file"]

            if os.path.exists(cached_file):
                print(f"Using cached audio file for {youtube_url}: {cached_file}")
                audio_file = cached_file
                is_cached = True
                # Update last used timestamp
                youtube_cache[youtube_url]["last_used"] = time.time()
                jobs[job_id]["progress"] = 0.4  # Skip ahead in progress
                jobs[job_id]["used_cache"] = True  # Mark that we used the cache
            else:
                # Cached file doesn't exist anymore, remove from cache
                print(f"Cached file {cached_file} no longer exists, removing from cache")
                del youtube_cache[youtube_url]

        # If not in cache, download the audio
        if not is_cached:
            try:
                # Create a unique filename for the audio
                audio_filename = f"preview_audio_{job_id}.wav"
                audio_file = os.path.join(job_dir, audio_filename)

                # Use yt-dlp to download just the preview segment (15s to 35s)
                cmd = [
                    "yt-dlp",
                    "-x",
                    "--audio-format", "wav",
                    "--audio-quality", "0",
                    "--postprocessor-args", "-ss 00:00:15 -to 00:00:35",
                    "-o", audio_file,
                    youtube_url
                ]

                print(f"Running preview command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"yt-dlp preview error: {result.stderr}")
                    raise Exception(f"Error downloading preview audio: {result.stderr}")

                # Verify the file exists
                if not os.path.exists(audio_file):
                    # Try to find any wav file in the directory
                    wav_files = [f for f in os.listdir(job_dir) if f.endswith('.wav')]
                    if wav_files:
                        audio_file = os.path.join(job_dir, wav_files[0])
                        print(f"Found preview audio file: {audio_file}")
                    else:
                        raise Exception("Preview audio file not found after download")

                # Add to cache
                youtube_cache[youtube_url] = {
                    "audio_file": audio_file,
                    "last_used": time.time()
                }
                print(f"Added {youtube_url} to cache with file {audio_file}")

                # Clean up cache if needed
                cleanup_cache()

                jobs[job_id]["progress"] = 0.5
            except Exception as e:
                print(f"Error downloading preview audio: {str(e)}")
                raise Exception(f"Error downloading preview audio: {str(e)}")

        # Apply effects
        try:
            processed_audio = os.path.join(job_dir, "processed_preview.wav")
            print(f"Applying effects to preview {audio_file}, saving to {processed_audio}")
            slowed_reverb(
                audio_file,
                processed_audio,
                speed=audio_speed,
                room_size=room_size,
                damping=damping,
                wet_level=wet_level,
                dry_level=dry_level
            )
            jobs[job_id]["progress"] = 0.8
        except Exception as e:
            print(f"Error applying effects to preview: {str(e)}")
            raise Exception(f"Error applying effects to preview: {str(e)}")

        # Copy to output directory
        try:
            output_file = os.path.join(OUTPUT_DIR, f"preview_{job_id}.mp3")
            print(f"Copying processed preview audio to {output_file}")
            shutil.copy(processed_audio, output_file)
        except Exception as e:
            print(f"Error in final preview processing: {str(e)}")
            raise Exception(f"Error in final preview processing: {str(e)}")

        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["result_file"] = os.path.basename(output_file)
        print(f"Preview job {job_id} completed successfully")

    except Exception as e:
        # Update job status with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"Error processing preview job {job_id}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
