import { create } from "zustand";
import type { ChatMessage, Modality } from "../types/chat";

interface ChatState {
  messages: ChatMessage[];
  selectedModality: Modality | null;
  isLoading: boolean;
  error: string | null;
  addMessage: (msg: ChatMessage) => void;
  appendToMessage: (id: string, chunk: string) => void;
  setMessageContent: (id: string, content: string) => void;
  setMessageMeta: (
    id: string,
    meta: { citations?: ChatMessage["citations"]; visionResult?: ChatMessage["visionResult"] }
  ) => void;
  setMessages: (messages: ChatMessage[]) => void;
  removeLastMessages: (count: number) => void;
  setModality: (m: Modality | null) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  clearHistory: () => void;
}

let idCounter = 0;
function nextId(): string {
  return "msg-" + String(++idCounter) + "-" + String(Date.now());
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  selectedModality: null,
  isLoading: false,
  error: null,
  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, { ...msg, id: msg.id || nextId() }] })),
  appendToMessage: (id, chunk) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, content: (m.content ?? "") + chunk } : m
      ),
    })),
  setMessageContent: (id, content) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? { ...m, content } : m)),
    })),
  setMessageMeta: (id, meta) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, ...meta } : m
      ),
    })),
  setMessages: (messages) =>
    set({
      messages: messages.map((m) => ({ ...m, id: m.id || nextId() })),
    }),
  removeLastMessages: (count) =>
    set((s) => ({
      messages: s.messages.slice(0, Math.max(0, s.messages.length - count)),
    })),
  setModality: (m) => set({ selectedModality: m }),
  setLoading: (v) => set({ isLoading: v }),
  setError: (e) => set({ error: e }),
  clearHistory: () => set({ messages: [], error: null }),
}));
