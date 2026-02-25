# WhisperBatch

**Private speech-to-text transcription, entirely in your browser.**

No installs. No uploads. No servers. Your audio never leaves your device.

**[Launch WhisperBatch](https://innomen.github.io/WhisperBatch/)**

## How it works

WhisperBatch runs OpenAI's Whisper speech recognition model directly in your browser using [Transformers.js](https://huggingface.co/docs/transformers.js). The model downloads once from HuggingFace CDN and caches in your browser for offline use.

- **WebGPU acceleration** when available, with automatic WASM fallback
- **Multiple model sizes** from tiny (~40 MB) to large-v3-turbo (~800 MB)
- **Timestamped output** with SRT export
- **Supports audio and video files** — MP3, WAV, FLAC, OGG, M4A, MP4, WebM, and more

## Usage

1. Open the app in a modern browser (Chrome/Edge recommended for WebGPU)
2. Select a model size (large-v3-turbo is default for best accuracy)
3. Drop an audio or video file onto the upload area
4. Click **Transcribe** and wait for the result
5. Copy or download your transcript

The first run downloads the model (~800 MB for the default). Subsequent runs use the cached model instantly.

## Privacy

All audio processing happens locally in your browser. Nothing is uploaded to any server. The only network request is the one-time model download from HuggingFace CDN.

## Credits

Created by [@Innomen](https://github.com/Innomen) with help from Claude (Anthropic).
