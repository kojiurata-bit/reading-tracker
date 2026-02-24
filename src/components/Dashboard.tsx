"use client";

import { useState } from "react";
import { Book } from "@/types/book";

interface DashboardProps {
  books: Book[];
  yearlyGoal: number;
  onGoalChange: (goal: number) => void;
  selectedGenre: string | null;
  onGenreSelect: (genre: string | null) => void;
}

function GenrePieChart({
  books,
  selectedGenre,
  onGenreSelect,
}: {
  books: Book[];
  selectedGenre: string | null;
  onGenreSelect: (genre: string | null) => void;
}) {
  const genreCounts: Record<string, number> = {};
  for (const book of books) {
    const genre = book.genre || "その他";
    genreCounts[genre] = (genreCounts[genre] || 0) + 1;
  }

  const entries = Object.entries(genreCounts).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  if (total === 0) return null;

  const colors = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
    "#10b981", "#06b6d4", "#f97316", "#64748b",
  ];

  let cumulative = 0;
  const slices = entries.map(([, count], i) => {
    const start = cumulative;
    const angle = (count / total) * 360;
    cumulative += angle;
    const startRad = ((start - 90) * Math.PI) / 180;
    const endRad = ((start + angle - 90) * Math.PI) / 180;
    const large = angle > 180 ? 1 : 0;
    const r = 38;
    const cx = 50, cy = 50;
    const x1 = cx + r * Math.cos(startRad);
    const y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad);
    const y2 = cy + r * Math.sin(endRad);

    const genre = entries[i][0];
    const isSelected = selectedGenre === genre;
    const isOther = selectedGenre !== null && !isSelected;
    const fillColor = colors[i % colors.length];
    const opacity = isOther ? 0.25 : 1;

    if (entries.length === 1) {
      return (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          fill={fillColor}
          opacity={opacity}
          className="cursor-pointer transition-opacity duration-200"
          onClick={() => onGenreSelect(isSelected ? null : genre)}
        />
      );
    }
    return (
      <path
        key={i}
        d={`M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${large} 1 ${x2},${y2} Z`}
        fill={fillColor}
        opacity={opacity}
        className="cursor-pointer transition-opacity duration-200"
        onClick={() => onGenreSelect(isSelected ? null : genre)}
      />
    );
  });

  return (
    <div className="flex items-center gap-4">
      <svg viewBox="0 0 100 100" className="w-20 h-20 shrink-0">
        <circle cx="50" cy="50" r="16" fill="white" />
        {slices}
        <circle cx="50" cy="50" r="16" fill="white" />
      </svg>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5">
        {entries.map(([genre, count], i) => {
          const isSelected = selectedGenre === genre;
          const isOther = selectedGenre !== null && !isSelected;
          return (
            <button
              key={genre}
              type="button"
              onClick={() => onGenreSelect(isSelected ? null : genre)}
              className={`flex items-center gap-1.5 rounded-md px-1 -mx-1 transition-opacity duration-200 ${
                isOther ? "opacity-30" : "opacity-100"
              } ${isSelected ? "ring-1 ring-zinc-300 bg-zinc-50" : "hover:bg-zinc-50"}`}
            >
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: colors[i % colors.length] }}
              />
              <span className="text-xs text-zinc-500">
                {genre} <span className="text-zinc-400">{count}</span>
              </span>
            </button>
          );
        })}
        {selectedGenre && (
          <button
            type="button"
            onClick={() => onGenreSelect(null)}
            className="text-[10px] text-zinc-400 hover:text-zinc-600 transition-colors ml-1"
          >
            クリア
          </button>
        )}
      </div>
    </div>
  );
}

export default function Dashboard({
  books,
  yearlyGoal,
  onGoalChange,
  selectedGenre,
  onGenreSelect,
}: DashboardProps) {
  const [editing, setEditing] = useState(false);
  const [goalInput, setGoalInput] = useState(String(yearlyGoal || ""));

  const currentYear = new Date().getFullYear();
  const finishedThisYear = books.filter(
    (b) =>
      b.status === "finished" &&
      b.finishedDate &&
      b.finishedDate.startsWith(String(currentYear))
  ).length;
  const readingCount = books.filter((b) => b.status === "reading").length;
  const tsundokuCount = books.filter((b) => b.status === "tsundoku").length;

  const goalProgress =
    yearlyGoal > 0 ? Math.min(finishedThisYear / yearlyGoal, 1) : 0;

  const handleGoalSave = () => {
    const val = parseInt(goalInput, 10);
    onGoalChange(isNaN(val) || val < 0 ? 0 : val);
    setEditing(false);
  };

  return (
    <div className="bg-white rounded-xl border border-zinc-100 p-4 space-y-4 shadow-sm">
      {/* Stats row */}
      <div className="flex items-center gap-3">
        {[
          { label: "読了", value: finishedThisYear, color: "bg-emerald-500" },
          { label: "読書中", value: readingCount, color: "bg-blue-500" },
          { label: "積読", value: tsundokuCount, color: "bg-amber-500" },
        ].map((s) => (
          <div key={s.label} className="flex items-center gap-2 bg-zinc-50 rounded-lg px-3 py-2 flex-1">
            <span className={`w-2 h-2 rounded-full ${s.color}`} />
            <div>
              <p className="text-lg font-semibold text-zinc-900 leading-tight">{s.value}</p>
              <p className="text-[10px] text-zinc-400 uppercase tracking-wider">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Goal */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-xs font-medium text-zinc-500">{currentYear}年の目標</p>
          {editing ? (
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                min={0}
                value={goalInput}
                onChange={(e) => setGoalInput(e.target.value)}
                className="w-14 rounded-md border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-xs text-zinc-900 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                autoFocus
                onKeyDown={(e) => e.key === "Enter" && handleGoalSave()}
              />
              <span className="text-xs text-zinc-400">冊</span>
              <button
                onClick={handleGoalSave}
                className="text-xs text-indigo-500 hover:text-indigo-700 font-medium"
              >
                保存
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setGoalInput(String(yearlyGoal || "")); setEditing(true); }}
              className="text-xs text-zinc-400 hover:text-zinc-600 transition-colors"
            >
              {yearlyGoal > 0 ? `${yearlyGoal}冊 — 変更` : "目標を設定"}
            </button>
          )}
        </div>
        {yearlyGoal > 0 && (
          <>
            <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                style={{ width: `${goalProgress * 100}%` }}
              />
            </div>
            <p className="text-[10px] text-zinc-400 mt-1">
              {finishedThisYear} / {yearlyGoal}
              {goalProgress >= 1 ? " 達成!" : ` — 残り${yearlyGoal - finishedThisYear}冊`}
            </p>
          </>
        )}
      </div>

      {/* Genre chart */}
      <GenrePieChart books={books} selectedGenre={selectedGenre} onGenreSelect={onGenreSelect} />
    </div>
  );
}
