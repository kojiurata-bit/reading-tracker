"use client";

import { useState, useMemo } from "react";

interface ReadingJournalProps {
  checkedDates: string[];
  onToggle: (date: string) => void;
}

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function formatDate(y: number, m: number, d: number) {
  return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

export default function ReadingJournal({
  checkedDates,
  onToggle,
}: ReadingJournalProps) {
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());

  const todayStr = formatDate(
    today.getFullYear(),
    today.getMonth(),
    today.getDate()
  );

  const checkedSet = useMemo(() => new Set(checkedDates), [checkedDates]);

  const daysInMonth = getDaysInMonth(viewYear, viewMonth);

  const monthChecked = checkedDates.filter((d) =>
    d.startsWith(`${viewYear}-${String(viewMonth + 1).padStart(2, "0")}`)
  ).length;

  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewYear((y) => y - 1);
      setViewMonth(11);
    } else {
      setViewMonth((m) => m - 1);
    }
  };

  const nextMonth = () => {
    if (viewMonth === 11) {
      setViewYear((y) => y + 1);
      setViewMonth(0);
    } else {
      setViewMonth((m) => m + 1);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-zinc-100 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <button
            onClick={prevMonth}
            className="text-zinc-400 hover:text-zinc-600 transition-colors text-sm px-1"
          >
            &lsaquo;
          </button>
          <h2 className="text-sm font-semibold text-zinc-700 tabular-nums">
            {viewYear}年{viewMonth + 1}月
          </h2>
          <button
            onClick={nextMonth}
            className="text-zinc-400 hover:text-zinc-600 transition-colors text-sm px-1"
          >
            &rsaquo;
          </button>
        </div>
        <span className="text-xs text-zinc-400">
          {monthChecked} / {daysInMonth}日
        </span>
      </div>

      {/* Horizontal day row */}
      <div className="flex gap-[3px] overflow-x-auto pb-1">
        {Array.from({ length: daysInMonth }).map((_, i) => {
          const day = i + 1;
          const dateStr = formatDate(viewYear, viewMonth, day);
          const isChecked = checkedSet.has(dateStr);
          const isToday = dateStr === todayStr;
          const isFuture = dateStr > todayStr;

          return (
            <button
              key={day}
              disabled={isFuture}
              onClick={() => onToggle(dateStr)}
              className={`
                shrink-0 w-[calc((100%-90px)/31)] min-w-[22px] aspect-square rounded-md text-[10px] font-medium
                flex items-center justify-center transition-all
                ${isFuture ? "text-zinc-200 cursor-default" : "cursor-pointer"}
                ${isToday && !isChecked ? "ring-1 ring-indigo-400 text-indigo-500" : ""}
                ${isChecked
                  ? "bg-indigo-500 text-white hover:bg-indigo-600"
                  : isFuture
                    ? "bg-zinc-50"
                    : "bg-zinc-50 text-zinc-400 hover:bg-zinc-100"
                }
              `}
            >
              {day}
            </button>
          );
        })}
      </div>

      <p className="text-[10px] text-zinc-300 mt-2 text-center">
        読書した日をタップして記録
      </p>
    </div>
  );
}
