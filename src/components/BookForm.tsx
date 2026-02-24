"use client";

import { useState } from "react";
import { Book, ReadingStatus, GENRE_OPTIONS } from "@/types/book";
import { GoogleBookResult, mapCategoryToGenre } from "@/lib/google-books";
import StarRating from "./StarRating";
import BookSearch from "./BookSearch";

interface BookFormProps {
  book?: Book;
  initialData?: Partial<Book>;
  onSubmit: (data: {
    title: string;
    author: string;
    genre: string;
    publishedDate: string;
    pageCount: number;
    status: ReadingStatus;
    rating: number;
    memo: string;
    description: string;
    thumbnail: string | null;
    purchaseUrl: string;
    finishedDate: string | null;
  }) => void;
  onCancel: () => void;
  onDelete?: () => void;
}

const statusOptions: { value: ReadingStatus; label: string }[] = [
  { value: "tsundoku", label: "積読" },
  { value: "reading", label: "読書中" },
  { value: "finished", label: "読了" },
  { value: "wishlist", label: "買いたい" },
];

const inputClass =
  "w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-indigo-400/40 focus:border-transparent placeholder:text-zinc-300";

export default function BookForm({
  book,
  initialData,
  onSubmit,
  onCancel,
  onDelete,
}: BookFormProps) {
  const [title, setTitle] = useState(book?.title ?? initialData?.title ?? "");
  const [author, setAuthor] = useState(book?.author ?? initialData?.author ?? "");
  const [genre, setGenre] = useState(book?.genre ?? initialData?.genre ?? "");
  const [publishedDate, setPublishedDate] = useState(
    book?.publishedDate ?? initialData?.publishedDate ?? ""
  );
  const [status, setStatus] = useState<ReadingStatus>(
    book?.status ?? initialData?.status ?? "tsundoku"
  );
  const [pageCount, setPageCount] = useState(book?.pageCount ?? initialData?.pageCount ?? 0);
  const [rating, setRating] = useState(book?.rating ?? initialData?.rating ?? 0);
  const [memo, setMemo] = useState(book?.memo ?? initialData?.memo ?? "");
  const [thumbnail, setThumbnail] = useState<string | null>(
    book?.thumbnail ?? initialData?.thumbnail ?? null
  );
  const [purchaseUrl, setPurchaseUrl] = useState(
    book?.purchaseUrl ?? initialData?.purchaseUrl ?? ""
  );
  const [description, setDescription] = useState(
    book?.description ?? initialData?.description ?? ""
  );
  const [finishedDate, setFinishedDate] = useState(
    book?.finishedDate ?? initialData?.finishedDate ?? ""
  );

  const handleSearchSelect = (result: GoogleBookResult) => {
    setTitle(result.title);
    setAuthor(result.authors.join(", "));
    setThumbnail(result.thumbnail);
    setPublishedDate(result.publishedDate);
    setPageCount(result.pageCount);
    setDescription(result.description ?? "");
    if (result.categories.length > 0) {
      setGenre(mapCategoryToGenre(result.categories));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const finalPurchaseUrl =
      purchaseUrl.trim() ||
      (status === "wishlist" && title.trim()
        ? `https://www.amazon.co.jp/s?k=${encodeURIComponent(title.trim() + " " + author.trim())}`
        : "");
    onSubmit({
      title: title.trim(),
      author: author.trim(),
      genre: genre.trim(),
      publishedDate: publishedDate.trim(),
      pageCount,
      status,
      rating,
      memo: memo.trim(),
      description,
      thumbnail,
      purchaseUrl: finalPurchaseUrl,
      finishedDate: finishedDate || null,
    });
  };

  const handleStatusChange = (newStatus: ReadingStatus) => {
    setStatus(newStatus);
    if (newStatus === "finished" && !finishedDate) {
      setFinishedDate(new Date().toISOString().split("T")[0]);
    }
    if (newStatus !== "finished") {
      setFinishedDate("");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          <h2 className="text-lg font-bold text-zinc-900 mb-5">
            {book ? "本を編集" : "本を追加"}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!book && (
              <div>
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  書籍を検索
                </label>
                <BookSearch onSelect={handleSearchSelect} />
                <p className="text-xs text-zinc-300 mt-1">
                  検索して選択するか、下のフォームに直接入力
                </p>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                タイトル <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className={inputClass}
                placeholder="本のタイトル"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                著者
              </label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                className={inputClass}
                placeholder="著者名"
              />
            </div>
            <div className="flex gap-3">
              <div className="flex-1">
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  出版日
                </label>
                <input
                  type="date"
                  value={publishedDate}
                  onChange={(e) => setPublishedDate(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div className="w-24">
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  ページ数
                </label>
                <input
                  type="number"
                  value={pageCount || ""}
                  onChange={(e) => setPageCount(Number(e.target.value) || 0)}
                  className={inputClass}
                  placeholder="0"
                  min={0}
                  inputMode="numeric"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                ジャンル
              </label>
              <select
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                className={inputClass}
              >
                <option value="">選択してください</option>
                {GENRE_OPTIONS.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                ステータス
              </label>
              <div className="flex flex-wrap gap-2">
                {statusOptions.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => handleStatusChange(s.value)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      status === s.value
                        ? "bg-zinc-900 text-white"
                        : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
            {status === "finished" && (
              <div>
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  読了日
                </label>
                <input
                  type="date"
                  value={finishedDate}
                  onChange={(e) => setFinishedDate(e.target.value)}
                  className={inputClass}
                />
              </div>
            )}
            {(status === "wishlist" || status === "tsundoku") && (
              <div>
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  購入リンク
                </label>
                <input
                  type="url"
                  value={purchaseUrl}
                  onChange={(e) => setPurchaseUrl(e.target.value)}
                  className={inputClass}
                  placeholder={status === "wishlist" ? "空欄ならAmazon検索リンクを自動生成" : "Amazon等のURL"}
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                評価
              </label>
              <StarRating rating={rating} onChange={setRating} />
            </div>
            {description && (
              <div>
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  紹介文
                </label>
                <div className="rounded-lg border border-zinc-100 bg-zinc-50/50 px-3 py-2.5 text-sm text-zinc-500 leading-relaxed max-h-32 overflow-y-auto">
                  {description}
                </div>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                メモ
              </label>
              <textarea
                value={memo}
                onChange={(e) => setMemo(e.target.value)}
                rows={3}
                className={`${inputClass} resize-none`}
                placeholder="感想やメモを記入..."
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={!title.trim()}
                className="flex-1 bg-zinc-900 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {book ? "保存" : "追加"}
              </button>
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 bg-zinc-100 text-zinc-500 rounded-lg py-2.5 text-sm font-medium hover:bg-zinc-200 transition-colors"
              >
                キャンセル
              </button>
            </div>
            {book && onDelete && (
              <button
                type="button"
                onClick={onDelete}
                className="w-full text-red-400 text-sm hover:text-red-500 transition-colors pt-1"
              >
                この本を削除
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
