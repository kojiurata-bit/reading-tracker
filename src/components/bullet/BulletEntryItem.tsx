"use client";

import { BulletEntry, BulletType, TaskState, BULLET_SYMBOLS } from "@/types/bullet";

interface Props {
  entry: BulletEntry;
  onUpdateState: (id: string, state: TaskState) => void;
  onUpdateContent: (id: string, content: string) => void;
  onTogglePriority: (id: string) => void;
  onDelete: (id: string) => void;
}

const stateStyles: Record<TaskState, string> = {
  open: "text-zinc-800",
  done: "text-zinc-400 line-through",
  migrated: "text-blue-400 line-through",
  scheduled: "text-amber-500",
  cancelled: "text-zinc-300 line-through",
};

const bulletColors: Record<BulletType, string> = {
  task: "text-zinc-600",
  event: "text-indigo-500",
  note: "text-emerald-500",
};

export default function BulletEntryItem({
  entry,
  onUpdateState,
  onUpdateContent,
  onTogglePriority,
  onDelete,
}: Props) {
  const nextState: Record<TaskState, TaskState> = {
    open: "done",
    done: "open",
    migrated: "open",
    scheduled: "open",
    cancelled: "open",
  };

  const handleStateClick = () => {
    onUpdateState(entry.id, nextState[entry.state]);
  };

  const stateOverlay =
    entry.state === "done"
      ? "×"
      : entry.state === "migrated"
        ? ">"
        : entry.state === "scheduled"
          ? "<"
          : null;

  return (
    <div className="group flex items-start gap-1.5 py-1 px-1 -mx-1 rounded hover:bg-zinc-50 transition-colors">
      {/* Priority marker */}
      <button
        onClick={() => onTogglePriority(entry.id)}
        className={`shrink-0 w-4 text-center text-xs mt-0.5 ${
          entry.priority ? "text-red-400" : "text-transparent group-hover:text-zinc-200"
        } transition-colors`}
        title="優先度を切り替え"
      >
        *
      </button>

      {/* Bullet / State toggle */}
      <button
        onClick={handleStateClick}
        className={`shrink-0 w-5 h-5 flex items-center justify-center text-sm font-bold relative ${bulletColors[entry.type]} transition-colors`}
        title="状態を切り替え"
      >
        <span className={entry.state !== "open" ? "opacity-30" : ""}>
          {BULLET_SYMBOLS[entry.type]}
        </span>
        {stateOverlay && (
          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-zinc-600">
            {stateOverlay}
          </span>
        )}
      </button>

      {/* Content */}
      <input
        type="text"
        value={entry.content}
        onChange={(e) => onUpdateContent(entry.id, e.target.value)}
        className={`flex-1 bg-transparent text-sm outline-none ${stateStyles[entry.state]} placeholder:text-zinc-300`}
        placeholder="内容を入力..."
      />

      {/* Context menu */}
      <div className="shrink-0 opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
        {entry.type === "task" && entry.state === "open" && (
          <>
            <button
              onClick={() => onUpdateState(entry.id, "migrated")}
              className="text-xs text-blue-400 hover:text-blue-600 px-1"
              title="移動"
            >
              &gt;
            </button>
            <button
              onClick={() => onUpdateState(entry.id, "scheduled")}
              className="text-xs text-amber-400 hover:text-amber-600 px-1"
              title="予定"
            >
              &lt;
            </button>
          </>
        )}
        <button
          onClick={() => onDelete(entry.id)}
          className="text-xs text-zinc-300 hover:text-red-400 px-1"
          title="削除"
        >
          ×
        </button>
      </div>
    </div>
  );
}
