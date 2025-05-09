# Reverbed API Examples

This directory contains example scripts that demonstrate how to use the Reverbed API.

## Prerequisites

- Python 3.8 or higher
- `requests` library: `pip install requests`

## Examples

### 1. Process a Video

The `process_video.py` script demonstrates how to process a YouTube video with reverb effects, check the job status, and download the result.

```bash
python process_video.py <youtube_url> [options]
```

Options:
- `--speed`: Speed of the audio (0.1 to 1.0, default: 0.8)
- `--room-size`: Size of the reverb room (0.0 to 1.0, default: 0.75)
- `--damping`: Damping of the reverb (0.0 to 1.0, default: 0.5)
- `--wet-level`: Wet level of the reverb (0.0 to 1.0, default: 0.08)
- `--dry-level`: Dry level of the reverb (0.0 to 1.0, default: 0.2)
- `--output`: Output file path (default: reverbed_<job_id>.mp3)

Example:
```bash
python process_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --speed 0.7 --output my_reverbed_song.mp3
```

### 2. Generate a Preview

The `generate_preview.py` script demonstrates how to generate a 20-second preview of a YouTube video with reverb effects.

```bash
python generate_preview.py <youtube_url> [options]
```

Options:
- `--speed`: Speed of the audio (0.1 to 1.0, default: 0.8)
- `--room-size`: Size of the reverb room (0.0 to 1.0, default: 0.75)
- `--damping`: Damping of the reverb (0.0 to 1.0, default: 0.5)
- `--wet-level`: Wet level of the reverb (0.0 to 1.0, default: 0.08)
- `--dry-level`: Dry level of the reverb (0.0 to 1.0, default: 0.2)
- `--download`: Download the preview file

Example:
```bash
python generate_preview.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --download
```

### 3. Search YouTube

The `search_youtube.py` script demonstrates how to search for YouTube videos using the Reverbed API.

```bash
python search_youtube.py <query> [options]
```

Options:
- `--limit`: Maximum number of results to return (default: 5)
- `--json`: Output results as JSON

Example:
```bash
python search_youtube.py "lofi hip hop" --limit 10
```

## API Documentation

For more information about the Reverbed API, see the [API documentation](../README.md).
