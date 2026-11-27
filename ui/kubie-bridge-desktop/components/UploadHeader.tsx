import { KubieMark } from "./KubieMark";

type UploadHeaderProps = {
  username: string;
  onLogout: () => void;
};

export function UploadHeader({ username, onLogout }: UploadHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-black/[.08] bg-white px-6 py-3 dark:border-white/[.145] dark:bg-zinc-950">
      <div className="flex items-center gap-2">
        <KubieMark />
        <span className="text-lg font-semibold text-black dark:text-zinc-50">
          Kubie-Bridge
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-zinc-600 dark:text-zinc-400">{username}</span>
        <button
          type="button"
          onClick={onLogout}
          className="rounded-full border border-black/[.08] px-4 py-1.5 text-sm text-black transition-colors hover:bg-black/[.04] dark:border-white/[.145] dark:text-zinc-50 dark:hover:bg-[#1a1a1a]"
        >
          Log out
        </button>
      </div>
    </header>
  );
}
