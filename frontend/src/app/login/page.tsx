"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { useAuthStore } from "../../store/authStore";
import { ThemeToggle } from "../../components/ThemeToggle";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getErrorMessage(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    return first.msg ?? "Validation error";
  }
  return "Login failed";
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const setUser = useAuthStore((s) => s.setUser);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(getErrorMessage(data.detail));
      }
      const data = await res.json();
      setToken(data.access_token);
      const meRes = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      if (meRes.ok) {
        const me = await meRes.json();
        setUser({ id: me.id, email: me.email });
      }
      toast.success("Logged in");
      router.push("/chat");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Login failed. Check the backend is running.";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] p-4">
      <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 shadow-card">
        <div className="mb-4 flex justify-end">
          <ThemeToggle />
        </div>
        <h1 className="text-xl font-semibold text-[var(--primary)] mb-6">
          Sign in
        </h1>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full h-12 rounded-xl border border-[var(--border)] px-4 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--secondary)]"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full h-12 rounded-xl border border-[var(--border)] px-4 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--secondary)]"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 rounded-xl bg-[var(--brand)] text-[var(--brand-contrast)] font-medium hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <p className="mt-4 text-sm text-[var(--text-muted)]">
          No account?{" "}
          <Link href="/register" className="text-[var(--secondary)] hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
