"use client";

import { ReadingStatus } from "@/types/book";

type TabValue = ReadingStatus | "all";

interface StatusTabsProps {
  current: TabValue;
  onChange: (tab: TabValue) => void;
  counts: Record<TabValue, number>;
}

const tabs: { value: TabValue; label: string }[] = [
  { value: "all", label: "すべて" },
  { value: "tsundoku", label: "積読" },
  { value: "reading", label: "読書中" },
  { value: "finished", label: "読了" },
  { value: "wishlist", label: "買いたい" },
];

export default function StatusTabs({
  current,
  onChange,
  counts,
}: StatusTabsProps) {
  return (
    <div className="flex gap-1 bg-zinc-100/60 rounded-lg p-1 overflow-x-auto">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onChange(tab.value)}
          className={`shrink-0 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            current === tab.value
              ? "bg-white text-zinc-900 shadow-sm"
              : "text-zinc-400 hover:text-zinc-600"
          }`}
        >
          {tab.label}
          <span className="ml-1 text-xs opacity-50">
            {counts[tab.value]}
          </span>
        </button>
      ))}
    </div>
  );
}
