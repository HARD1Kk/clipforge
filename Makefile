.PHONY: clip preview list titles post schedule clean test sync streams streams-json help

help:
	@echo "ClipForge (uv-powered)"
	@echo "Available commands:"
	@echo "  make streams      - Find 100 live GTA 6 streams"
	@echo "  make streams-json - Find 100 live GTA 6 streams in JSON format"
	@echo "  make clip         - Search GTA 6 stream, auto-clip, and generate titles"
	@echo "  make titles       - Generate/refresh Groq LLM titles for output clips"
	@echo "  make preview      - Open and watch the latest video in media player"
	@echo "  make list         - Show all clips, scores, and approval status"
	@echo "  make post         - Publish latest approved clip immediately"
	@echo "  make schedule     - Schedule latest approved clip for tomorrow 12:00 PM"
	@echo "  make sync         - Install/sync all dependencies via uv"
	@echo "  make clean        - Clear output folder"
	@echo "  make test         - Run unit tests with uv"

sync:
	uv sync

streams:
	uv run python find_streams.py "GTA 6" --max 100

streams-json:
	uv run python find_streams.py "GTA 6" --max 100 --json

clip:
	uv run python clipper.py clip

titles:
	uv run python clipper.py titles

preview:
	uv run python clipper.py preview

list:
	uv run python clipper.py list

post:
	uv run python clipper.py post

schedule:
	uv run python clipper.py schedule

clean:
	uv run python clipper.py clean

test:
	uv run python -m unittest discover -s tests -v
