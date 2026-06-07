const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function warmupVoiceModels(): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/voice/warmup`, { method: "POST" });
  } catch {
    // Non-fatal; first request may be slower.
  }
}

export async function transcribeWav(wav: Blob): Promise<string> {
  const form = new FormData();
  form.append("file", wav, "speech.wav");
  const res = await fetch(`${API_BASE}/api/voice/stt`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `STT failed (${res.status})`);
  }
  const data = (await res.json()) as { text?: string };
  return (data.text ?? "").trim();
}

export async function fetchTtsWav(text: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/voice/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`TTS failed (${res.status})`);
  }
  return res.blob();
}

/** Base64 WAV chunks, one per line — play sequentially for low time-to-first-audio. */
export async function fetchTtsChunks(text: string): Promise<Blob[]> {
  const res = await fetch(`${API_BASE}/api/voice/tts/chunks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`TTS chunks failed (${res.status})`);
  }
  const raw = await res.text();
  if (!raw.trim()) return [];
  const lines = raw.split("\n").filter(Boolean);
  return lines.map((line) => {
    const binary = atob(line);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new Blob([bytes], { type: "audio/wav" });
  });
}
