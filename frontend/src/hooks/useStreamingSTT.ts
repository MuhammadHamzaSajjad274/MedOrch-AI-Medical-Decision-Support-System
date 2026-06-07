import { useCallback, useMemo, useRef, useState } from "react";
import { transcribeWav } from "../lib/voiceApi";

const MIN_RECORD_MS = 400;

function floatTo16BitPCM(input: Float32Array): Int16Array {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i] ?? 0));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return output;
}

function encodeWavMono(samples: Float32Array, sampleRate: number): Blob {
  const pcm = floatTo16BitPCM(samples);
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const dataSize = pcm.length * 2;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  const writeString = (offset: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i));
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(36, "data");
  view.setUint32(40, dataSize, true);

  let offset = 44;
  for (let i = 0; i < pcm.length; i++) {
    view.setInt16(offset, pcm[i], true);
    offset += 2;
  }
  return new Blob([buffer], { type: "audio/wav" });
}

async function resampleTo16kMono(input: Float32Array, inputSampleRate: number): Promise<Float32Array> {
  if (inputSampleRate === 16000) return input;
  const lengthInSamples = Math.ceil((input.length * 16000) / inputSampleRate);
  const ctx = new OfflineAudioContext(1, lengthInSamples, 16000);
  const buffer = ctx.createBuffer(1, input.length, inputSampleRate);
  buffer.getChannelData(0).set(input);
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(ctx.destination);
  source.start();
  const rendered = await ctx.startRendering();
  return rendered.getChannelData(0);
}

function rmsLevel(samples: Float32Array): number {
  if (samples.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < samples.length; i++) {
    const v = samples[i] ?? 0;
    sum += v * v;
  }
  return Math.sqrt(sum / samples.length);
}

export interface StreamingSTT {
  supported: boolean;
  isRecording: boolean;
  isTranscribing: boolean;
  error: string | null;
  start: () => Promise<void>;
  stop: () => Promise<string>;
}

export function useStreamingSTT(): StreamingSTT {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef<number>(0);

  const supported = useMemo(() => {
    return (
      typeof window !== "undefined" &&
      !!navigator.mediaDevices?.getUserMedia &&
      !!(window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)
    );
  }, []);

  const start = useCallback(async () => {
    if (!supported || isRecording) return;
    setError(null);
    recordedChunksRef.current = [];
    startedAtRef.current = Date.now();

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });
    } catch {
      setError("Microphone permission denied. Allow mic access and try again.");
      return;
    }
    mediaStreamRef.current = stream;

    const preferredTypes = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "",
    ];
    let recorder: MediaRecorder | null = null;
    for (const mimeType of preferredTypes) {
      if (
        mimeType &&
        typeof MediaRecorder !== "undefined" &&
        !MediaRecorder.isTypeSupported(mimeType)
      ) {
        continue;
      }
      try {
        recorder = mimeType
          ? new MediaRecorder(stream, { mimeType })
          : new MediaRecorder(stream);
        break;
      } catch {
        // try next mime type
      }
    }
    if (!recorder) {
      setError("Could not initialize microphone recorder.");
      mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
      return;
    }

    recorder.ondataavailable = (evt: BlobEvent) => {
      if (evt.data && evt.data.size > 0) {
        recordedChunksRef.current.push(evt.data);
      }
    };
    recorderRef.current = recorder;
    recorder.start(250);
    setIsRecording(true);
  }, [supported, isRecording]);

  const stop = useCallback(async (): Promise<string> => {
    if (!isRecording) return "";
    setIsRecording(false);

    try {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        await new Promise<void>((resolve) => {
          const recorder = recorderRef.current;
          if (!recorder) {
            resolve();
            return;
          }
          recorder.onstop = () => resolve();
          recorder.stop();
        });
      }
      recorderRef.current = null;
      mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    } catch {
      // ignore cleanup errors
    }

    const elapsed = Date.now() - startedAtRef.current;
    const chunks = recordedChunksRef.current;
    recordedChunksRef.current = [];
    if (chunks.length === 0 || elapsed < MIN_RECORD_MS) {
      setError("Speak a little longer, then release the mic.");
      return "";
    }

    setIsTranscribing(true);
    try {
      const audioBlob = new Blob(chunks, { type: chunks[0]?.type || "audio/webm" });
      const arrayBuffer = await audioBlob.arrayBuffer();
      const Ctx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!Ctx) {
        throw new Error("AudioContext not supported");
      }
      const decodeCtx = new Ctx();
      const decoded = await decodeCtx.decodeAudioData(arrayBuffer.slice(0));
      await decodeCtx.close();

      const sourceData =
        decoded.numberOfChannels > 1
          ? (() => {
              const mono = new Float32Array(decoded.length);
              for (let i = 0; i < decoded.length; i++) {
                let sum = 0;
                for (let ch = 0; ch < decoded.numberOfChannels; ch++) {
                  sum += decoded.getChannelData(ch)[i] ?? 0;
                }
                mono[i] = sum / decoded.numberOfChannels;
              }
              return mono;
            })()
          : decoded.getChannelData(0);

      if (rmsLevel(sourceData) < 0.0015) {
        setError("No speech detected. Check your microphone.");
        return "";
      }

      const mono16k = await resampleTo16kMono(new Float32Array(sourceData), decoded.sampleRate);
      const wav = encodeWavMono(mono16k, 16000);
      const transcript = await transcribeWav(wav);
      if (!transcript) {
        setError("Could not understand audio. Try again.");
      }
      return transcript;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "STT failed";
      setError(msg);
      return "";
    } finally {
      setIsTranscribing(false);
    }
  }, [isRecording]);

  return { supported, isRecording, isTranscribing, error, start, stop };
}
