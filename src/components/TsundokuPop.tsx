"use client";

import { useState, useMemo } from "react";
import { Book } from "@/types/book";

interface TsundokuPopProps {
  books: Book[];
  onStartReading: (id: string) => void;
}

/**
 * Seeded random based on today's date — gives a consistent "daily pick"
 * that changes each day.
 */
function dailySeed(): number {
  const d = new Date();
  const str = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export default function TsundokuPop({
  books,
  onStartReading,
}: TsundokuPopProps) {
  const tsundokuBooks = useMemo(
    () => books.filter((b) => b.status === "tsundoku"),
    [books]
  );

  // Pick candidates: prefer books with descriptions, but include all
  const candidates = useMemo(() => {
    const withDesc = tsundokuBooks.filter((b) => b.description.trim());
    return withDesc.length > 0 ? withDesc : tsundokuBooks;
  }, [tsundokuBooks]);

  const [shuffleCount, setShuffleCount] = useState(0);

  const pickedBook = useMemo(() => {
    if (candidates.length === 0) return null;
    const idx = (dailySeed() + shuffleCount) % candidates.length;
    return candidates[idx];
  }, [candidates, shuffleCount]);

  const [isSpinning, setIsSpinning] = useState(false);

  if (!pickedBook) return null;

  const handleShuffle = () => {
    setIsSpinning(true);
    setTimeout(() => {
      setShuffleCount((c) => c + 1);
      setIsSpinning(false);
    }, 400);
  };

  const daysAgo = Math.floor(
    (Date.now() - new Date(pickedBook.createdAt).getTime()) /
      (1000 * 60 * 60 * 24)
  );

  const dustLabel =
    daysAgo < 7
      ? "✨ まだ新鮮"
      : daysAgo < 30
        ? "📖 そろそろ読み時"
        : daysAgo < 90
          ? "🍂 少し積もってきた"
          : "🕸️ だいぶ眠ってます";

  return (
    <div className="relative bg-gradient-to-br from-indigo-50 via-white to-violet-50 rounded-2xl border border-indigo-100/60 p-5 shadow-sm overflow-hidden">
      {/* Decorative bookshelf pop feel */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-100/30 rounded-full -translate-y-8 translate-x-8" />
      <div className="absolute bottom-0 left-0 w-16 h-16 bg-violet-100/30 rounded-full translate-y-6 -translate-x-6" />

      <div className="relative">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-base">📚</span>
            <h2 className="text-sm font-bold text-zinc-800">
              今日の積読ピックアップ
            </h2>
          </div>
          <button
            onClick={handleShuffle}
            disabled={isSpinning || candidates.length <= 1}
            className="text-xs text-indigo-400 hover:text-indigo-600 transition-colors disabled:opacity-30 flex items-center gap-1"
          >
            <span
              className={`inline-block transition-transform ${isSpinning ? "animate-spin" : ""}`}
            >
              🎲
            </span>
            シャッフル
          </button>
        </div>

        {/* Book Card */}
        <div
          className={`transition-opacity duration-300 ${isSpinning ? "opacity-0" : "opacity-100"}`}
        >
          <div className="flex gap-4">
            {pickedBook.thumbnail ? (
              <img
                src={pickedBook.thumbnail}
                alt=""
                className="w-16 h-[92px] object-cover rounded-xl shadow-md shrink-0"
              />
            ) : (
              <div className="w-16 h-[92px] bg-white rounded-xl shrink-0 flex items-center justify-center text-zinc-300 text-2xl border border-zinc-100 shadow-sm">
                📕
              </div>
            )}

            <div className="min-w-0 flex-1">
              <h3 className="font-bold text-zinc-900 text-base leading-snug line-clamp-2">
                {pickedBook.title}
              </h3>
              <p className="text-xs text-zinc-400 mt-0.5">
                {pickedBook.author}
                {pickedBook.publishedDate &&
                  ` (${pickedBook.publishedDate})`}
              </p>

              {/* Dust meter */}
              <p className="text-[11px] text-zinc-400 mt-1.5">
                {dustLabel}
                <span className="text-zinc-300 ml-1">
                  — 登録から{daysAgo}日
                </span>
              </p>
            </div>
          </div>

          {/* Description — the bookstore "pop" */}
          {pickedBook.description && (
            <div className="mt-3 bg-white/70 rounded-xl px-4 py-3 border border-indigo-100/40">
              <p className="text-xs font-medium text-indigo-400 mb-1">
                📝 こんな本です
              </p>
              <p className="text-sm text-zinc-600 leading-relaxed line-clamp-3">
                {pickedBook.description}
              </p>
            </div>
          )}

          {/* Action */}
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={() => onStartReading(pickedBook.id)}
              className="px-4 py-1.5 bg-indigo-500 text-white text-xs font-medium rounded-lg hover:bg-indigo-600 transition-colors shadow-sm"
            >
              読み始める
            </button>
            {pickedBook.purchaseUrl && (
              <a
                href={pickedBook.purchaseUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-indigo-400 hover:text-indigo-600 hover:underline"
              >
                Amazon →
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
