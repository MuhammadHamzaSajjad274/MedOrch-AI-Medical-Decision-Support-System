"use client";

import type { DragEvent } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Image as ImageIcon, Mic, MicOff, Send } from "lucide-react";
import toast from "react-hot-toast";
import { useChatStore } from "../store/chatStore";
import { useVoiceStore } from "../store/voiceStore";
import { useAuthStore } from "../store/authStore";
import type { ChatRequest, ChatResponse } from "../types/chat";
import { useSpeech } from "../hooks/useSpeech";
import { useStreamingSTT } from "../hooks/useStreamingSTT";

const MIN_AUTO_SEND_LEN = 3;
const FILLER_PATTERN = /\b(um|uh|hmm|hm|er|ah)\b/gi;

function cleanForAutoSend(text: string): string {
  return text.replace(FILLER_PATTERN, "").replace(/\s+/g, " ").trim();
}

function shouldAutoSend(text: string): boolean {
  const cleaned = cleanForAutoSend(text);
  return cleaned.length >= MIN_AUTO_SEND_LEN;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type StreamCallbacks = {
  onChunk: (chunk: string) => void;
  onDone: (data: ChatResponse) => void;
  onError: (err: string) => void;
};

async function sendChatStream(
  body: ChatRequest,
  token: string | null,
  callbacks: StreamCallbacks
): Promise<void> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const t = await res.text();
    let msg = t || `HTTP ${res.status}`;
    try {
      const j = JSON.parse(t) as { detail?: string };
      if (j.detail) msg = j.detail;
    } catch {
      /* use raw msg */
    }
    callbacks.onError(msg);
    return;
  }
  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError("No response body");
    return;
  }
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const data = JSON.parse(line.slice(6)) as {
            type: string;
            content?: string;
            detail?: string;
            message?: string;
            citations?: ChatResponse["citations"];
            vision_result?: ChatResponse["vision_result"];
          };
          if (data.type === "status" && data.content === "thinking") {
            // Backend signals work has started; loading UI already reflects this.
            continue;
          }
          if (data.type === "chunk" && data.content) {
            callbacks.onChunk(data.content);
          } else if (data.type === "done") {
            callbacks.onDone({
              message: data.message ?? "",
              citations: data.citations ?? [],
              vision_result: data.vision_result ?? null,
            });
          } else if (data.type === "error") {
            callbacks.onError(data.detail ?? "Stream error");
          }
        } catch {
          /* skip malformed */
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export function ChatInput() {
  const [text, setText] = useState("");
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [isImageLoading, setIsImageLoading] = useState(false);
  const addMessage = useChatStore((s) => s.addMessage);
  const setLoading = useChatStore((s) => s.setLoading);
  const setError = useChatStore((s) => s.setError);
  const removeLastMessages = useChatStore((s) => s.removeLastMessages);
  const selectedModality = useChatStore((s) => s.selectedModality);
  const token = useAuthStore((s) => s.token);
  const submitRef = useRef<HTMLButtonElement>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const lastAutoSendRef = useRef<boolean>(false);
  const undoTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const voiceMode = useVoiceStore((s) => s.voiceMode);
  const setVoiceMode = useVoiceStore((s) => s.setVoiceMode);
  const autoSpeakReply = useVoiceStore((s) => s.autoSpeakReply);
  const setAutoSpeakReply = useVoiceStore((s) => s.setAutoSpeakReply);
  const autoReopenMic = useVoiceStore((s) => s.autoReopenMic);
  const setAutoReopenMic = useVoiceStore((s) => s.setAutoReopenMic);
  const isLoading = useChatStore((s) => s.isLoading);
  const isSpeaking = useVoiceStore((s) => s.isSpeaking);

  const streamingStt = useStreamingSTT();

  const handleUndo = useCallback(() => {
    if (undoTimeoutRef.current) {
      clearTimeout(undoTimeoutRef.current);
      undoTimeoutRef.current = null;
    }
    if (lastAutoSendRef.current) {
      removeLastMessages(2);
      lastAutoSendRef.current = false;
      toast.success("Undone");
    }
  }, [removeLastMessages]);

  const submitFromVoice = useCallback(
    (spoken: string) => {
      // If an image is still being converted to base64, wait instead of sending a half-formed request.
      if (isImageLoading) {
        toast.error("Still processing the image. Please wait a moment and try again.");
        return;
      }
      const cleaned = cleanForAutoSend(spoken);
      if (!cleaned || cleaned.length < MIN_AUTO_SEND_LEN) {
        setText((prev) => (prev ? `${prev} ${spoken}`.trim() : spoken));
        return;
      }
      const message = cleaned;
      const imageToSend = imageBase64;
      setText("");
      setImageBase64(null);
      addMessage({ id: "", role: "user", content: message, imageBase64: imageToSend ?? undefined });
      setLoading(true);
      setError(null);
      const body: ChatRequest = {
        message,
        modality: selectedModality ?? undefined,
        image_base64: imageToSend ?? undefined,
      };
      const streamId = `stream-${Date.now()}`;
      addMessage({
        id: streamId,
        role: "assistant",
        content: "",
        imageBase64: imageToSend ?? undefined,
      });
      lastAutoSendRef.current = true;
      if (undoTimeoutRef.current) clearTimeout(undoTimeoutRef.current);
      undoTimeoutRef.current = setTimeout(() => {
        undoTimeoutRef.current = null;
        lastAutoSendRef.current = false;
      }, 3000);
      toast(
        (t) => (
          <span className="flex items-center gap-2">
            Sent
            <button
              type="button"
              onClick={() => {
                handleUndo();
                toast.dismiss(t.id);
              }}
              className="text-[var(--secondary)] font-medium underline"
            >
              Undo
            </button>
          </span>
        ),
        { duration: 3000 }
      );
      sendChatStream(body, token, {
        onChunk: (chunk) => useChatStore.getState().appendToMessage(streamId, chunk),
        onDone: (data) => {
          useChatStore.getState().setMessageContent(streamId, data.message);
          useChatStore.getState().setMessageMeta(streamId, {
            citations: data.citations,
            visionResult: data.vision_result ?? undefined,
          });
          if (useVoiceStore.getState().autoSpeakReply && data.message?.trim()) {
            window.dispatchEvent(
              new CustomEvent("voice-speak", { detail: { text: data.message } })
            );
          }
        },
        onError: (errMsg) => {
          setError(errMsg);
          toast.error(errMsg);
          useChatStore.getState().setMessageContent(streamId, `Error: ${errMsg}`);
        },
      }).finally(() => setLoading(false));
    },
    [imageBase64, isImageLoading, selectedModality, token, addMessage, setLoading, setError, handleUndo]
  );

  const {
    supported: speechSupported,
    isRecording,
    transcript,
    startRecording,
    stopRecording,
    resetTranscript,
  } = useSpeech({
    onRecordingComplete: (spoken) => {
      if (voiceMode === "conversation" && shouldAutoSend(spoken)) {
        submitFromVoice(spoken);
      } else {
        setText((prev) => (prev ? `${prev.trim()} ${spoken.trim()}` : spoken.trim()));
      }
    },
    silenceTimeoutMs: voiceMode === "conversation" ? 800 : 0,
  });

  const [isDragOver, setIsDragOver] = useState(false);

  useEffect(() => {
    const onRequestMic = () => startRecording();
    window.addEventListener("voice-request-mic", onRequestMic);
    return () => window.removeEventListener("voice-request-mic", onRequestMic);
  }, [startRecording]);

  const handleImageSelect = (file: File | null) => {
    if (!file || !file.type.startsWith("image/")) return;
    setIsImageLoading(true);
    const reader = new FileReader();
    reader.onload = () => {
      const data = reader.result as string;
      if (data.startsWith("data:")) {
        const base64 = data.split(",")[1] ?? data;
        setImageBase64(base64);
      }
      setIsImageLoading(false);
    };
    reader.onerror = () => {
      setIsImageLoading(false);
      toast.error("Could not read image. Please try another file.");
    };
    reader.readAsDataURL(file);
  };

  const submit = async () => {
    const message = text.trim();
    if (!message && !imageBase64) return;
    if (isImageLoading) {
      toast.error("Still processing the image. Please wait a moment and try again.");
      return;
    }
    const imageToSend = imageBase64;
    setText("");
    setImageBase64(null);
    addMessage({
      id: "",
      role: "user",
      content: message || "[Image attached]",
      imageBase64: imageToSend ?? undefined,
    });
    setLoading(true);
    setError(null);
    const body: ChatRequest = {
      message: message || "What do you see in this image?",
      modality: selectedModality ?? undefined,
      image_base64: imageToSend ?? undefined,
    };
    const streamId = `stream-${Date.now()}`;
    addMessage({
      id: streamId,
      role: "assistant",
      content: "",
      imageBase64: imageToSend ?? undefined,
    });
    try {
      await sendChatStream(body, token, {
        onChunk: (chunk) => {
          useChatStore.getState().appendToMessage(streamId, chunk);
        },
        onDone: (data) => {
          useChatStore.getState().setMessageContent(streamId, data.message);
          useChatStore.getState().setMessageMeta(streamId, {
            citations: data.citations,
            visionResult: data.vision_result ?? undefined,
          });
          if (useVoiceStore.getState().autoSpeakReply && data.message?.trim()) {
            window.dispatchEvent(
              new CustomEvent("voice-speak", { detail: { text: data.message } })
            );
          }
        },
        onError: (errMsg) => {
          setError(errMsg);
          toast.error(errMsg);
          useChatStore.getState().setMessageContent(
            streamId,
            `Error: ${errMsg}`
          );
        },
      });
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : "Request failed";
      setError(errMsg);
      toast.error(errMsg);
      useChatStore.getState().setMessageContent(streamId, `Error: ${errMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!e.dataTransfer.types.includes("Files")) return;
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    // Only reset when leaving the wrapper, not children
    if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0] ?? null;
    handleImageSelect(file);
  };

  const statusLabel =
    streamingStt.isRecording || isRecording
      ? "Listening…"
      : streamingStt.isTranscribing
        ? "Transcribing…"
        : isLoading
          ? "Thinking…"
          : isSpeaking
            ? "Speaking…"
            : null;

  useEffect(() => {
    if (streamingStt.error) {
      toast.error(streamingStt.error);
    }
  }, [streamingStt.error]);

  return (
    <div
      className={`border-t bg-[var(--surface)] p-5 space-y-3 shadow-soft transition-colors ${
        isDragOver
          ? "border-[var(--secondary)]/70 bg-[var(--background)]/80"
          : "border-[var(--border)]"
      }`}
      onDragOver={handleDragOver}
      onDragEnter={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {(statusLabel || (speechSupported && voiceMode)) && (
        <div className="flex items-center justify-between gap-2">
          {statusLabel && (
            <span className="text-xs text-[var(--text-muted)] font-medium">{statusLabel}</span>
          )}
          {speechSupported && (
            <div className="flex items-center gap-2">
              <div className="flex rounded-lg border border-[var(--border)] p-0.5 bg-[var(--background)]">
                <button
                  type="button"
                  onClick={() => setVoiceMode("draft")}
                  className={`px-2 py-1 text-xs rounded-md transition-colors ${
                    voiceMode === "draft"
                      ? "bg-[var(--surface)] text-[var(--text-primary)] shadow-sm"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  Draft
                </button>
                <button
                  type="button"
                  onClick={() => setVoiceMode("conversation")}
                  className={`px-2 py-1 text-xs rounded-md transition-colors ${
                    voiceMode === "conversation"
                      ? "bg-[var(--surface)] text-[var(--text-primary)] shadow-sm"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  Conversation
                </button>
              </div>
              {voiceMode === "conversation" && (
                <label className="flex items-center gap-1 text-xs text-[var(--text-muted)] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoSpeakReply}
                    onChange={(e) => setAutoSpeakReply(e.target.checked)}
                    className="rounded"
                  />
                  Speak reply
                </label>
              )}
              {voiceMode === "conversation" && (
                <label className="flex items-center gap-1 text-xs text-[var(--text-muted)] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoReopenMic}
                    onChange={(e) => setAutoReopenMic(e.target.checked)}
                    className="rounded"
                  />
                  Auto-mic
                </label>
              )}
            </div>
          )}
        </div>
      )}
      {imageBase64 && (
        <p className="text-xs text-[var(--text-muted)]">
          Image attached. Send message to analyze.
        </p>
      )}
      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center justify-center h-10 w-10 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--text-muted)] hover:border-[var(--secondary)]/60 hover:text-[var(--secondary)] transition-colors"
        >
          <ImageIcon className="h-5 w-5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleImageSelect(e.target.files?.[0] ?? null)}
        />
        <button
          type="button"
          disabled={!streamingStt.supported && !speechSupported}
          onClick={async () => {
            // Draft mode: live browser captions (fast). Conversation: Whisper (accurate).
            const useWhisper = voiceMode === "conversation" && streamingStt.supported;

            if (useWhisper) {
              try {
                if (streamingStt.isRecording) {
                  const spoken = await streamingStt.stop();
                  if (spoken) {
                    if (shouldAutoSend(spoken)) {
                      submitFromVoice(spoken);
                    } else {
                      setText((prev) => (prev ? `${prev.trim()} ${spoken.trim()}` : spoken.trim()));
                    }
                  }
                } else {
                  await streamingStt.start();
                }
              } catch (e) {
                toast.error(e instanceof Error ? e.message : "Microphone access failed");
              }
              return;
            }

            if (!speechSupported) {
              toast.error("Voice input is not supported in this browser.");
              return;
            }
            if (isRecording) {
              stopRecording();
            } else {
              resetTranscript();
              startRecording();
            }
          }}
          className="flex items-center justify-center h-10 w-10 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--text-muted)] hover:border-[var(--secondary)]/60 hover:text-[var(--secondary)] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {streamingStt.isRecording || isRecording ? (
            <MicOff className="h-5 w-5 text-red-500" />
          ) : (
            <Mic className="h-5 w-5" />
          )}
        </button>
        <input
          type="text"
          value={isRecording && transcript ? `${text} ${transcript}`.trim() : text}
          onChange={(e) => !isRecording && setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && submit()}
          placeholder="Type a message..."
          className="flex-1 h-12 rounded-xl border border-[var(--border)] px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--secondary)] focus:border-transparent transition-shadow"
        />
        <button
          ref={submitRef}
          type="button"
          onClick={submit}
          className="h-12 rounded-xl bg-[var(--brand)] text-[var(--brand-contrast)] px-5 py-3 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[var(--secondary)] transition-opacity"
        >
          <Send className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
