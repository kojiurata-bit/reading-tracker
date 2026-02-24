"use client";

import { useState, useRef } from "react";

const BOOKS_KEY = "reading-tracker-books";
const GOAL_KEY = "reading-tracker-goal";
const JOURNAL_KEY = "reading-tracker-journal";

interface ExportData {
  books: unknown[];
  goal: number;
  journal: string[];
  exportedAt: string;
}

export default function DataManager() {
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showMessage = (text: string, type: "success" | "error") => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 4000);
  };

  // --- Export ---
  const handleExport = () => {
    try {
      const books = JSON.parse(localStorage.getItem(BOOKS_KEY) || "[]");
      const goal = parseInt(localStorage.getItem(GOAL_KEY) || "0", 10);
      const journal = JSON.parse(
        localStorage.getItem(JOURNAL_KEY) || "[]"
      );

      const data: ExportData = {
        books,
        goal,
        journal,
        exportedAt: new Date().toISOString(),
      };

      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const today = new Date().toISOString().slice(0, 10);
      a.href = url;
      a.download = `reading-tracker-backup-${today}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showMessage(
        `${books.length}冊のデータをエクスポートしました`,
        "success"
      );
    } catch {
      showMessage("エクスポートに失敗しました", "error");
    }
  };

  // --- Import ---
  const handleImport = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const raw = event.target?.result as string;
        const data = JSON.parse(raw) as ExportData;

        // Validation
        if (!data.books || !Array.isArray(data.books)) {
          showMessage(
            "無効なファイルです：書籍データが見つかりません",
            "error"
          );
          return;
        }

        const existingBooks = JSON.parse(
          localStorage.getItem(BOOKS_KEY) || "[]"
        );
        const confirmMsg =
          existingBooks.length > 0
            ? `現在${existingBooks.length}冊のデータがあります。\nインポートすると${data.books.length}冊のデータで上書きされます。\nよろしいですか？`
            : `${data.books.length}冊のデータをインポートします。よろしいですか？`;

        if (!window.confirm(confirmMsg)) return;

        // Write to localStorage
        localStorage.setItem(BOOKS_KEY, JSON.stringify(data.books));
        if (data.goal != null) {
          localStorage.setItem(GOAL_KEY, String(data.goal));
        }
        if (data.journal && Array.isArray(data.journal)) {
          localStorage.setItem(JOURNAL_KEY, JSON.stringify(data.journal));
        }

        showMessage(
          `${data.books.length}冊のデータをインポートしました。リロードします...`,
          "success"
        );

        // Reload to reflect imported data
        setTimeout(() => window.location.reload(), 1500);
      } catch {
        showMessage("ファイルの読み込みに失敗しました", "error");
      }
    };
    reader.readAsText(file);

    // Reset so the same file can be selected again
    e.target.value = "";
  };

  return (
    <section className="mt-8 border-t border-zinc-200 pt-6 pb-8">
      <h2 className="text-sm font-semibold text-zinc-500 mb-3">
        データ管理
      </h2>
      <div className="flex gap-3">
        <button
          onClick={handleExport}
          className="px-4 py-2 text-sm rounded-lg border border-zinc-300 text-zinc-700 hover:bg-zinc-50 transition-colors cursor-pointer"
        >
          エクスポート
        </button>
        <button
          onClick={handleImport}
          className="px-4 py-2 text-sm rounded-lg border border-zinc-300 text-zinc-700 hover:bg-zinc-50 transition-colors cursor-pointer"
        >
          インポート
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
      {message && (
        <p
          className={`mt-2 text-sm ${
            message.type === "success" ? "text-green-600" : "text-red-600"
          }`}
        >
          {message.text}
        </p>
      )}
      <p className="mt-2 text-xs text-zinc-400">
        エクスポートでバックアップ用JSONファイルをダウンロード。インポートで別のブラウザやデバイスにデータを移行できます。
      </p>
    </section>
  );
}
