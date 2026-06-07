"use client";

import Link from "next/link";
import { Stethoscope, ShieldCheck, Sparkles } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { ThemeToggle } from "../components/ThemeToggle";

export default function Home() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-[var(--secondary)]" />
            <span className="font-semibold text-[var(--primary)]">Medical Assistant</span>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/login" className="text-sm text-[var(--text-muted)] hover:text-[var(--primary)]">
              Sign in
            </Link>
            <Link
              href="/register"
              className="text-sm rounded-lg bg-[var(--brand)] text-[var(--brand-contrast)] px-3 py-1.5 hover:opacity-90"
            >
              Register
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-16">
        <section className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-8 md:p-12 shadow-card">
          <div className="max-w-3xl">
            <p className="inline-flex items-center gap-2 text-xs uppercase tracking-wider text-[var(--secondary)] font-semibold">
              <Sparkles className="h-4 w-4" />
              AI Clinical Support
            </p>
            <h1 className="mt-3 text-4xl md:text-5xl font-bold text-[var(--primary)] leading-tight">
              Welcome to your multi-modal medical assistant
            </h1>
            <p className="mt-4 text-[var(--text-muted)] text-base md:text-lg leading-relaxed">
              Start with a secure account, then chat with text or medical images
              (MRI, X-ray, skin lesion) and receive AI assistance with citations.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              {token ? (
                <Link
                  href="/chat"
                  className="rounded-xl bg-[var(--brand)] text-[var(--brand-contrast)] px-5 py-3 font-medium hover:opacity-90"
                >
                  Continue to chat
                </Link>
              ) : (
                <>
                  <Link
                    href="/register"
                    className="rounded-xl bg-[var(--brand)] text-[var(--brand-contrast)] px-5 py-3 font-medium hover:opacity-90"
                  >
                    Create account
                  </Link>
                  <Link
                    href="/login"
                    className="rounded-xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] px-5 py-3 font-medium hover:bg-[var(--background)]"
                  >
                    Login to existing account
                  </Link>
                </>
              )}
            </div>

            {token && user && (
              <p className="mt-4 text-sm text-[var(--text-muted)]">
                Signed in as <span className="text-[var(--primary)] font-medium">{user.email}</span>
              </p>
            )}
          </div>
        </section>

        <section className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <p className="font-semibold text-[var(--primary)]">Image + Text Chat</p>
            <p className="mt-1 text-sm text-[var(--text-muted)]">Supports Brain MRI, Chest X-ray, and Skin Lesion workflows.</p>
          </div>
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <p className="font-semibold text-[var(--primary)]">Citations + History</p>
            <p className="mt-1 text-sm text-[var(--text-muted)]">Review sources and reopen previous consultations anytime.</p>
          </div>
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <p className="font-semibold text-[var(--primary)] inline-flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[var(--secondary)]" />
              Secure Access
            </p>
            <p className="mt-1 text-sm text-[var(--text-muted)]">Login/register first, then continue with protected chat and profile.</p>
          </div>
        </section>
      </main>
    </div>
  );
}
