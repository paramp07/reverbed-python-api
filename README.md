# Reverbed API Documentation

The Reverbed API allows you to create slowed and reverbed versions of YouTube videos. This document provides detailed information about the available endpoints, request/response formats, and examples of how to use the API.

## Table of Contents

1. [Getting Started](#getting-started)
2. [API Endpoints](#api-endpoints)
   - [Process Video](#process-video)
   - [Preview Audio](#preview-audio)
   - [Get Job Status](#get-job-status)
   - [Download Result](#download-result)
   - [List Jobs](#list-jobs)
   - [Search YouTube](#search-youtube)
   - [Cache Status](#cache-status)
3. [Data Models](#data-models)
4. [Examples](#examples)
   - [Python](#python-examples)
   - [JavaScript](#javascript-examples)
   - [cURL](#curl-examples)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- FastAPI
- yt-dlp
- FFmpeg

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

The API will be available at `http://localhost:8000`.

## API Endpoints

### Process Video

Process a YouTube video to create a slowed and reverbed version.

- **URL**: `/process`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  // Optional, separate video source
    "audio_speed": 0.8,  // Optional, default: 0.8
    "room_size": 0.75,   // Optional, default: 0.75
    "damping": 0.5,      // Optional, default: 0.5
    "wet_level": 0.08,   // Optional, default: 0.08
    "dry_level": 0.2,    // Optional, default: 0.2
    "start_time": "0:30", // Optional, format: "MM:SS"
    "end_time": "1:00",   // Optional, format: "MM:SS"
    "loop_video": false   // Optional, default: false
  }
  ```
- **Response**:
  ```json
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "progress": 0.0,
    "result_file": null,
    "error": null,
    "used_cache": false
  }
  ```

### Preview Audio

Generate a 20-second preview (from 15s to 35s) of the processed audio.

- **URL**: `/preview`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "audio_speed": 0.8,  // Optional, default: 0.8
    "room_size": 0.75,   // Optional, default: 0.75
    "damping": 0.5,      // Optional, default: 0.5
    "wet_level": 0.08,   // Optional, default: 0.08
    "dry_level": 0.2     // Optional, default: 0.2
  }
  ```
- **Response**:
  ```json
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "progress": 0.0,
    "result_file": null,
    "error": null,
    "used_cache": false
  }
  ```

### Get Job Status

Check the status of a processing job.

- **URL**: `/status/{job_id}`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",  // "queued", "processing", "completed", or "failed"
    "progress": 1.0,        // 0.0 to 1.0
    "result_file": "550e8400-e29b-41d4-a716-446655440000.mp3",
    "error": null,
    "used_cache": false
  }
  ```

### Download Result

Download the processed file.

- **URL**: `/download/{job_id}`
- **Method**: `GET`
- **Response**: The processed file (audio or video)

### List Jobs

List all jobs in the system.

- **URL**: `/jobs`
- **Method**: `GET`
- **Response**:
  ```json
  [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": 1.0,
      "result_file": "550e8400-e29b-41d4-a716-446655440000.mp3",
      "error": null,
      "used_cache": false
    },
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440001",
      "status": "processing",
      "progress": 0.5,
      "result_file": null,
      "error": null,
      "used_cache": true
    }
  ]
  ```

### Search YouTube

Search for YouTube videos.

- **URL**: `/search`
- **Method**: `GET`
- **Query Parameters**:
  - `query`: Search query
  - `limit`: Maximum number of results (default: 5)
- **Response**:
  ```json
  {
    "videos": [
      {
        "id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "duration": "3:33",
        "channel": "Rick Astley",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
      }
    ]
  }
  ```

### Cache Status

Get information about the YouTube audio cache (for debugging).

- **URL**: `/cache-status`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "cache_size": 10,
    "max_cache_size": 50,
    "cache_expiration_seconds": 86400,
    "entries": [
      {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "file": "/path/to/cached/file.wav",
        "last_used": 1620000000,
        "age_seconds": 3600,
        "file_exists": true
      }
    ]
  }
  ```

## Data Models

### VideoProcessRequest

```python
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
```

### PreviewRequest

```python
class PreviewRequest(BaseModel):
    youtube_url: str
    audio_speed: float = 0.8
    room_size: float = 0.75
    damping: float = 0.5
    wet_level: float = 0.08
    dry_level: float = 0.2
```

### JobStatus

```python
class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    result_file: Optional[str] = None
    error: Optional[str] = None
    used_cache: bool = False
```

### YouTubeVideo

```python
class YouTubeVideo(BaseModel):
    id: str
    title: str
    thumbnail: str
    duration: str
    channel: str
    url: str
```

## Examples

### Python Examples

#### Process a Video and Download the Result

```python
import requests
import time
import os

# API base URL
API_BASE_URL = "http://localhost:8000"

# Process a video
def process_video(youtube_url, audio_speed=0.8, room_size=0.75, damping=0.5, wet_level=0.08, dry_level=0.2):
    url = f"{API_BASE_URL}/process"
    payload = {
        "youtube_url": youtube_url,
        "audio_speed": audio_speed,
        "room_size": room_size,
        "damping": damping,
        "wet_level": wet_level,
        "dry_level": dry_level
    }

    response = requests.post(url, json=payload)
    return response.json()

# Check job status
def check_job_status(job_id):
    url = f"{API_BASE_URL}/status/{job_id}"
    response = requests.get(url)
    return response.json()

# Download the result
def download_result(job_id, output_path):
    url = f"{API_BASE_URL}/download/{job_id}"
    response = requests.get(url)

    with open(output_path, 'wb') as f:
        f.write(response.content)

    return output_path

# Main process
def main():
    # Process a video
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = process_video(youtube_url)
    job_id = result["job_id"]

    print(f"Processing started. Job ID: {job_id}")

    # Wait for processing to complete
    while True:
        status = check_job_status(job_id)
        print(f"Status: {status['status']}, Progress: {status['progress'] * 100:.1f}%")

        if status["status"] == "completed":
            break
        elif status["status"] == "failed":
            print(f"Processing failed: {status['error']}")
            return

        time.sleep(2)

    # Download the result
    output_path = f"reverbed_{job_id}.mp3"
    download_result(job_id, output_path)
    print(f"Downloaded to {output_path}")

if __name__ == "__main__":
    main()
```

#### Generate a Preview

```python
import requests
import time

# API base URL
API_BASE_URL = "http://localhost:8000"

# Generate a preview
def generate_preview(youtube_url, audio_speed=0.8):
    url = f"{API_BASE_URL}/preview"
    payload = {
        "youtube_url": youtube_url,
        "audio_speed": audio_speed
    }

    response = requests.post(url, json=payload)
    return response.json()

# Check job status
def check_job_status(job_id):
    url = f"{API_BASE_URL}/status/{job_id}"
    response = requests.get(url)
    return response.json()

# Main process
def main():
    # Generate a preview
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = generate_preview(youtube_url)
    job_id = result["job_id"]

    print(f"Preview generation started. Job ID: {job_id}")

    # Wait for processing to complete
    while True:
        status = check_job_status(job_id)
        print(f"Status: {status['status']}, Progress: {status['progress'] * 100:.1f}%")

        if status["status"] == "completed":
            break
        elif status["status"] == "failed":
            print(f"Processing failed: {status['error']}")
            return

        time.sleep(1)

    # Get the preview URL
    preview_url = f"{API_BASE_URL}/download/{job_id}"
    print(f"Preview available at: {preview_url}")

if __name__ == "__main__":
    main()
```

### JavaScript Examples

#### Process a Video and Download the Result

```javascript
// Using fetch API
async function processVideo(youtubeUrl) {
  const response = await fetch('http://localhost:8000/process', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      youtube_url: youtubeUrl,
      audio_speed: 0.8,
      room_size: 0.75,
      damping: 0.5,
      wet_level: 0.08,
      dry_level: 0.2
    }),
  });

  return response.json();
}

async function checkJobStatus(jobId) {
  const response = await fetch(`http://localhost:8000/status/${jobId}`);
  return response.json();
}

async function downloadResult(jobId) {
  // Create a link element to trigger the download
  const link = document.createElement('a');
  link.href = `http://localhost:8000/download/${jobId}`;
  link.download = `reverbed_${jobId}.mp3`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Example usage
async function main() {
  try {
    // Process a video
    const youtubeUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
    const result = await processVideo(youtubeUrl);
    const jobId = result.job_id;

    console.log(`Processing started. Job ID: ${jobId}`);

    // Poll for status
    const checkStatus = async () => {
      const status = await checkJobStatus(jobId);
      console.log(`Status: ${status.status}, Progress: ${(status.progress * 100).toFixed(1)}%`);

      if (status.status === 'completed') {
        console.log('Processing complete!');
        downloadResult(jobId);
      } else if (status.status === 'failed') {
        console.error(`Processing failed: ${status.error}`);
      } else {
        // Continue polling
        setTimeout(checkStatus, 2000);
      }
    };

    checkStatus();
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
```

### cURL Examples

#### Process a Video

```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "audio_speed": 0.8,
    "room_size": 0.75,
    "damping": 0.5,
    "wet_level": 0.08,
    "dry_level": 0.2
  }'
```

#### Generate a Preview

```bash
curl -X POST "http://localhost:8000/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "audio_speed": 0.8
  }'
```

#### Check Job Status

```bash
curl -X GET "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"
```

#### Download Result

```bash
curl -X GET "http://localhost:8000/download/550e8400-e29b-41d4-a716-446655440000" --output reverbed.mp3
```

#### Search YouTube

```bash
curl -X GET "http://localhost:8000/search?query=lofi%20hip%20hop&limit=3"
```