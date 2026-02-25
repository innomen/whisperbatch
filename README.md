# WhisperBatch

**Private speech-to-text transcription.**

No uploads. No servers. Your audio never leaves your device.

## Web App

**[Launch WhisperBatch](https://innomen.github.io/WhisperBatch/)**

Runs OpenAI Whisper directly in your browser using [Transformers.js](https://huggingface.co/docs/transformers.js). The model downloads once from HuggingFace CDN and caches in your browser.

- **Multi-threaded** — uses all CPU cores (requires cross-origin isolation via service worker)
- **WebGPU acceleration** when available, with automatic WASM fallback
- **Web Worker architecture** — UI never freezes, stop button works instantly
- **Multiple model sizes** from tiny (~40 MB) to large-v3-turbo (~800 MB)
- **Timestamped output** with SRT export
- **Supports audio and video files** — MP3, WAV, FLAC, OGG, M4A, MP4, WebM, and more

### Local development

Serve via HTTP (required for service worker / SharedArrayBuffer):

```bash
cd WhisperBatch
python -m http.server 8080
# Open http://localhost:8080
```

## Python CLI

For local use without a browser, `transcribe.py` uses OpenAI Whisper (large-v3) directly:

```bash
pip install openai-whisper
python transcribe.py yourfile.mp3
```

Outputs `yourfile.srt` in the same directory. Requires `ffmpeg`.

## Privacy

All processing happens locally. The only network request is the one-time model download.

## Credits

Created by [@Innomen](https://github.com/Innomen) with help from Claude (Anthropic).
