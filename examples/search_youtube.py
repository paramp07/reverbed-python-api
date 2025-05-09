#!/usr/bin/env python3
"""
Example script for using the Reverbed API to search YouTube.

This script demonstrates how to:
1. Search for YouTube videos using the Reverbed API
2. Display the search results

Usage:
    python search_youtube.py <query> [--limit <limit>]

Example:
    python search_youtube.py "lofi hip hop" --limit 10
"""

import requests
import sys
import argparse
import json

# API base URL
API_BASE_URL = "http://localhost:8000"

def search_youtube(query, limit=5):
    """
    Search for YouTube videos.
    
    Args:
        query (str): Search query
        limit (int): Maximum number of results to return
        
    Returns:
        dict: Search results
    """
    url = f"{API_BASE_URL}/search"
    params = {
        "query": query,
        "limit": limit
    }
    
    print(f"Searching YouTube for: {query}")
    response = requests.get(url, params=params)
    return response.json()

def main():
    parser = argparse.ArgumentParser(description='Search YouTube using the Reverbed API')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--limit', type=int, default=5, help='Maximum number of results to return')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    try:
        # Search YouTube
        results = search_youtube(args.query, args.limit)
        
        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Search results for '{args.query}':")
            for i, video in enumerate(results["videos"]):
                print(f"{i+1}. {video['title']} ({video['duration']})")
                print(f"   Channel: {video['channel']}")
                print(f"   URL: {video['url']}")
                print(f"   Thumbnail: {video['thumbnail']}")
                print()
        
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
