"use client";

import { useState, useEffect, useRef } from "react";
import { BulletEntry, BulletType, TaskState } from "@/types/bullet";
import {
  getEntriesByDate,
  addEntry,
  updateEntry,
  deleteEntry,
} from "@/lib/bullet-storage";
import BulletEntryItem from "./BulletEntryItem";

interface Props {
  date: string; // YYYY-MM-DD
}

const WEEKDAYS = ["日", "月", "火", "水", "木", "金", "土"];

function formatDateJa(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const weekday = WEEKDAYS[d.getDay()];
  return `${month}月${day}日（${weekday}）`;
}

export default function DailyLog({ date }: Props) {
  const [entries, setEntries] = useState<BulletEntry[]>([]);
  const [newType, setNewType] = useState<BulletType>("task");
  const [newContent, setNewContent] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setEntries(getEntriesByDate(date));
  }, [date]);

  const refresh = () => setEntries(getEntriesByDate(date));

  const handleAdd = () => {
    if (!newContent.trim()) return;
    addEntry({
      type: newType,
      content: newContent.trim(),
      state: "open",
      date,
      priority: false,
    });
    setNewContent("");
    refresh();
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleAdd();
    }
  };

  const handleUpdateState = (id: string, state: TaskState) => {
    updateEntry(id, { state });
    refresh();
  };

  const handleUpdateContent = (id: string, content: string) => {
    updateEntry(id, { content });
    refresh();
  };

  const handleTogglePriority = (id: string) => {
    const entry = entries.find((e) => e.id === id);
    if (entry) {
      updateEntry(id, { priority: !entry.priority });
      refresh();
    }
  };

  const handleDelete = (id: string) => {
    deleteEntry(id);
    refresh();
  };

  const tasks = entries.filter((e) => e.type === "task");
  const events = entries.filter((e) => e.type === "event");
  const notes = entries.filter((e) => e.type === "note");
  const doneCount = tasks.filter((e) => e.state === "done").length;

  return (
    <div>
      {/* Date header */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-zinc-800">
          {formatDateJa(date)}
        </h2>
        {tasks.length > 0 && (
          <span className="text-xs text-zinc-400">
            {doneCount}/{tasks.length} 完了
          </span>
        )}
      </div>

      {/* Entries grouped */}
      <div className="space-y-3">
        {events.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-indigo-400 font-medium mb-1">
              イベント
            </div>
            {events.map((entry) => (
              <BulletEntryItem
                key={entry.id}
                entry={entry}
                onUpdateState={handleUpdateState}
                onUpdateContent={handleUpdateContent}
                onTogglePriority={handleTogglePriority}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {tasks.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium mb-1">
              タスク
            </div>
            {tasks.map((entry) => (
              <BulletEntryItem
                key={entry.id}
                entry={entry}
                onUpdateState={handleUpdateState}
                onUpdateContent={handleUpdateContent}
                onTogglePriority={handleTogglePriority}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {notes.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-emerald-400 font-medium mb-1">
              メモ
            </div>
            {notes.map((entry) => (
              <BulletEntryItem
                key={entry.id}
                entry={entry}
                onUpdateState={handleUpdateState}
                onUpdateContent={handleUpdateContent}
                onTogglePriority={handleTogglePriority}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add new entry */}
      <div className="mt-4 flex items-center gap-2 border-t border-zinc-100 pt-3">
        <div className="flex gap-0.5 shrink-0">
          {(["task", "event", "note"] as BulletType[]).map((type) => (
            <button
              key={type}
              onClick={() => setNewType(type)}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${
                newType === type
                  ? "bg-zinc-800 text-white"
                  : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200"
              }`}
            >
              {type === "task" ? "タスク" : type === "event" ? "イベント" : "メモ"}
            </button>
          ))}
        </div>
        <input
          ref={inputRef}
          type="text"
          value={newContent}
          onChange={(e) => setNewContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="新しい項目を追加..."
          className="flex-1 text-sm bg-transparent outline-none text-zinc-800 placeholder:text-zinc-300"
        />
        <button
          onClick={handleAdd}
          disabled={!newContent.trim()}
          className="text-xs text-zinc-400 hover:text-zinc-600 disabled:opacity-30 px-2 py-1"
        >
          追加
        </button>
      </div>
    </div>
  );
}
