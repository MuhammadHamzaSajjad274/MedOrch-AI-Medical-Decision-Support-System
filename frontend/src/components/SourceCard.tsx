"use client";

interface SourceCardProps {
  source: string;
  snippet: string;
  link?: string;
}

export function SourceCard({ source, snippet, link }: SourceCardProps) {
  return (
    <div className="rounded-xl bg-[var(--background)]/80 border border-[var(--border)] p-3 text-xs shadow-soft">
      <p className="font-medium text-[var(--primary)] truncate">{source}</p>
      <p className="text-[var(--text-muted)] line-clamp-2 mt-0.5">{snippet}</p>
      {link && (
        <a
          href={link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[var(--secondary)] hover:underline mt-1.5 inline-block font-medium"
        >
          Open source
        </a>
      )}
    </div>
  );
}
