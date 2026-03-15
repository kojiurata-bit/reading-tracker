"use client";

import { useState, useEffect, useRef } from "react";
import { BulletEntry, TaskState } from "@/types/bullet";
import { Collection } from "@/types/bullet";
import {
  getCollections,
  addCollection,
  deleteCollection,
  getEntriesByCollection,
  addEntry,
  updateEntry,
  deleteEntry,
} from "@/lib/bullet-storage";
import BulletEntryItem from "./BulletEntryItem";

export default function CollectionView() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [activeCollection, setActiveCollection] = useState<string | null>(null);
  const [entries, setEntries] = useState<BulletEntry[]>([]);
  const [newName, setNewName] = useState("");
  const [newContent, setNewContent] = useState("");
  const [showNewForm, setShowNewForm] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setCollections(getCollections());
  }, []);

  useEffect(() => {
    if (activeCollection) {
      setEntries(getEntriesByCollection(activeCollection));
    }
  }, [activeCollection]);

  const refreshEntries = () => {
    if (activeCollection) {
      setEntries(getEntriesByCollection(activeCollection));
    }
  };

  const handleAddCollection = () => {
    if (!newName.trim()) return;
    const col = addCollection(newName.trim());
    setCollections(getCollections());
    setActiveCollection(col.id);
    setNewName("");
    setShowNewForm(false);
  };

  const handleDeleteCollection = (id: string) => {
    deleteCollection(id);
    setCollections(getCollections());
    if (activeCollection === id) {
      setActiveCollection(null);
      setEntries([]);
    }
  };

  const handleAddEntry = () => {
    if (!newContent.trim() || !activeCollection) return;
    const today = new Date().toISOString().split("T")[0];
    addEntry({
      type: "task",
      content: newContent.trim(),
      state: "open",
      date: today,
      priority: false,
      collection: activeCollection,
    });
    setNewContent("");
    refreshEntries();
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleAddEntry();
    }
  };

  return (
    <div>
      {/* Collection list */}
      <div className="flex items-center gap-2 flex-wrap mb-4">
        {collections.map((col) => (
          <div key={col.id} className="flex items-center">
            <button
              onClick={() => setActiveCollection(col.id)}
              className={`px-3 py-1.5 text-xs rounded-l-lg transition-colors ${
                activeCollection === col.id
                  ? "bg-zinc-800 text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
              }`}
            >
              {col.name}
            </button>
            <button
              onClick={() => handleDeleteCollection(col.id)}
              className={`px-1.5 py-1.5 text-xs rounded-r-lg transition-colors ${
                activeCollection === col.id
                  ? "bg-zinc-700 text-zinc-300 hover:text-white"
                  : "bg-zinc-100 text-zinc-300 hover:text-red-400"
              }`}
              title="削除"
            >
              ×
            </button>
          </div>
        ))}
        {showNewForm ? (
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.nativeEvent.isComposing) handleAddCollection();
                if (e.key === "Escape") setShowNewForm(false);
              }}
              placeholder="コレクション名"
              className="text-xs border border-zinc-200 rounded-lg px-2 py-1.5 outline-none focus:ring-2 focus:ring-indigo-400/40 w-32"
              autoFocus
            />
            <button
              onClick={handleAddCollection}
              className="text-xs text-indigo-500 hover:text-indigo-700 px-1"
            >
              追加
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowNewForm(true)}
            className="px-3 py-1.5 text-xs rounded-lg border border-dashed border-zinc-300 text-zinc-400 hover:text-zinc-600 hover:border-zinc-400 transition-colors"
          >
            + 新規
          </button>
        )}
      </div>

      {/* Collection entries */}
      {activeCollection ? (
        <div>
          {entries.length === 0 && (
            <p className="text-xs text-zinc-400 text-center py-6">
              まだ項目がありません
            </p>
          )}
          {entries.map((entry) => (
            <BulletEntryItem
              key={entry.id}
              entry={entry}
              onUpdateState={(id, state: TaskState) => {
                updateEntry(id, { state });
                refreshEntries();
              }}
              onUpdateContent={(id, content) => {
                updateEntry(id, { content });
                refreshEntries();
              }}
              onTogglePriority={(id) => {
                const e = entries.find((x) => x.id === id);
                if (e) {
                  updateEntry(id, { priority: !e.priority });
                  refreshEntries();
                }
              }}
              onDelete={(id) => {
                deleteEntry(id);
                refreshEntries();
              }}
            />
          ))}

          <div className="mt-3 flex items-center gap-2 border-t border-zinc-100 pt-3">
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
              onClick={handleAddEntry}
              disabled={!newContent.trim()}
              className="text-xs text-zinc-400 hover:text-zinc-600 disabled:opacity-30 px-2 py-1"
            >
              追加
            </button>
          </div>
        </div>
      ) : (
        <p className="text-xs text-zinc-400 text-center py-6">
          コレクションを選択するか、新規作成してください
        </p>
      )}
    </div>
  );
}
