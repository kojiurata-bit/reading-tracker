"use client";

import { Book, ReadingStatus } from "@/types/book";
import StarRating from "./StarRating";

const statusConfig: Record<
  ReadingStatus,
  { label: string; color: string }
> = {
  tsundoku: { label: "積読", color: "bg-amber-50 text-amber-600 border border-amber-200/60" },
  reading: { label: "読書中", color: "bg-blue-50 text-blue-600 border border-blue-200/60" },
  finished: { label: "読了", color: "bg-emerald-50 text-emerald-600 border border-emerald-200/60" },
  wishlist: { label: "買いたい", color: "bg-violet-50 text-violet-600 border border-violet-200/60" },
};

interface BookCardProps {
  book: Book;
  onClick: () => void;
}

export default function BookCard({ book, onClick }: BookCardProps) {
  const status = statusConfig[book.status];

  const formatDate = (d: string) => {
    if (!d) return "";
    if (/^\d{4}-\d{2}-\d{2}$/.test(d)) {
      const [y, m, day] = d.split("-");
      return `${Number(y)}年${Number(m)}月${Number(day)}日`;
    }
    if (/^\d{4}-\d{2}$/.test(d)) {
      const [y, m] = d.split("-");
      return `${Number(y)}年${Number(m)}月`;
    }
    if (/^\d{4}$/.test(d)) return `${Number(d)}年`;
    return d;
  };

  const authorWithDate = [
    book.author,
    book.publishedDate ? `(${formatDate(book.publishedDate)})` : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white rounded-xl border border-zinc-100 p-4 hover:shadow-md hover:border-zinc-200 transition-all cursor-pointer group"
    >
      <div className="flex gap-4">
        {book.thumbnail ? (
          <img
            src={book.thumbnail}
            alt=""
            className="w-14 h-20 object-cover rounded-lg shadow-sm shrink-0 group-hover:shadow-md transition-shadow"
          />
        ) : (
          <div className="w-14 h-20 bg-zinc-50 rounded-lg shrink-0 flex items-center justify-center text-zinc-300 text-2xl border border-zinc-100">
            📕
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-zinc-900 truncate">
              {book.title}
            </h3>
            <span
              className={`shrink-0 px-2 py-0.5 rounded-full text-[11px] font-medium ${status.color}`}
            >
              {status.label}
            </span>
          </div>
          {authorWithDate && (
            <p className="text-sm text-zinc-400 mt-0.5">{authorWithDate}</p>
          )}
          {(book.genre || book.pageCount > 0) && (
            <p className="text-xs text-zinc-300 mt-1">
              {book.genre}
              {book.genre && book.pageCount > 0 && " · "}
              {book.pageCount > 0 && `${book.pageCount}p`}
            </p>
          )}
          <div className="mt-1.5 flex items-center justify-between">
            <StarRating rating={book.rating} readonly size="sm" />
            <div className="flex items-center gap-2">
              {book.purchaseUrl && book.status === "wishlist" && (
                <a
                  href={book.purchaseUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-xs text-indigo-500 hover:text-indigo-700 hover:underline font-medium"
                >
                  購入 &rarr;
                </a>
              )}
              {book.finishedDate && (
                <span className="text-xs text-zinc-300">
                  {new Date(book.finishedDate).toLocaleDateString("ja-JP")}
                </span>
              )}
            </div>
          </div>
          {book.description && (
            <p className="text-xs text-zinc-400/70 mt-1.5 line-clamp-1 italic">
              {book.description}
            </p>
          )}
        </div>
      </div>
      {book.memo && (
        <p className="text-sm text-zinc-400 mt-2 pl-18 line-clamp-2">
          {book.memo}
        </p>
      )}
    </button>
  );
}
