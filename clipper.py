"""Convenience CLI shortcuts for ClipForge.

Usage:
  python clipper.py clip       # Find live stream, clip, and auto-title
  python clipper.py preview    # Open and watch the latest video
  python clipper.py list       # Show all clips with score & status
  python clipper.py post       # Publish latest approved clip now
  python clipper.py schedule   # Schedule latest approved clip for tomorrow 12:00 PM
  python clipper.py clean      # Clear output folder
"""
import datetime as dt
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def get_latest_clip(unposted_only=False):
    """Find the newest .mp4 clip in output/, optionally filtering for unposted clips."""
    mp4s = sorted(glob.glob(str(HERE / "output" / "*.mp4")), key=os.path.getmtime, reverse=True)
    if not mp4s:
        return None
    if not unposted_only:
        return Path(mp4s[0])
    for f in mp4s:
        p = Path(f)
        json_file = p.with_suffix(".json")
        if json_file.is_file():
            try:
                with open(json_file, "r", encoding="utf-8") as meta:
                    data = json.load(meta)
                if not data.get("zernio_post_id"):
                    return p
            except Exception:
                continue
    return None

def cmd_preview():
    latest = get_latest_clip()
    if not latest:
        print("No clips found in output/ to preview.")
        return
    print(f"🎬 Opening latest clip: {latest.name}")
    try:
        os.startfile(str(latest))
    except Exception:
        # Fallback for non-windows or subprocess
        subprocess.run(["explorer.exe", str(latest)])

def cmd_list():
    jsons = sorted(glob.glob(str(HERE / "output" / "*.json")), key=os.path.getmtime, reverse=True)
    if not jsons:
        print("No clips found in output/.")
        return
    print(f"\n{'FILE':<24} {'SCORE':<7} {'STATUS':<14} TITLE")
    print("-" * 75)
    for p in jsons:
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("zernio_post_id"):
                status = "🚀 Posted"
            elif d.get("approved"):
                status = "✅ Approved"
            else:
                status = "⏳ Draft"
            score = str(d.get("score", 0))
            title = (d.get("title") or "(no title)")[:32]
            print(f"{Path(p).stem:<24} {score:<7} {status:<14} {title}")
        except Exception:
            continue
    print()

def cmd_clip():
    print("🚀 Launching ClipForge...")
    subprocess.run([sys.executable, str(HERE / "auto_run.py")])

def cmd_post():
    latest = get_latest_clip(unposted_only=True)
    if not latest:
        print("No unposted clips found in output/. All clips have already been published!")
        return
    stem = latest.with_suffix("")
    json_path = stem.with_suffix(".json")
    if not json_path.is_file():
        print(f"Metadata file {json_path.name} not found.")
        return
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data.get("approved"):
        print(f"Clip {latest.name} is not approved yet. Set 'approved': true first.")
        return
    print(f"📤 Publishing latest unposted clip: {latest.name}...")
    subprocess.run([sys.executable, str(HERE / "publish.py"), str(stem), "--now", "--publish"])

def cmd_schedule():
    latest = get_latest_clip(unposted_only=True)
    if not latest:
        print("No unposted clips found in output/. All clips have already been published!")
        return
    stem = latest.with_suffix("")
    tomorrow = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%dT12:00:00+05:30")
    print(f"📅 Scheduling latest unposted clip: {latest.name} for tomorrow at 12:00 PM IST ({tomorrow})...")
    subprocess.run([sys.executable, str(HERE / "publish.py"), str(stem), "--scheduled-for", tomorrow, "--publish"])

def cmd_clean():
    count = 0
    for f in glob.glob(str(HERE / "output" / "*")):
        try:
            os.remove(f)
            count += 1
        except Exception:
            pass
    print(f"🧹 Cleaned {count} files from output/.")

def cmd_titles():
    """Generate or refresh titles using Groq LLM for clips in output/."""
    from auto_run import generate_viral_metadata
    jsons = sorted(glob.glob(str(HERE / "output" / "*.json")), key=os.path.getmtime, reverse=True)
    if not jsons:
        print("No clips found in output/.")
        return
    updated = 0
    for p in jsons:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        force = "--force" in sys.argv
        if not data.get("title") or force:
            print(f"Generating title for {Path(p).stem}...")
            title, yt_desc, ig_caption, hashtags = generate_viral_metadata(
                data.get("streamer"),
                data.get("transcript"),
                data.get("score"),
                data.get("source_url"),
                data.get("stream_title")
            )
            data["title"] = title
            data["youtube_description"] = yt_desc
            data["instagram_caption"] = ig_caption
            data["hashtags"] = hashtags
            data["approved"] = True
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ {Path(p).stem}: {title}")
            updated += 1
    if updated == 0:
        print("All clips already have titles. Use 'titles --force' to regenerate.")
    else:
        print(f"✨ Updated {updated} clip(s) with Groq AI titles.")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    action = sys.argv[1].lower()
    if action == "preview":
        cmd_preview()
    elif action == "clip":
        cmd_clip()
    elif action == "list":
        cmd_list()
    elif action == "titles":
        cmd_titles()
    elif action == "post":
        cmd_post()
    elif action == "schedule":
        cmd_schedule()
    elif action == "streams":
        subprocess.run([sys.executable, str(HERE / "find_streams.py"), "GTA 6", "--max", "100"])
    elif action in ("streams-json", "json"):
        subprocess.run([sys.executable, str(HERE / "find_streams.py"), "GTA 6", "--max", "100", "--json"])
    elif action == "clean":
        cmd_clean()
    else:
        print(f"Unknown action: '{action}'. Available: clip, preview, list, titles, post, schedule, streams, streams-json, clean")

if __name__ == "__main__":
    main()
