"use client";

import { useMemo } from "react";
import { getDatesWithEntries, getEntriesByMonth } from "@/lib/bullet-storage";

interface Props {
  year: number;
  month: number; // 1-12
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

const WEEKDAY_LABELS = ["日", "月", "火", "水", "木", "金", "土"];

export default function MonthlyLog({
  year,
  month,
  selectedDate,
  onSelectDate,
}: Props) {
  const yearMonth = `${year}-${String(month).padStart(2, "0")}`;

  const datesWithEntries = useMemo(() => getDatesWithEntries(yearMonth), [yearMonth]);

  const monthEntries = useMemo(() => getEntriesByMonth(yearMonth), [yearMonth]);
  const openTaskCount = monthEntries.filter(
    (e) => e.type === "task" && e.state === "open"
  ).length;
  const doneTaskCount = monthEntries.filter(
    (e) => e.type === "task" && e.state === "done"
  ).length;

  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();

  const today = new Date();
  const todayStr =
    today.getFullYear() === year && today.getMonth() + 1 === month
      ? `${yearMonth}-${String(today.getDate()).padStart(2, "0")}`
      : null;

  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  return (
    <div>
      {/* Month stats */}
      <div className="flex items-center gap-3 mb-3 text-xs text-zinc-400">
        <span>{monthEntries.length} 件</span>
        {openTaskCount > 0 && (
          <span className="text-amber-500">{openTaskCount} 未完了</span>
        )}
        {doneTaskCount > 0 && (
          <span className="text-emerald-500">{doneTaskCount} 完了</span>
        )}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-0.5">
        {WEEKDAY_LABELS.map((label) => (
          <div
            key={label}
            className="text-center text-[10px] text-zinc-400 font-medium py-1"
          >
            {label}
          </div>
        ))}
        {cells.map((day, i) => {
          if (day === null) {
            return <div key={`empty-${i}`} />;
          }
          const dateStr = `${yearMonth}-${String(day).padStart(2, "0")}`;
          const isSelected = dateStr === selectedDate;
          const isToday = dateStr === todayStr;
          const hasEntries = datesWithEntries.has(dateStr);

          return (
            <button
              key={dateStr}
              onClick={() => onSelectDate(dateStr)}
              className={`
                relative h-9 rounded-lg text-xs font-medium transition-all
                ${isSelected
                  ? "bg-zinc-800 text-white shadow-sm"
                  : isToday
                    ? "bg-indigo-50 text-indigo-600 ring-1 ring-indigo-200"
                    : "text-zinc-600 hover:bg-zinc-100"
                }
              `}
            >
              {day}
              {hasEntries && !isSelected && (
                <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-indigo-400" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
