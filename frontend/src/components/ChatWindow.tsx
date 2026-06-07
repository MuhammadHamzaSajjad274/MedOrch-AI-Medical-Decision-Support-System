"use client";

import { useCallback, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Volume2 } from "lucide-react";
import { useChatStore } from "../store/chatStore";
import { useVoiceStore } from "../store/voiceStore";
import { useTts } from "../hooks/useTts";
import { warmupVoiceModels } from "../lib/voiceApi";
import { SourceCard } from "./SourceCard";
import { SkeletonLoader } from "./SkeletonLoader";
import type { ChatMessage as ChatMessageType } from "../types/chat";

interface MessageBubbleProps {
  msg: ChatMessageType;
  playTts?: (text: string) => void;
}

function MessageBubble({ msg, playTts }: MessageBubbleProps) {
  const isUser = msg.role === "user";
  const bubbleBase =
    "max-w-[72%] md:max-w-[60%] rounded-2xl px-5 py-3.5 shadow-card transition-transform duration-150 " +
    (isUser
      ? "bg-[var(--brand)] text-[var(--brand-contrast)] border-l-4 border-[var(--accent)] hover:translate-y-0.5"
      : "bg-[var(--surface)] text-[var(--text-primary)] border border-[var(--border)] border-l-4 border-l-[var(--secondary)] hover:translate-y-0.5");

  return (
    <div className={"flex w-full " + (isUser ? "justify-end" : "justify-start")}>
      <div className={bubbleBase}>
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            {msg.content}
          </p>
        ) : (
          <>
            <div className="flex justify-end mb-1">
              {playTts && (
                <button
                  type="button"
                  onClick={() => playTts(msg.content)}
                  className="inline-flex items-center justify-center rounded-full bg-[var(--background)] text-[var(--text-muted)] hover:text-[var(--secondary)] hover:bg-[var(--surface)] transition-colors h-7 w-7"
                  aria-label="Play assistant message"
                >
                  <Volume2 className="h-4 w-4" aria-hidden="true" />
                </button>
              )}
            </div>
            <div className="prose prose-sm max-w-none text-sm leading-relaxed text-[var(--text-primary)] whitespace-pre-wrap break-words">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          </>
        )}

        {msg.visionResult && (
          <div className="mt-3 pt-3 border-t border-[var(--border)] space-y-2">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="font-medium text-[var(--text-primary)]">Vision: </span>
              <span className="text-[var(--text-muted)]">{msg.visionResult.label}</span>
              <div className="flex-1 min-w-[80px] max-w-[120px] h-2 rounded-full bg-[var(--border)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[var(--secondary)] transition-all"
                  style={{ width: `${Math.round(msg.visionResult.confidence * 100)}%` }}
                />
              </div>
              <span className="text-[var(--text-muted)] tabular-nums">
                {(msg.visionResult.confidence * 100).toFixed(0)}%
              </span>
            </div>
            {(msg.visionResult.heatmap_base64 || msg.imageBase64) && (
              <div className="flex flex-wrap gap-2 mt-2">
                {msg.imageBase64 && (
                  <div className="flex flex-col items-center">
                    <p className="text-[10px] text-[var(--text-muted)] mb-1">Original</p>
                    <img
                      src={`data:image/jpeg;base64,${msg.imageBase64}`}
                      alt="Uploaded"
                      className="rounded-lg max-h-32 object-contain border border-[var(--border)]"
                    />
                  </div>
                )}
                {msg.visionResult.heatmap_base64 && (
                  <div className="flex flex-col items-center">
                    <p className="text-[10px] text-[var(--text-muted)] mb-1">Heatmap</p>
                    <img
                      src={`data:image/png;base64,${msg.visionResult.heatmap_base64}`}
                      alt="Grad-CAM"
                      className="rounded-lg max-h-32 object-contain border border-[var(--border)]"
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {msg.citations && msg.citations.length > 0 && (
          <div className="mt-3 space-y-2">
            {msg.citations.map((c, i) => (
              <SourceCard key={i} source={c.source} snippet={c.snippet} link={c.link} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function ChatWindow() {
  const messages = useChatStore((s) => s.messages);
  const isLoading = useChatStore((s) => s.isLoading);
  const endRef = useRef<HTMLDivElement>(null);
  const lastSpokenAtRef = useRef(0);
  const autoSpeakReply = useVoiceStore((s) => s.autoSpeakReply);
  const autoReopenMic = useVoiceStore((s) => s.autoReopenMic);
  const setIsSpeaking = useVoiceStore((s) => s.setIsSpeaking);

  const { speak, stop } = useTts({
    onStart: () => setIsSpeaking(true),
    onEnd: () => {
      setIsSpeaking(false);
      if (autoReopenMic) {
        window.dispatchEvent(new CustomEvent("voice-request-mic"));
      }
    },
    useBrowserFallback: true,
  });

  const speakOnce = useCallback(
    (text: string) => {
      const now = Date.now();
      if (now - lastSpokenAtRef.current < 800) return;
      lastSpokenAtRef.current = now;
      void speak(text);
    },
    [speak]
  );

  useEffect(() => {
    void warmupVoiceModels();
  }, []);

  useEffect(() => {
    const onSpeak = (evt: Event) => {
      if (!autoSpeakReply) return;
      const detail = (evt as CustomEvent<{ text?: string }>).detail;
      if (detail?.text) speakOnce(detail.text);
    };
    window.addEventListener("voice-speak", onSpeak);
    return () => window.removeEventListener("voice-speak", onSpeak);
  }, [autoSpeakReply, speakOnce]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => () => stop(), [stop]);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[var(--background)]">
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full min-h-[200px] text-[var(--text-muted)] text-sm">
          Send a message or upload an image to get started.
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          msg={msg}
          playTts={msg.role === "assistant" ? (t) => speakOnce(t) : undefined}
        />
      ))}
      {isLoading && <SkeletonLoader />}
      <div ref={endRef} />
    </div>
  );
}
