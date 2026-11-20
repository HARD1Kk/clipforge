# ClipForge CLI Options & Configuration

This guide details all command-line arguments and configuration options for `clip.py` and `find_streams.py`.

## `clip.py` Options Reference

| Option | Default | Description |
| --- | ---: | --- |
| `--max-seconds` | `0` | Total stream recording time in seconds (`0` runs indefinitely until stopped with `Ctrl+C`). |
| `--chunk` | `90` | Analysis chunk size in seconds for rolling stream recording. |
| `--clip-len` | `30` | Duration of each exported vertical clip in seconds. |
| `--lead-in` | `6` | Seconds of context to include before the detected hype peak. |
| `--top` | `1` | Maximum number of clips to export per analysis chunk. |
| `--gameplay-confirmed` | *required for live URLs* | Safety gate confirming gameplay is visible on screen. |
| `--min-score` | `2.5` | Minimum hype score required to export a clip (use `3.0` for high reaction, `5.0` for extreme). |
| `--layout` | `fill` | Framing mode: `fill` crops to full 9:16 vertical view (facecams avoided); `fit` places the 16:9 gameplay in the center over a blurred background. |
| `--moment-source` | `chat` | Scoring method: `chat` (viewer chat reaction spikes), `combined` (chat + audio RMS + Whisper reaction speech), or `audio` (audio + speech only). |
| `--spoken-language` | `auto` | `auto` detects language and locks to Hindi/English. Pass `en` or `hi` to force language throughout. |
| `--block-facecam` | `off` | Enforces pure center crop ($x=0.5$), strictly preventing edge camera framing. |
| `--require-en-hi` | `off` | Discards chunks where detected language is neither English nor Hindi. |
| `--no-chat` | `off` | Disables live chat scraping; uses audio and speech scoring only. |
| `--output-dir` | `output/` | Directory where rendered `.mp4` and `.json` metadata are saved. |
| `--file` | `None` | Local video file path to analyze instead of a live URL (requires `--test`). |
| `--test` | `off` | Test mode: exports to `test_out/` and flags metadata as test (not publishable). |

## Examples

### 1. Combined scoring (Chat + Loud Audio + Reactions)
```bash
# Windows PowerShell
python clip.py "https://www.youtube.com/watch?v=VIDEO_ID" --gameplay-confirmed --moment-source combined --min-score 3.0 --top 2

# macOS / Linux
python3 clip.py "https://www.youtube.com/watch?v=VIDEO_ID" --gameplay-confirmed --moment-source combined --min-score 3.0 --top 2
```

### 2. Local Video Testing
```bash
# Windows
python clip.py --file "C:\path\to\gameplay.mp4" --test --clip-len 30

# macOS / Linux
python3 clip.py --file "/path/to/gameplay.mp4" --test --clip-len 30
```
