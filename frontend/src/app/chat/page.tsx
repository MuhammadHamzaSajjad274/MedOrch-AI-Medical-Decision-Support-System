"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { ChatWindow } from "../../components/ChatWindow";
import { ChatInput } from "../../components/ChatInput";
import { Sidebar } from "../../components/Sidebar";
import { InsightsPanel } from "../../components/InsightsPanel";
import { ThemeToggle } from "../../components/ThemeToggle";
import { useChatStore } from "../../store/chatStore";
import { useAuthStore } from "../../store/authStore";

export default function ChatPage() {
  const error = useChatStore((s) => s.error);
  const isLoading = useChatStore((s) => s.isLoading);
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();

  useEffect(() => {
    if (!token) {
      router.replace("/");
    }
  }, [token, router]);

  if (!token) {
    return null;
  }

  return (
    <div className="flex h-screen bg-[var(--background)]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--surface)] px-6 py-4 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-[var(--primary)] tracking-tight">
                Medical Assistant
              </h1>
              <p className="mt-1 text-xs text-[var(--text-muted)] max-w-xl">
                This assistant provides general information only and is not a diagnosis.
                Always consult a healthcare professional for personal medical advice.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              {user ? (
                <>
                  <span className="text-sm text-[var(--text-muted)]">
                    {user.email}
                  </span>
                  <Link
                    href="/profile"
                    className="text-sm text-[var(--secondary)] hover:underline"
                  >
                    Profile
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      logout();
                      router.push("/");
                    }}
                    className="text-sm text-[var(--text-muted)] hover:underline"
                  >
                    Logout
                  </button>
                </>
              ) : null}
            </div>
          </div>
          {error && (
            <p className="text-sm text-[var(--danger)] mt-1" role="alert">
              {error}
            </p>
          )}
          {isLoading && (
            <p className="text-sm text-[var(--text-muted)] mt-1 flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-[var(--secondary)] animate-pulse" />
              Thinking...
            </p>
          )}
        </header>
        <main className="flex-1 flex min-h-0">
          <div className="flex-1 flex flex-col min-w-0">
            <ChatWindow />
            <ChatInput />
          </div>
          <div className="hidden xl:block w-80">
            <InsightsPanel />
          </div>
        </main>
      </div>
    </div>
  );
}
