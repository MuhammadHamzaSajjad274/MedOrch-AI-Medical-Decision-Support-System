"use client";

export function SkeletonLoader() {
  return (
    <div className="flex w-full justify-start">
      <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-surface border border-[var(--border)] shadow-soft animate-pulse">
        <div className="flex gap-2">
          <div className="h-3 w-3 rounded-full bg-[var(--secondary)]/30" />
          <div className="h-3 flex-1 rounded bg-[var(--text-muted)]/30 max-w-[200px]" />
        </div>
        <div className="mt-2 h-3 rounded bg-[var(--text-muted)]/20 w-full" />
        <div className="mt-1 h-3 rounded bg-[var(--text-muted)]/20 w-3/4" />
      </div>
    </div>
  );
}
