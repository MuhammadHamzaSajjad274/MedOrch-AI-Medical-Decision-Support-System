"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { useAuthStore } from "../../store/authStore";
import { ThemeToggle } from "../../components/ThemeToggle";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ProfileData {
  user_id: string;
  name: string;
  age: number | null;
  sex: string;
  allergies: string;
  conditions: string;
  medications: string;
  preferences: string;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    fetch(`${API_BASE}/api/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        setProfile(data || null);
      })
      .finally(() => setLoading(false));
  }, [token, router]);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!token || !profile) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: profile.name,
          age: profile.age ?? undefined,
          sex: profile.sex,
          allergies: profile.allergies,
          conditions: profile.conditions,
          medications: profile.medications,
          preferences: profile.preferences,
        }),
      });
      if (!res.ok) throw new Error("Failed to save");
      const data = await res.json();
      setProfile(data);
      toast.success("Profile saved");
    } catch {
      toast.error("Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
        <p className="text-[var(--text-muted)]">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--background)] p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-[var(--primary)]">
            Patient profile
          </h1>
          <div className="flex gap-2 items-center">
            <ThemeToggle />
            <Link
              href="/chat"
              className="px-4 py-2 rounded-xl border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--surface)]"
            >
              Back to chat
            </Link>
            <button
              type="button"
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="px-4 py-2 rounded-xl border border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--surface)]"
            >
              Logout
            </button>
          </div>
        </div>
        {user && (
          <p className="text-sm text-[var(--text-muted)] mb-4">
            Logged in as {user.email}
          </p>
        )}
        {profile && (
          <form
            onSubmit={submit}
            className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-card space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
                Name
              </label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) =>
                  setProfile((p) => (p ? { ...p, name: e.target.value } : p))
                }
                className="w-full h-12 rounded-xl border border-[var(--border)] px-4 text-[var(--text-primary)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
                Age
              </label>
              <input
                type="number"
                min={1}
                max={150}
                value={profile.age ?? ""}
                onChange={(e) =>
                  setProfile((p) => ({
                    ...p!,
                    age: e.target.value ? parseInt(e.target.value, 10) : null,
                  }))
                }
                className="w-full h-12 rounded-xl border border-[var(--border)] px-4 text-[var(--text-primary)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
                Sex
              </label>
              <input
                type="text"
                value={profile.sex}
                onChange={(e) =>
                  setProfile((p) => (p ? { ...p, sex: e.target.value } : p))
                }
                placeholder="e.g. Male, Female"
                className="w-full h-12 rounded-xl border border-[var(--border)] px-4 text-[var(--text-primary)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
                Allergies
              </label>
              <textarea
                value={profile.allergies}
                onChange={(e) =>
                  setProfile((p) => (p ? { ...p, allergies: e.target.value } : p))
                }
                rows={2}
                className="w-full rounded-xl border border-[var(--border)] px-4 py-3 text-[var(--text-primary)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
                Conditions
              </label>
              <textarea
                value={profile.conditions}
                onChange={(e) =>
                  setProfile((p) =>
                    p ? { ...p, conditions: e.target.value } : p
                  )
                }
                rows={2}
                placeholder="e.g. Diabetes, Hypertension"
                className="w-full rounded-xl border border-[var(--border)] px-4 py-3 text-[var(--text-primary)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
                Medications
              </label>
              <textarea
                value={profile.medications}
                onChange={(e) =>
                  setProfile((p) =>
                    p ? { ...p, medications: e.target.value } : p
                  )
                }
                rows={2}
                className="w-full rounded-xl border border-[var(--border)] px-4 py-3 text-[var(--text-primary)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">
                Preferences
              </label>
              <textarea
                value={profile.preferences}
                onChange={(e) =>
                  setProfile((p) =>
                    p ? { ...p, preferences: e.target.value } : p
                  )
                }
                rows={2}
                placeholder="e.g. Language, communication style"
                className="w-full rounded-xl border border-[var(--border)] px-4 py-3 text-[var(--text-primary)]"
              />
            </div>
            <button
              type="submit"
              disabled={saving}
              className="w-full h-12 rounded-xl bg-[var(--brand)] text-[var(--brand-contrast)] font-medium hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save profile"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
