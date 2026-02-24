"use client";

import { useState } from "react";
import { GoogleBookResult, mapCategoryToGenre } from "@/lib/google-books";
import { searchByIsbn, searchBooks } from "@/lib/google-books";
import {
  isAmazonUrl,
  isShortUrl,
  extractAsin,
  isLikelyIsbn,
  extractTitleFromUrl,
  cleanAmazonUrl,
} from "@/lib/amazon";

type Phase = "idle" | "loading" | "preview" | "not-found" | "error";

interface AmazonUrlInputProps {
  onRegister: (data: {
    title: string;
    author: string;
    genre: string;
    publishedDate: string;
    pageCount: number;
    status: "tsundoku";
    rating: number;
    memo: string;
    description: string;
    thumbnail: string | null;
    purchaseUrl: string;
    finishedDate: null;
  }) => void;
  onEditRegister: (data: {
    title: string;
    author: string;
    genre: string;
    publishedDate: string;
    pageCount: number;
    description: string;
    thumbnail: string | null;
    purchaseUrl: string;
  }) => void;
}

export default function AmazonUrlInput({
  onRegister,
  onEditRegister,
}: AmazonUrlInputProps) {
  const [inputValue, setInputValue] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [bookData, setBookData] = useState<GoogleBookResult | null>(null);
  const [amazonUrl, setAmazonUrl] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const reset = () => {
    setInputValue("");
    setPhase("idle");
    setBookData(null);
    setAmazonUrl("");
    setErrorMsg("");
  };

  const handleUrlSubmit = async (input: string) => {
    const trimmed = input.trim();
    if (!trimmed) return;

    if (!isAmazonUrl(trimmed)) {
      setErrorMsg("AmazonのURLを入力してください");
      setPhase("error");
      return;
    }

    if (isShortUrl(trimmed)) {
      setErrorMsg("短縮URLは非対応です。商品ページのURLを貼り付けてください");
      setPhase("error");
      return;
    }

    setPhase("loading");
    const cleanedUrl = cleanAmazonUrl(trimmed);
    setAmazonUrl(cleanedUrl);

    const asin = extractAsin(trimmed);

    // Strategy 1: ISBN lookup
    if (asin && isLikelyIsbn(asin)) {
      try {
        const result = await searchByIsbn(asin);
        if (result) {
          setBookData(result);
          setPhase("preview");
          return;
        }
      } catch {
        // Fall through to title extraction
      }
    }

    // Strategy 2: Title extraction from URL path
    const titleFromUrl = extractTitleFromUrl(trimmed);
    if (titleFromUrl) {
      try {
        const results = await searchBooks(titleFromUrl);
        if (results.length > 0) {
          setBookData(results[0]);
          setPhase("preview");
          return;
        }
      } catch {
        // Fall through to not-found
      }
    }

    // Strategy 3: Nothing found
    setPhase("not-found");
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pasted = e.clipboardData.getData("text");
    if (isAmazonUrl(pasted.trim())) {
      e.preventDefault();
      setInputValue(pasted.trim());
      handleUrlSubmit(pasted.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleUrlSubmit(inputValue);
    }
  };

  const handleQuickRegister = () => {
    if (!bookData) return;
    onRegister({
      title: bookData.title,
      author: bookData.authors.join(", "),
      genre: mapCategoryToGenre(bookData.categories),
      publishedDate: bookData.publishedDate,
      pageCount: bookData.pageCount,
      status: "tsundoku",
      rating: 0,
      memo: "",
      description: bookData.description ?? "",
      thumbnail: bookData.thumbnail,
      purchaseUrl: amazonUrl,
      finishedDate: null,
    });
    reset();
  };

  const handleEditRegister = () => {
    onEditRegister({
      title: bookData?.title ?? "",
      author: bookData?.authors.join(", ") ?? "",
      genre: bookData ? mapCategoryToGenre(bookData.categories) : "",
      publishedDate: bookData?.publishedDate ?? "",
      pageCount: bookData?.pageCount ?? 0,
      description: bookData?.description ?? "",
      thumbnail: bookData?.thumbnail ?? null,
      purchaseUrl: amazonUrl,
    });
    reset();
  };

  return (
    <div className="space-y-2">
      {/* URL Input */}
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onPaste={handlePaste}
          onKeyDown={handleKeyDown}
          placeholder="AmazonのURLを貼り付けて自動登録..."
          className="w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-9 pr-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-indigo-400/40 focus:border-transparent placeholder:text-zinc-300"
        />
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
          />
        </svg>
        {phase === "loading" && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-zinc-200 border-t-indigo-500 rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Preview Card */}
      {phase === "preview" && bookData && (
        <div className="bg-white rounded-xl border border-zinc-100 p-4 shadow-sm animate-in fade-in">
          <div className="flex gap-3">
            {bookData.thumbnail ? (
              <img
                src={bookData.thumbnail}
                alt=""
                className="w-12 h-[68px] object-cover rounded-lg shadow-sm shrink-0"
              />
            ) : (
              <div className="w-12 h-[68px] bg-zinc-50 rounded-lg shrink-0 flex items-center justify-center text-zinc-300 text-lg border border-zinc-100">
                📕
              </div>
            )}
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-semibold text-zinc-900 truncate">
                {bookData.title}
              </h3>
              <p className="text-xs text-zinc-400 truncate">
                {bookData.authors.join(", ") || "著者不明"}
              </p>
              {bookData.publishedDate && (
                <p className="text-xs text-zinc-300 mt-0.5">
                  {bookData.publishedDate}
                </p>
              )}
              <div className="flex items-center gap-2 mt-2">
                <button
                  onClick={handleQuickRegister}
                  className="px-3 py-1 bg-zinc-900 text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition-colors"
                >
                  積読に登録
                </button>
                <button
                  onClick={handleEditRegister}
                  className="px-3 py-1 bg-zinc-100 text-zinc-500 text-xs font-medium rounded-lg hover:bg-zinc-200 transition-colors"
                >
                  編集して登録
                </button>
                <button
                  onClick={reset}
                  className="text-xs text-zinc-300 hover:text-zinc-500 transition-colors ml-auto"
                >
                  キャンセル
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Not Found */}
      {phase === "not-found" && (
        <div className="bg-zinc-50 rounded-xl border border-zinc-100 p-3 text-center">
          <p className="text-sm text-zinc-400 mb-2">
            書籍情報が見つかりませんでした
          </p>
          <div className="flex items-center justify-center gap-2">
            <button
              onClick={handleEditRegister}
              className="px-3 py-1 bg-zinc-900 text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition-colors"
            >
              手動で入力
            </button>
            <button
              onClick={reset}
              className="text-xs text-zinc-300 hover:text-zinc-500 transition-colors"
            >
              キャンセル
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {phase === "error" && (
        <div className="flex items-center justify-between bg-red-50 rounded-lg border border-red-100 px-3 py-2">
          <p className="text-xs text-red-400">{errorMsg}</p>
          <button
            onClick={reset}
            className="text-xs text-red-300 hover:text-red-500 transition-colors ml-2 shrink-0"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
