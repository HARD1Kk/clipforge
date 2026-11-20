"""Find current YouTube live streams for a query, ranked by YouTube view count.

Set YOUTUBE_API_KEY in the environment. The YouTube API does not provide this
search as a dependable live concurrent-viewer leaderboard.
"""
import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3/search"


def load_env_fallback():
    """Load variables from .env if present without external dependencies."""
    from pathlib import Path
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k not in os.environ and v:
                        os.environ[k] = v
        except Exception:
            pass


load_env_fallback()


def find_streams(query, api_key, limit=100):
    streams = []
    page_token = None
    target_count = min(max(limit, 1), 100)

    while len(streams) < target_count:
        fetch_n = min(50, target_count - len(streams))
        query_dict = {
            "part": "snippet", "eventType": "live", "type": "video", "q": query,
            "maxResults": fetch_n, "order": "viewCount", "key": api_key,
        }
        if page_token:
            query_dict["pageToken"] = page_token

        params = urllib.parse.urlencode(query_dict)
        request = urllib.request.Request(f"{API}?{params}", headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)

        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            streams.append({
                "title": html.unescape(snippet.get("title", "")),
                "channel": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "rank_signal": "YouTube search order=viewCount; not current live viewers",
            })
            if len(streams) >= target_count:
                break

        page_token = payload.get("nextPageToken")
        if not page_token or not payload.get("items"):
            break

    return streams


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles default to cp1252
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="GTA 6")
    parser.add_argument("--max", type=int, default=100, help="candidate count (up to 100)")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        sys.exit("Set YOUTUBE_API_KEY in your environment before searching.")
    try:
        streams = find_streams(args.query, api_key, args.max)
    except urllib.error.HTTPError as error:
        sys.exit(f"YouTube API returned HTTP {error.code}; check the API key and quota.")
    except Exception as error:
        sys.exit(f"Stream search failed ({type(error).__name__}). Check the network and API key.")
    if args.json:
        print(json.dumps(streams, ensure_ascii=False, indent=2))
    else:
        for rank, stream in enumerate(streams, 1):
            print(f"[{rank}] {stream['channel']} — {stream['title']}\n    {stream['url']}")
            print("    Rank signal: YouTube view-count ordering; not current concurrent viewers.")
        if not streams:
            print("No live results found. Try another search phrase.")


if __name__ == "__main__":
    main()
