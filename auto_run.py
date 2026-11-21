"""Full End-to-End Automation for ClipForge.

Workflow:
1. Searches YouTube for live gaming streams using find_streams.py (e.g. GTA 6; reads YOUTUBE_API_KEY from .env).
2. Picks the top active stream.
3. Runs clip.py with your exact preferences (min-score 3.0, 30s clips, 10 mins capture, fill layout, combined hype signals).
4. Automatically writes viral titles, descriptions, and hashtags for all generated clips.
5. Marks them approved and optionally schedules them through Zernio!
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Automatically load .env if present
def load_env():
    env_file = HERE / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k not in os.environ and v:
                    os.environ[k] = v

load_env()

def generate_viral_metadata(streamer, transcript, score, source_url, stream_title, hook=None):
    """Generate punchy, viral title, YouTube description, and Instagram caption using Groq LLM."""
    streamer_clean = streamer or "Streamer"
    groq_api_key = os.environ.get("GROQ_API_KEY")
    groq_model = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")

    hook_line = f"KEY MOMENT HOOK: \"{hook}\"\n" if hook else ""

    # 1. Try 100% LLM AI Generation via Groq
    if groq_api_key:
        try:
            import requests
            prompt = (
                f"You are a viral YouTube Shorts and Instagram Reels strategist for GTA gaming content.\n"
                f"Analyze this stream highlight and write high-CTR, click-worthy metadata.\n\n"
                f"STREAMER: {streamer_clean}\n"
                f"ORIGINAL STREAM: {stream_title or 'GTA 6 Live'}\n"
                f"{hook_line}"
                f"MOMENT HYPE SCORE: {score}/10\n"
                f"TRANSCRIPT / WHAT WAS SAID:\n\"{transcript or '(Intense screams / gaming action without clear words)'}\"\n\n"
                f"Return ONLY valid JSON with these exact keys:\n"
                f"- title: Short, punchy, high-CTR YouTube Shorts title under 75 characters with 1-2 emojis and #shorts. Hook the viewer immediately.\n"
                f"- youtube_description: 3-5 lines describing the moment, crediting {streamer_clean}, asking viewers to subscribe, plus GTA 6 hashtags. Never mention internal scores or ratings.\n"
                f"- instagram_caption: Engaging reel caption with hook, @{streamer_clean.replace(' ', '').lower()} tag, comment CTA, and hashtags. Never mention internal scores or ratings.\n"
                f"- hashtags: array of 5-7 popular hashtags (strings without '#')."
            )
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": groq_model,
                    "messages": [
                        {"role": "system", "content": "You are an elite viral gaming copywriter. Always output strictly valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=12
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                res_json = json.loads(content)
                title = res_json.get("title")
                yt_desc = res_json.get("youtube_description")
                ig_caption = res_json.get("instagram_caption")
                hashtags = res_json.get("hashtags") or ["GTA6", "Gaming", "Shorts"]
                if title and yt_desc and ig_caption:
                    print(f"  🤖 Groq AI ({groq_model}) generated viral title!")
                    return title.strip(), yt_desc.strip(), ig_caption.strip(), hashtags
        except Exception as e:
            print(f"  [Notice: Groq LLM unavailable ({e}); using smart fallback]")

    # 2. Smart local fallback generator
    if transcript and len(transcript.strip()) > 10:
        quote = transcript.strip().split(".")[0][:45].strip('"')
        title = f'"{quote}" 😂💀 | {streamer_clean} GTA 6 #shorts'
    else:
        title = f'{streamer_clean} Went Completely Insane on GTA 6! 💥😂 #shorts'

    if len(title) > 95:
        title = title[:92] + "..."

    yt_description = (
        f"{streamer_clean} with an insane GTA 6 stream highlight! 😂🔥\n\n"
        f"Streamer: {streamer_clean}\n"
        f"Original Stream: {stream_title or 'GTA 6 Live'}\n"
        f"Source: {source_url}\n\n"
        f"Are you ready for GTA 6? Subscribe for daily GTA 6 leaks, gameplay & stream highlights! 🎮\n\n"
        f"#{streamer_clean.replace(' ', '')} #GTA6 #GTAVI #GrandTheftAuto6 #Gaming #Shorts #YouTubeShorts #Trending"
    )

    ig_caption = (
        f"GTA 6 is getting completely out of hand 😂💀 Wait till the end!\n\n"
        f"Streamer: @{streamer_clean.replace(' ', '').lower()}\n\n"
        f"Drop a 🔥 if you're hyped for GTA 6!\n.\n.\n"
        f"#{streamer_clean.replace(' ', '').lower()} #gta6 #gtavi #grandtheftauto6 #gta #gaming #gamingshorts #gamingreels #reels #viral"
    )

    hashtags = ["GTA6", "GTAVI", "GrandTheftAuto6", "Gaming", "Shorts", "YouTubeShorts", streamer_clean.replace(" ", "")]
    return title, yt_description, ig_caption, hashtags


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Fully Automated Stream Finder, Clipper, and Approver")
    parser.add_argument("--query", default="GTA 6 live english", help="Stream search phrase (default: 'GTA 6 live english')")
    parser.add_argument("--max-seconds", type=int, default=600, help="Recording capture time in seconds (default: 600 = 10 mins)")
    parser.add_argument("--clip-len", type=int, default=30, help="Clip length in seconds (default: 30)")
    parser.add_argument("--top", type=int, default=2, help="Clips per chunk (default: 2)")
    parser.add_argument("--min-score", type=float, default=2.0, help="Minimum moment score (default: 2.0)")
    parser.add_argument("--stream-url", help="Direct stream URL if you already have one")
    parser.add_argument("--publish-now", action="store_true", help="Automatically publish approved clips immediately via Zernio")
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    stream_url = args.stream_url

    if not stream_url:
        if not api_key:
            sys.exit("Error: YOUTUBE_API_KEY not found in environment or .env file.")
        
        print(f"\n🔍 Searching up to 100 live streams for: '{args.query}'...")
        from find_streams import find_streams
        try:
            streams = find_streams(args.query, api_key, limit=100)
        except Exception as e:
            sys.exit(f"Failed to find streams: {e}")

        if not streams:
            sys.exit("No live streams found for that query. Try another search term.")

        print("\nFound top active streams:")
        for i, st in enumerate(streams, 1):
            print(f" [{i}] {st['channel']} — {st['title']}")
            print(f"     {st['url']}")

        # Filter strictly for GTA 6 streams in English or Hindi
        non_en_hi_signals = (
            "ao vivo", "en vivo", "türkçe", "español", "português", "você", "voces", 
            "loko", "paulinho", "gameplayrj", "pra ", "hoje", "ngày", "jogo", "direto", 
            "brasil", "pt-br", "en direct", "en directo"
        )
        gta6_candidates = [
            st for st in streams
            if any(k in st["title"].lower() for k in ("gta 6", "gta vi", "gta6"))
            and not any(neg in (st["title"] + " " + st["channel"]).lower() for neg in non_en_hi_signals)
        ]
        selected = gta6_candidates[0] if gta6_candidates else streams[0]
        stream_url = selected["url"]
        print(f"\n👉 Auto-selected GTA 6 Stream: {selected['channel']} ({selected['title']})")
        print(f"   URL: {stream_url}\n")

    # Snapshot existing json clips before running
    before_clips = set(glob.glob(str(HERE / "output" / "*.json")))

    # Run clip.py with exact preferences
    cmd = [
        sys.executable, str(HERE / "clip.py"),
        stream_url,
        "--gameplay-confirmed",
        "--max-seconds", str(args.max_seconds),
        "--clip-len", str(args.clip_len),
        "--top", str(args.top),
        "--min-score", str(args.min_score),
        "--moment-source", "combined",
        "--layout", "fill",
        "--spoken-language", "auto",
        "--block-facecam",
        "--require-en-hi",
    ]

    print("🚀 Starting AI Clipper with your preferences:")
    print(f"   • Min Hype Score : {args.min_score}")
    print(f"   • Duration       : {args.max_seconds} seconds ({args.max_seconds // 60} mins)")
    print(f"   • Clips Per Chunk: {args.top}")
    print(f"   • Clip Length    : {args.clip_len}s vertical 9:16 fill")
    print(f"   • Facecam Block  : Strictly ON (pure central gameplay)")
    print(f"   • Languages      : English & Hindi only (others discarded)")
    print(f"   • Scoring Signals: combined (chat + loud audio + speech reaction)\n")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nCapture interrupted by user. Processing clips generated so far...")

    # Detect new clips produced
    after_clips = set(glob.glob(str(HERE / "output" / "*.json")))
    new_clips = sorted(after_clips - before_clips)

    if not new_clips:
        print("\nNo new clips reached the score threshold (3.0+) in this session.")
        print("Tip: If the stream was quiet, try running with --min-score 2.0 to capture more moments.")
        return

    print(f"\n🎉 Successfully created {len(new_clips)} new high-energy clip(s)!\n")

    # Auto-generate metadata and approve each new clip
    for clip_json_path in new_clips:
        p = Path(clip_json_path)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        title, yt_desc, ig_caption, hashtags = generate_viral_metadata(
            data.get("streamer"),
            data.get("transcript"),
            data.get("score"),
            data.get("source_url"),
            data.get("stream_title"),
            hook=data.get("hook")
        )

        data["title"] = title
        data["youtube_description"] = yt_desc
        data["instagram_caption"] = ig_caption
        data["hashtags"] = hashtags
        data["approved"] = True

        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Approved: {data['video']}")
        print(f"   Score : {data['score']}")
        print(f"   Title : {title}")

        # If user enabled auto-publish
        if args.publish_now:
            print(f"   📤 Publishing {data['video']} via Zernio...")
            pub_cmd = [sys.executable, str(HERE / "publish.py"), str(p.with_suffix("")), "--now", "--publish"]
            res = subprocess.run(pub_cmd)
            if res.returncode == 0:
                print(f"   🚀 Published successfully!")
            else:
                print(f"   ⚠️ Publish failed. Check Zernio settings.")

    print("\n✨ All done! Your clips are ready in output/ with full titles and descriptions.")


if __name__ == "__main__":
    main()
