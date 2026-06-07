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
    const first = detail[0] as { msg?: string; loc?: unknown };
    return first.msg ?? "Validation error";
  }
  return "Registration failed";
}

export default function RegisterPage() {
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
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = getErrorMessage(data.detail);
        throw new Error(message);
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
      toast.success("Account created");
      router.push("/chat");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Registration failed. Check the backend is running and CORS allows this origin.";
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
          Create account
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
              minLength={3}
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
              minLength={6}
              className="w-full h-12 rounded-xl border border-[var(--border)] px-4 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--secondary)]"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 rounded-xl bg-[var(--brand)] text-[var(--brand-contrast)] font-medium hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>
        <p className="mt-4 text-sm text-[var(--text-muted)]">
          Already have an account?{" "}
          <Link href="/login" className="text-[var(--secondary)] hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
