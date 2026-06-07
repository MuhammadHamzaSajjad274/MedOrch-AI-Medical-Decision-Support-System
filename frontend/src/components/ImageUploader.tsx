"use client";

import { useCallback, useState } from "react";
import { Upload } from "lucide-react";
import { useChatStore } from "../store/chatStore";

interface ImageUploaderProps {
  onImageSelect: (base64: string) => void;
}

export function ImageUploader({ onImageSelect }: ImageUploaderProps) {
  const [drag, setDrag] = useState(false);
  const modality = useChatStore((s) => s.selectedModality);

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file || !file.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = () => {
        const data = reader.result as string;
        if (data.startsWith("data:")) onImageSelect(data.split(",")[1] ?? data);
      };
      reader.readAsDataURL(file);
    },
    [onImageSelect]
  );

  return (
    <div
      className={
        "border-2 border-dashed rounded-xl p-4 text-center transition-colors " +
        (drag
          ? "border-[var(--secondary)] bg-[var(--secondary)]/10"
          : "border-[var(--border)] bg-[var(--background)]")
      }
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        handleFile(e.dataTransfer.files[0] ?? null);
      }}
    >
      <Upload className="mx-auto h-8 w-8 text-[var(--text-muted)] mb-2" />
      <p className="text-sm text-[var(--text-muted)]">
        Drag and drop an image, or click to select. Modality:{" "}
        {modality ?? "select in sidebar"}
      </p>
      <label
        htmlFor="image-upload"
        className="cursor-pointer text-[var(--secondary)] hover:underline text-sm mt-1 inline-block font-medium"
      >
        Choose file
      </label>
      <input
        type="file"
        accept="image/*"
        className="hidden"
        id="image-upload"
        onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}
