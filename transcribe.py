#!/usr/bin/env python3
"""
Transcribe audio/video to SRT using OpenAI Whisper (large-v3).
Outputs .srt next to the input file.

Usage:
    python transcribe.py <file.mp3|file.mp4|...>

First run downloads the large-v3 model (~3GB). Cached after that.
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_or_video_file>")
        sys.exit(1)

    input_path = os.path.abspath(sys.argv[1])
    if not os.path.isfile(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Lazy imports so --help is fast
    try:
        import whisper
    except ImportError:
        print("Installing openai-whisper...")
        os.system(f"{sys.executable} -m pip install -U openai-whisper")
        import whisper

    base, _ = os.path.splitext(input_path)
    srt_path = base + ".srt"

    print(f"Input:  {input_path}")
    print(f"Output: {srt_path}")
    print()

    # Load model (downloads on first run, cached in ~/.cache/whisper/)
    print("Loading model: large-v3 (this downloads ~3GB on first run)...")
    model = whisper.load_model("large-v3")
    print("Model loaded.")
    print()

    # Transcribe
    print("Transcribing (using all CPU cores)...")
    result = model.transcribe(input_path, verbose=True)

    # Write SRT
    segments = result.get("segments", [])
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    print()
    print(f"Done. {len(segments)} segments written to: {srt_path}")


def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


if __name__ == "__main__":
    main()
