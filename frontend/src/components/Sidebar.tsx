"use client";

import { useEffect, useState } from "react";
import { History, Trash2 } from "lucide-react";
import { useChatStore } from "../store/chatStore";
import { useAuthStore } from "../store/authStore";
import type { Modality } from "../types/chat";
import type { ChatMessage } from "../types/chat";
import type { VisionResult } from "../types/chat";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ConsultationSummary {
  id: string;
  title: string;
  created_at: string;
}

interface ConsultationDetail {
  id: string;
  title: string;
  messages: Array<{
    role: string;
    content: string;
    citations?: Array<{ source: string; snippet: string; link?: string }>;
    vision_result?: {
      modality: string;
      label: string;
      confidence: number;
      class_names: string[];
      heatmap_base64?: string | null;
    };
  }>;
  created_at: string;
}

const MODALITIES: { value: Modality; label: string }[] = [
  { value: "brain_mri", label: "Brain MRI" },
  { value: "chest_xray", label: "Chest X-ray" },
  { value: "skin_lesion", label: "Skin Lesion" },
];

function formatConsultationDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return "";
  }
}

function isVisionModality(value: string): value is Modality {
  return value === "brain_mri" || value === "chest_xray" || value === "skin_lesion";
}

export function Sidebar() {
  const selectedModality = useChatStore((s) => s.selectedModality);
  const setModality = useChatStore((s) => s.setModality);
  const clearHistory = useChatStore((s) => s.clearHistory);
  const setMessages = useChatStore((s) => s.setMessages);
  const token = useAuthStore((s) => s.token);
  const [consultations, setConsultations] = useState<ConsultationSummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (!token) {
      setConsultations([]);
      return;
    }
    let cancelled = false;
    setLoadingHistory(true);
    fetch(`${API_BASE}/api/consultations`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : []))
      .then((data: ConsultationSummary[]) => {
        if (!cancelled) setConsultations(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (!cancelled) setConsultations([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function loadConsultation(id: string) {
    if (!token) return;
    const res = await fetch(`${API_BASE}/api/consultations/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const detail: ConsultationDetail = await res.json();
    const msgs: ChatMessage[] = (detail.messages || []).map((m, i) => ({
      id: `${detail.id}-${i}`,
      role: m.role === "user" ? "user" : "assistant",
      content: m.content ?? "",
      citations: m.citations,
      visionResult:
        m.vision_result && isVisionModality(m.vision_result.modality)
          ? ({ ...m.vision_result, modality: m.vision_result.modality } as VisionResult)
          : undefined,
    }));
    setMessages(msgs);
  }

  return (
    <aside className="w-64 border-r border-[var(--border)] bg-[var(--surface)] flex flex-col shadow-soft">
      <div className="p-4 border-b border-[var(--border)] flex items-center gap-2">
        <History className="h-5 w-5 text-[var(--secondary)]" />
        <span className="font-medium text-[var(--primary)]">Sessions</span>
      </div>
      {token && (
        <div className="p-4 border-b border-[var(--border)]">
          <p className="text-xs text-[var(--text-muted)] mb-2 uppercase tracking-wider">
            Consultation history
          </p>
          {loadingHistory ? (
            <p className="text-sm text-[var(--text-muted)]">Loading…</p>
          ) : consultations.length === 0 ? (
            <p className="text-sm text-[var(--text-muted)]">No past consultations</p>
          ) : (
            <ul className="space-y-1 max-h-40 overflow-y-auto">
              {consultations.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => loadConsultation(c.id)}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm bg-[var(--background)] border border-[var(--border)] hover:border-[var(--secondary)]/50 hover:bg-[var(--secondary)]/5 truncate"
                  >
                    <span className="block truncate text-[var(--text-primary)]">{c.title}</span>
                    <span className="block text-xs text-[var(--text-muted)]">
                      {formatConsultationDate(c.created_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      <div className="p-4 flex-1">
        <p className="text-xs text-[var(--text-muted)] mb-2 uppercase tracking-wider">
          Image modality
        </p>
        <div className="space-y-1">
          {MODALITIES.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => setModality(value)}
              className={`w-full text-left px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                selectedModality === value
                  ? "bg-[var(--secondary)] text-[var(--brand-contrast)] shadow-soft"
                  : "bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--secondary)]/50 hover:bg-[var(--secondary)]/5"
              }`}
            >
              {label}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setModality(null)}
            className="w-full text-left px-3 py-2.5 rounded-xl text-sm text-[var(--text-muted)] bg-[var(--background)] border border-[var(--border)] hover:bg-[var(--background)] hover:border-[var(--border)]"
          >
            None
          </button>
        </div>
      </div>
      <div className="p-4 border-t border-[var(--border)]">
        <button
          type="button"
          onClick={clearHistory}
          className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--primary)] text-sm transition-colors"
        >
          <Trash2 className="h-4 w-4" />
          Clear history
        </button>
      </div>
    </aside>
  );
}
