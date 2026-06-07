import { useCallback, useRef } from "react";
import { fetchTtsChunks, fetchTtsWav } from "../lib/voiceApi";

function stripMarkdownForSpeech(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[#*_>-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function speakWithBrowser(text: string): Promise<void> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      resolve();
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 1;
    utterance.onend = () => resolve();
    utterance.onerror = () => resolve();
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  });
}

export interface UseTtsOptions {
  onStart?: () => void;
  onEnd?: () => void;
  useBrowserFallback?: boolean;
}

export function useTts(options?: UseTtsOptions) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const abortRef = useRef(false);
  const onStartRef = useRef(options?.onStart);
  const onEndRef = useRef(options?.onEnd);
  onStartRef.current = options?.onStart;
  onEndRef.current = options?.onEnd;

  const stop = useCallback(() => {
    abortRef.current = true;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    if (typeof window !== "undefined") {
      window.speechSynthesis?.cancel();
    }
  }, []);

  const playBlob = useCallback((blob: Blob): Promise<void> => {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        URL.revokeObjectURL(url);
        resolve();
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Audio playback failed"));
      };
      void audio.play().catch(reject);
    });
  }, []);

  const speak = useCallback(
    async (rawText: string) => {
      const text = stripMarkdownForSpeech(rawText);
      if (!text) return;

      stop();
      abortRef.current = false;
      onStartRef.current?.();

      try {
        const chunks = await fetchTtsChunks(text);
        if (abortRef.current) return;

        if (chunks.length > 0) {
          for (const chunk of chunks) {
            if (abortRef.current) break;
            await playBlob(chunk);
          }
          return;
        }

        const single = await fetchTtsWav(text);
        if (!abortRef.current) {
          await playBlob(single);
        }
      } catch {
        if (options?.useBrowserFallback !== false) {
          await speakWithBrowser(text);
        }
      } finally {
        onEndRef.current?.();
      }
    },
    [options?.useBrowserFallback, playBlob, stop]
  );

  return { speak, stop };
}
