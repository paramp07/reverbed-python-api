#!/usr/bin/env python3
"""
Example script for using the Reverbed API to generate a preview of a YouTube video.

This script demonstrates how to:
1. Generate a 20-second preview of a YouTube video with reverb effects
2. Check the job status
3. Get the URL for the preview when processing is complete

Usage:
    python generate_preview.py <youtube_url>

Example:
    python generate_preview.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
"""

import requests
import time
import sys
import argparse

# API base URL
API_BASE_URL = "http://localhost:8000"

def generate_preview(youtube_url, audio_speed=0.8, room_size=0.75, damping=0.5, wet_level=0.08, dry_level=0.2):
    """
    Generate a preview of a YouTube video with reverb effects.
    
    Args:
        youtube_url (str): URL of the YouTube video to preview
        audio_speed (float): Speed of the audio (0.1 to 1.0)
        room_size (float): Size of the reverb room (0.0 to 1.0)
        damping (float): Damping of the reverb (0.0 to 1.0)
        wet_level (float): Wet level of the reverb (0.0 to 1.0)
        dry_level (float): Dry level of the reverb (0.0 to 1.0)
        
    Returns:
        dict: Job status information
    """
    url = f"{API_BASE_URL}/preview"
    payload = {
        "youtube_url": youtube_url,
        "audio_speed": audio_speed,
        "room_size": room_size,
        "damping": damping,
        "wet_level": wet_level,
        "dry_level": dry_level
    }
    
    print(f"Generating preview for: {youtube_url}")
    response = requests.post(url, json=payload)
    return response.json()

def check_job_status(job_id):
    """
    Check the status of a processing job.
    
    Args:
        job_id (str): ID of the job to check
        
    Returns:
        dict: Job status information
    """
    url = f"{API_BASE_URL}/status/{job_id}"
    response = requests.get(url)
    return response.json()

def main():
    parser = argparse.ArgumentParser(description='Generate a preview of a YouTube video with reverb effects')
    parser.add_argument('youtube_url', help='URL of the YouTube video to preview')
    parser.add_argument('--speed', type=float, default=0.8, help='Speed of the audio (0.1 to 1.0)')
    parser.add_argument('--room-size', type=float, default=0.75, help='Size of the reverb room (0.0 to 1.0)')
    parser.add_argument('--damping', type=float, default=0.5, help='Damping of the reverb (0.0 to 1.0)')
    parser.add_argument('--wet-level', type=float, default=0.08, help='Wet level of the reverb (0.0 to 1.0)')
    parser.add_argument('--dry-level', type=float, default=0.2, help='Dry level of the reverb (0.0 to 1.0)')
    parser.add_argument('--download', action='store_true', help='Download the preview file')
    
    args = parser.parse_args()
    
    try:
        # Generate the preview
        result = generate_preview(
            args.youtube_url,
            audio_speed=args.speed,
            room_size=args.room_size,
            damping=args.damping,
            wet_level=args.wet_level,
            dry_level=args.dry_level
        )
        
        job_id = result["job_id"]
        print(f"Preview generation started. Job ID: {job_id}")
        
        # Wait for processing to complete
        while True:
            status = check_job_status(job_id)
            print(f"Status: {status['status']}, Progress: {status['progress'] * 100:.1f}%")
            
            if status["status"] == "completed":
                print("Preview generation complete!")
                break
            elif status["status"] == "failed":
                print(f"Preview generation failed: {status['error']}")
                return 1
            
            time.sleep(1)
        
        # Get the preview URL
        preview_url = f"{API_BASE_URL}/download/{job_id}"
        print(f"Preview available at: {preview_url}")
        
        # Download the preview if requested
        if args.download:
            output_path = f"preview_{job_id}.mp3"
            response = requests.get(preview_url)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded preview to {output_path}")
        
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
