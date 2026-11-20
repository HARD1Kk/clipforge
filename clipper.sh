#!/usr/bin/env bash
# Fast uv-powered runner for Git Bash
if command -v uv &> /dev/null; then
    uv run python clipper.py "$@"
else
    python clipper.py "$@"
fi
