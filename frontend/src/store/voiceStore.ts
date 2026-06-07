import { create } from "zustand";
import { persist } from "zustand/middleware";

export type VoiceMode = "draft" | "conversation";

interface VoiceState {
  voiceMode: VoiceMode;
  autoSpeakReply: boolean;
  autoReopenMic: boolean;
  isSpeaking: boolean;
  setVoiceMode: (m: VoiceMode) => void;
  setAutoSpeakReply: (v: boolean) => void;
  setAutoReopenMic: (v: boolean) => void;
  setIsSpeaking: (v: boolean) => void;
}

export const useVoiceStore = create<VoiceState>()(
  persist(
    (set) => ({
      voiceMode: "conversation",
      autoSpeakReply: true,
      autoReopenMic: true,
      isSpeaking: false,
      setVoiceMode: (m) =>
        set((s) => ({
          voiceMode: m,
          autoSpeakReply: m === "conversation" ? true : s.autoSpeakReply,
        })),
      setAutoSpeakReply: (v) => set({ autoSpeakReply: v }),
      setAutoReopenMic: (v) => set({ autoReopenMic: v }),
      setIsSpeaking: (v) => set({ isSpeaking: v }),
    }),
    {
      name: "medical-voice-settings",
      partialize: (s) => ({
        voiceMode: s.voiceMode,
        autoSpeakReply: s.autoSpeakReply,
        autoReopenMic: s.autoReopenMic,
      }),
    }
  )
);
