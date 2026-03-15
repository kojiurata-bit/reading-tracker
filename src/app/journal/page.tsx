"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import DailyLog from "@/components/bullet/DailyLog";
import MonthlyLog from "@/components/bullet/MonthlyLog";
import CollectionView from "@/components/bullet/CollectionView";

type View = "daily" | "monthly" | "collections";

function getToday(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export default function JournalPage() {
  const [view, setView] = useState<View>("daily");
  const [selectedDate, setSelectedDate] = useState(getToday());

  const { year, month } = useMemo(() => {
    const [y, m] = selectedDate.split("-").map(Number);
    return { year: y, month: m };
  }, [selectedDate]);

  const navigateMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    const newYear = d.getFullYear();
    const newMonth = d.getMonth() + 1;
    const newDay = Math.min(
      parseInt(selectedDate.split("-")[2]),
      new Date(newYear, newMonth, 0).getDate()
    );
    setSelectedDate(
      `${newYear}-${String(newMonth).padStart(2, "0")}-${String(newDay).padStart(2, "0")}`
    );
  };

  const goToToday = () => setSelectedDate(getToday());

  const navigateDay = (delta: number) => {
    const d = new Date(selectedDate + "T00:00:00");
    d.setDate(d.getDate() + delta);
    setSelectedDate(
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
    );
  };

  return (
    <div className="min-h-screen bg-[#fafafa]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-zinc-100">
        <div className="max-w-2xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-zinc-400 hover:text-zinc-600 transition-colors text-sm"
            >
              ← 読書
            </Link>
            <h1 className="text-lg font-semibold text-zinc-900 tracking-tight">
              バレットジャーナル
            </h1>
          </div>
          <button
            onClick={goToToday}
            className="text-xs text-indigo-500 hover:text-indigo-700 transition-colors font-medium"
          >
            今日
          </button>
        </div>

        {/* View switcher */}
        <div className="max-w-2xl mx-auto px-4 pb-3 flex items-center gap-1">
          {(
            [
              { key: "daily", label: "デイリー" },
              { key: "monthly", label: "マンスリー" },
              { key: "collections", label: "コレクション" },
            ] as const
          ).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setView(key)}
              className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                view === key
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-500 hover:bg-zinc-100"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-5">
        {/* Date navigation (for daily/monthly) */}
        {view !== "collections" && (
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() =>
                view === "daily" ? navigateDay(-1) : navigateMonth(-1)
              }
              className="p-2 text-zinc-400 hover:text-zinc-600 transition-colors"
            >
              ‹
            </button>
            <span className="text-sm font-medium text-zinc-600">
              {view === "daily"
                ? selectedDate
                : `${year}年${month}月`}
            </span>
            <button
              onClick={() =>
                view === "daily" ? navigateDay(1) : navigateMonth(1)
              }
              className="p-2 text-zinc-400 hover:text-zinc-600 transition-colors"
            >
              ›
            </button>
          </div>
        )}

        {/* Content area */}
        <div className="bg-white rounded-xl border border-zinc-100 p-4 shadow-sm">
          {view === "daily" && <DailyLog date={selectedDate} />}
          {view === "monthly" && (
            <MonthlyLog
              year={year}
              month={month}
              selectedDate={selectedDate}
              onSelectDate={(date) => {
                setSelectedDate(date);
                setView("daily");
              }}
            />
          )}
          {view === "collections" && <CollectionView />}
        </div>

        {/* Key legend */}
        <div className="mt-6 p-4 bg-white rounded-xl border border-zinc-100 shadow-sm">
          <h3 className="text-xs font-medium text-zinc-400 mb-2">記号の意味</h3>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-zinc-500">
            <div className="flex items-center gap-2">
              <span className="font-bold text-zinc-600">•</span> タスク
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-zinc-600">×</span> 完了
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-indigo-500">○</span> イベント
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-zinc-600">&gt;</span> 移動済み
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-emerald-500">–</span> メモ
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-zinc-600">&lt;</span> 予定
            </div>
            <div className="flex items-center gap-2">
              <span className="text-red-400">*</span> 優先
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
