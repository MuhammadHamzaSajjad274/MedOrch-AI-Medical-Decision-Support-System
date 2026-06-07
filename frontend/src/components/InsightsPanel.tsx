"use client";

import { useMemo } from "react";
import { useChatStore } from "../store/chatStore";
import { SourceCard } from "./SourceCard";

export function InsightsPanel() {
  const messages = useChatStore((s) => s.messages);

  const lastAssistant = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant"),
    [messages]
  );

  if (!lastAssistant) {
    return (
      <div className="h-full p-4 text-xs text-[var(--text-muted)] bg-[var(--surface)] border-l border-[var(--border)]">
        Insights will appear here after the assistant responds, including imaging
        context and sources.
      </div>
    );
  }

  const vision = lastAssistant.visionResult;
  const citations = lastAssistant.citations || [];

  return (
    <aside className="h-full flex flex-col bg-[var(--surface)] border-l border-[var(--border)]">
      <div className="p-4 border-b border-[var(--border)]">
        <h2 className="text-sm font-semibold text-[var(--primary)]">Insights</h2>
        <p className="text-xs text-[var(--text-muted)]">
          Supporting information for the latest answer.
        </p>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {vision && (
          <section className="rounded-xl border border-[var(--border)] p-3 space-y-2">
            <p className="text-xs font-semibold text-[var(--primary)]">
              Imaging result ({vision.modality.replace("_", " ")}):
            </p>
            <p className="text-xs text-[var(--text-muted)]">{vision.label}</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 rounded-full bg-[var(--border)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[var(--secondary)] transition-all"
                  style={{ width: `${Math.round(vision.confidence * 100)}%` }}
                />
              </div>
              <span className="text-[10px] text-[var(--text-muted)] tabular-nums">
                {(vision.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </section>
        )}

        {citations.length > 0 && (
          <section className="space-y-2">
            <p className="text-xs font-semibold text-[var(--primary)]">Sources</p>
            {citations.map((c, i) => (
              <SourceCard
                key={i}
                source={c.source}
                snippet={c.snippet}
                link={c.link}
              />
            ))}
          </section>
        )}

        {!vision && citations.length === 0 && (
          <p className="text-xs text-[var(--text-muted)]">
            No additional context was used for this answer.
          </p>
        )}
      </div>
    </aside>
  );
}

