"use client";

import { useState, useEffect, useRef } from "react";
import { searchBooks, GoogleBookResult } from "@/lib/google-books";

interface BookSearchProps {
  onSelect: (book: GoogleBookResult) => void;
}

export default function BookSearch({ onSelect }: BookSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GoogleBookResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }

    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      setLoading(true);
      const books = await searchBooks(query);
      setResults(books);
      setOpen(books.length > 0);
      setLoading(false);
    }, 400);

    return () => clearTimeout(timerRef.current);
  }, [query]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleSelect = (book: GoogleBookResult) => {
    onSelect(book);
    setQuery("");
    setResults([]);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder="書籍を検索して追加..."
          className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 pl-9 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-indigo-400/40 focus:border-transparent placeholder:text-zinc-300"
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
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-zinc-200 border-t-indigo-500 rounded-full animate-spin" />
          </div>
        )}
      </div>

      {open && (
        <div className="absolute z-20 mt-1 w-full bg-white border border-zinc-200 rounded-lg shadow-lg max-h-72 overflow-y-auto">
          {results.map((book) => (
            <button
              key={book.id}
              type="button"
              onClick={() => handleSelect(book)}
              className="w-full text-left px-3 py-2.5 hover:bg-zinc-50 flex gap-3 border-b border-zinc-100 last:border-0"
            >
              {book.thumbnail ? (
                <img
                  src={book.thumbnail}
                  alt=""
                  className="w-10 h-14 object-cover rounded shrink-0"
                />
              ) : (
                <div className="w-10 h-14 bg-zinc-50 rounded shrink-0 flex items-center justify-center text-zinc-300 text-xs">
                  📕
                </div>
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium text-zinc-900 truncate">
                  {book.title}
                </p>
                <p className="text-xs text-zinc-400 truncate">
                  {book.authors.join(", ") || "著者不明"}
                </p>
                {book.categories.length > 0 && (
                  <p className="text-xs text-zinc-300 truncate">
                    {book.categories[0]}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
