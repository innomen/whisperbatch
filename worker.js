import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1';

env.allowLocalModels = false;

let transcriber = null;
let currentModel = null;

// Report capabilities on startup
async function reportCapabilities() {
  let webgpu = false;
  try {
    if (navigator.gpu) {
      const adapter = await navigator.gpu.requestAdapter();
      if (adapter) webgpu = true;
    }
  } catch {}

  self.postMessage({
    type: 'capabilities',
    webgpu,
    crossOriginIsolated: self.crossOriginIsolated,
    cores: navigator.hardwareConcurrency || 1,
  });
}

reportCapabilities();

// Handle commands from main thread
self.addEventListener('message', async (e) => {
  const msg = e.data;
  if (msg.type === 'load') {
    await loadModel(msg);
  } else if (msg.type === 'transcribe') {
    await doTranscribe(msg);
  }
});

async function loadModel({ modelId, useWebGPU }) {
  try {
    if (transcriber && currentModel === modelId) {
      self.postMessage({ type: 'model-ready', cached: true });
      return;
    }

    transcriber = null;
    currentModel = null;

    const dtype = useWebGPU
      ? { encoder_model: 'fp16', decoder_model_merged: 'q4' }
      : { encoder_model: 'q8', decoder_model_merged: 'q8' };
    const device = useWebGPU ? 'webgpu' : 'wasm';

    self.postMessage({ type: 'log', text: 'Loading model: ' + modelId + ' | device: ' + device + ' | dtype: ' + JSON.stringify(dtype) });

    transcriber = await pipeline('automatic-speech-recognition', modelId, {
      dtype,
      device,
      progress_callback: (progress) => {
        self.postMessage({ type: 'progress', progress });
      },
    });

    currentModel = modelId;
    self.postMessage({ type: 'model-ready', cached: false });
  } catch (err) {
    self.postMessage({ type: 'error', message: err.message, phase: 'model-loading' });
  }
}

async function doTranscribe({ audioData }) {
  try {
    let chunkCount = 0;
    const start = performance.now();

    const result = await transcriber(audioData, {
      chunk_length_s: 30,
      stride_length_s: 5,
      return_timestamps: true,
      language: null,
      chunk_callback: () => {
        chunkCount++;
        const elapsed = ((performance.now() - start) / 1000).toFixed(0);
        self.postMessage({ type: 'chunk-done', chunkCount, elapsed });
      },
    });

    const totalTime = ((performance.now() - start) / 1000).toFixed(1);

    // Send serializable result (strip non-cloneable properties)
    self.postMessage({
      type: 'result',
      text: result.text || '',
      chunks: (result.chunks || []).map(c => ({ timestamp: c.timestamp, text: c.text })),
      totalTime,
    });
  } catch (err) {
    self.postMessage({ type: 'error', message: err.message, phase: 'transcription' });
  }
}
