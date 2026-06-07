import { useCallback, useEffect, useRef, useState } from "react";

type RecognitionResultLike = {
  0?: { transcript?: string };
  length?: number;
  item?: (i: number) => { transcript?: string };
};

type RecognitionEventLike = {
  results?: ArrayLike<RecognitionResultLike>;
};

type RecognitionErrorEventLike = {
  error?: string;
  message?: string;
};

type RecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: RecognitionEventLike) => void) | null;
  onerror: ((event: RecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type RecognitionConstructor = new () => RecognitionInstance;

interface SpeechRecognitionWindow extends Window {
  SpeechRecognition?: RecognitionConstructor;
  webkitSpeechRecognition?: RecognitionConstructor;
}

export interface UseSpeech {
  supported: boolean;
  isRecording: boolean;
  isSpeaking: boolean;
  transcript: string;
  startRecording: () => void;
  stopRecording: () => void;
  resetTranscript: () => void;
  speak: (text: string) => void;
  cancelSpeak: () => void;
}

function getTranscriptFromResults(results: ArrayLike<RecognitionResultLike>): string {
  let full = "";
  for (let i = 0; i < results.length; i++) {
    const result = results[i];
    const alt = result?.[0] ?? result?.item?.(0);
    if (alt?.transcript) full += (full ? " " : "") + alt.transcript.trim();
  }
  return full.trim();
}

export function useSpeech(options?: {
  onRecordingComplete?: (text: string) => void;
  /** Auto-stop and call onRecordingComplete after this ms of silence. 0 = manual stop only. */
  silenceTimeoutMs?: number;
  onSpeakStart?: () => void;
  onSpeakEnd?: () => void;
}): UseSpeech {
  const [supported, setSupported] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");

  const recognitionRef = useRef<RecognitionInstance | null>(null);
  const transcriptRef = useRef("");
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onCompleteRef = useRef(options?.onRecordingComplete);
  onCompleteRef.current = options?.onRecordingComplete;
  const onSpeakStartRef = useRef(options?.onSpeakStart);
  const onSpeakEndRef = useRef(options?.onSpeakEnd);
  onSpeakStartRef.current = options?.onSpeakStart;
  onSpeakEndRef.current = options?.onSpeakEnd;
  const silenceTimeoutMs = options?.silenceTimeoutMs ?? 0;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const win = window as SpeechRecognitionWindow;
    setSupported(
      Boolean(win.SpeechRecognition ?? win.webkitSpeechRecognition),
    );
  }, []);

  const ensureRecognition = useCallback(() => {
    if (!supported || typeof window === "undefined") return null;
    if (recognitionRef.current) return recognitionRef.current;

    const win = window as SpeechRecognitionWindow;
    const Ctor = win.SpeechRecognition ?? win.webkitSpeechRecognition;
    if (!Ctor) return null;

    const recognition = new Ctor();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event: RecognitionEventLike) => {
      const results = event.results;
      if (!results?.length) return;
      const text = getTranscriptFromResults(results);
      if (text) {
        transcriptRef.current = text;
        setTranscript(text);
        if (silenceTimeoutMs > 0) {
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = setTimeout(() => {
            silenceTimerRef.current = null;
            try {
              recognitionRef.current?.stop();
            } catch {
              setIsRecording(false);
            }
          }, silenceTimeoutMs);
        }
      }
    };

    recognition.onerror = (e: RecognitionErrorEventLike) => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      if (e.error !== "aborted" && e.error !== "no-speech") {
        console.warn("Speech recognition error:", e.error ?? e.message);
      }
      setIsRecording(false);
    };

    recognition.onend = () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      const finalText = transcriptRef.current;
      transcriptRef.current = "";
      setIsRecording(false);
      setTranscript("");
      if (finalText) onCompleteRef.current?.(finalText);
    };

    recognitionRef.current = recognition;
    return recognition;
  }, [supported, silenceTimeoutMs]);

  const startRecording = useCallback(() => {
    const recognition = ensureRecognition();
    if (!recognition || isRecording) return;
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    transcriptRef.current = "";
    setTranscript("");
    setIsRecording(true);
    try {
      recognition.start();
    } catch (e) {
      console.warn("Speech start failed:", e);
      setIsRecording(false);
    }
  }, [ensureRecognition, isRecording]);

  const stopRecording = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    try {
      recognition.stop();
    } catch {
      setIsRecording(false);
    }
  }, []);

  const resetTranscript = useCallback(() => setTranscript(""), []);

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !text.trim()) return;
    const synth = window.speechSynthesis;
    if (!synth) return;

    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = () => {
      setIsSpeaking(false);
      onSpeakEndRef.current?.();
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      onSpeakEndRef.current?.();
    };

    setIsSpeaking(true);
    onSpeakStartRef.current?.();
    synth.speak(utterance);
  }, []);

  const cancelSpeak = useCallback(() => {
    if (typeof window === "undefined") return;
    const synth = window.speechSynthesis;
    if (!synth) return;
    synth.cancel();
    setIsSpeaking(false);
  }, []);

  return {
    supported,
    isRecording,
    isSpeaking,
    transcript,
    startRecording,
    stopRecording,
    resetTranscript,
    speak,
    cancelSpeak,
  };
}

