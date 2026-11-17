"use client";

import { useId, useRef, useState } from "react";

const ACCEPTED_EXTENSION = ".py";

type FileDropZoneProps = {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
};

export function FileDropZone({ file, onFileChange, disabled = false }: FileDropZoneProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function accept(candidate: File | undefined) {
    if (!candidate) return;
    if (!candidate.name.toLowerCase().endsWith(ACCEPTED_EXTENSION)) {
      setError(`Only Python (${ACCEPTED_EXTENSION}) files are supported.`);
      return;
    }
    setError(null);
    onFileChange(candidate);
  }

  function clear() {
    setError(null);
    onFileChange(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="flex flex-col gap-1">
      <div
        data-testid="file-drop-zone"
        data-dragging={isDragging ? "true" : undefined}
        onDragEnter={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setIsDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (disabled) return;
          accept(e.dataTransfer.files?.[0]);
        }}
        className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center text-sm transition-colors ${
          isDragging
            ? "border-foreground bg-black/[.04] dark:bg-white/[.06]"
            : "border-black/[.15] dark:border-white/[.2]"
        } ${disabled ? "opacity-50" : ""}`}
      >
        {file ? (
          <>
            <span className="font-medium text-black dark:text-zinc-50">{file.name}</span>
            <button
              type="button"
              onClick={clear}
              disabled={disabled}
              className="text-zinc-600 underline hover:text-black disabled:no-underline dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Remove file
            </button>
          </>
        ) : (
          <>
            <span className="text-zinc-700 dark:text-zinc-300">
              Drag and drop your Python script here
            </span>
            <span className="text-zinc-500">or</span>
            <label
              htmlFor={inputId}
              className="cursor-pointer rounded-full border border-black/[.08] px-4 py-1.5 font-medium hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a]"
            >
              Browse files
            </label>
          </>
        )}
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={ACCEPTED_EXTENSION}
          aria-label="Attach file"
          disabled={disabled}
          onChange={(e) => accept(e.target.files?.[0])}
          className="sr-only"
        />
      </div>
      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
