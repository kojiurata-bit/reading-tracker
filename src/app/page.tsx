"use client";

import { useState, useEffect, useCallback } from "react";
import { Book, ReadingStatus } from "@/types/book";
import { getBooks, addBook, updateBook, deleteBook } from "@/lib/storage";
import {
  searchBooks,
  searchByIsbn,
  mapCategoryToGenre,
  RateLimitError,
} from "@/lib/google-books";
import { extractAsin, isLikelyIsbn } from "@/lib/amazon";
import {
  getYearlyGoal,
  setYearlyGoal,
  getJournalDates,
  toggleJournalDate,
} from "@/lib/goals";
import Dashboard from "@/components/Dashboard";
import ReadingJournal from "@/components/ReadingJournal";
import StatusTabs from "@/components/StatusTabs";
import BookCard from "@/components/BookCard";
import BookForm from "@/components/BookForm";
import AmazonUrlInput from "@/components/AmazonUrlInput";
import TsundokuPop from "@/components/TsundokuPop";
import NearbyBookstoreMap from "@/components/NearbyBookstoreMap";

type TabValue = ReadingStatus | "all";
type SortKey =
  | "reg_desc"
  | "reg_asc"
  | "pub_desc"
  | "pub_asc"
  | "rating_desc"
  | "rating_asc"
  | "pages_asc"
  | "pages_desc";

function sortBooks(list: Book[], key: SortKey): Book[] {
  const sorted = [...list];
  const byCreated = (a: Book, b: Book) =>
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();

  switch (key) {
    case "reg_desc":
      return sorted.sort(byCreated);
    case "reg_asc":
      return sorted.sort((a, b) => -byCreated(a, b));
    case "pub_desc":
      return sorted.sort((a, b) => {
        const da = a.publishedDate || "0";
        const db = b.publishedDate || "0";
        return db.localeCompare(da) || byCreated(a, b);
      });
    case "pub_asc":
      return sorted.sort((a, b) => {
        const da = a.publishedDate || "9999";
        const db = b.publishedDate || "9999";
        return da.localeCompare(db) || byCreated(a, b);
      });
    case "rating_desc":
      return sorted.sort(
        (a, b) => b.rating - a.rating || byCreated(a, b)
      );
    case "rating_asc":
      return sorted.sort(
        (a, b) => a.rating - b.rating || byCreated(a, b)
      );
    case "pages_asc":
      return sorted.sort((a, b) => {
        const pa = a.pageCount || 99999;
        const pb = b.pageCount || 99999;
        return pa - pb || byCreated(a, b);
      });
    case "pages_desc":
      return sorted.sort((a, b) => {
        const pa = a.pageCount || 0;
        const pb = b.pageCount || 0;
        return pb - pa || byCreated(a, b);
      });
    default:
      return sorted;
  }
}

export default function Home() {
  const [books, setBooks] = useState<Book[]>([]);
  const [activeTab, setActiveTab] = useState<TabValue>("all");
  const [sortKey, setSortKey] = useState<SortKey>("reg_desc");
  const [showForm, setShowForm] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | undefined>();
  const [prefillData, setPrefillData] = useState<Partial<Book> | undefined>();
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null);
  const [yearlyGoal, setGoal] = useState(0);
  const [journalDates, setJournalDates] = useState<string[]>([]);

  useEffect(() => {
    setBooks(getBooks());
    setGoal(getYearlyGoal());
    setJournalDates(getJournalDates());
  }, []);

  // ---------------------------------------------------------------------------
  // Auto-backfill routine: automatically supplements missing book data.
  //   - Runs once per day (24h cooldown) on every page load.
  //   - Per-book "no-data" tracking: books where APIs returned nothing are
  //     skipped for 7 days to avoid wasting quota.
  //   - Phase 1 (ISBN via OpenBD + Google Books): no rate limit, runs for all
  //     eligible books every cycle.
  //   - Phase 2 (Google Books title search): rate-limited, max 30 books/day.
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const BACKFILL_KEY = "reading-tracker-backfill-ts";
    const NODATA_KEY = "reading-tracker-backfill-nodata";
    const ONE_DAY = 24 * 60 * 60 * 1000;
    const SEVEN_DAYS = 7 * ONE_DAY;
    const MAX_GOOGLE_PER_SESSION = 30;

    /** Returns set of book IDs that were attempted recently with no result. */
    const getNoDataSet = (): Record<string, number> => {
      try {
        return JSON.parse(localStorage.getItem(NODATA_KEY) || "{}");
      } catch {
        return {};
      }
    };

    /** Record a book as "no data available from APIs". */
    const markNoData = (noData: Record<string, number>, bookId: string) => {
      noData[bookId] = Date.now();
    };

    /** Check if a book should be skipped (attempted recently, no data). */
    const shouldSkip = (noData: Record<string, number>, bookId: string) => {
      const ts = noData[bookId];
      return ts != null && Date.now() - ts < SEVEN_DAYS;
    };

    /** Returns true if the book is missing important fields. */
    const isMissingData = (b: Book) =>
      !b.pageCount ||
      !b.publishedDate ||
      (b.publishedDate && b.publishedDate.length <= 4) ||
      !b.thumbnail ||
      !b.description;

    const backfillBookData = async () => {
      // --- Cooldown: once per day ---
      const lastRun = localStorage.getItem(BACKFILL_KEY);
      if (lastRun && Date.now() - Number(lastRun) < ONE_DAY) return;

      const current = getBooks();
      const noData = getNoDataSet();
      let updated = false;

      // Purge expired entries (older than 7 days)
      for (const id of Object.keys(noData)) {
        if (Date.now() - noData[id] >= SEVEN_DAYS) delete noData[id];
      }

      // --- Phase 1: ISBN lookup (OpenBD + Google Books parallel merge) ---
      const needsIsbnLookup = current.filter((b) => {
        if (shouldSkip(noData, b.id)) return false;
        if (!b.purchaseUrl) return false;
        const asin = extractAsin(b.purchaseUrl);
        if (!asin || !isLikelyIsbn(asin)) return false;
        return isMissingData(b);
      });

      for (const book of needsIsbnLookup) {
        try {
          const asin = extractAsin(book.purchaseUrl)!;
          const result = await searchByIsbn(asin);
          if (!result) {
            markNoData(noData, book.id);
            continue;
          }

          const updates: Partial<Book> = {};
          if (!book.pageCount && result.pageCount)
            updates.pageCount = result.pageCount;
          if (
            (!book.publishedDate || book.publishedDate.length <= 4) &&
            result.publishedDate
          )
            updates.publishedDate = result.publishedDate;
          if (!book.thumbnail && result.thumbnail)
            updates.thumbnail = result.thumbnail;
          if (!book.description && result.description)
            updates.description = result.description;
          if (!book.genre && result.categories.length > 0)
            updates.genre = mapCategoryToGenre(result.categories);

          if (Object.keys(updates).length > 0) {
            updateBook(book.id, updates);
            updated = true;
          } else {
            // API returned a result but nothing new to fill — mark to skip
            markNoData(noData, book.id);
          }
        } catch (err) {
          if (err instanceof RateLimitError) break;
        }
      }

      // --- Phase 2: Google Books title search (rate-limited) ---
      const afterPhase1 = updated ? getBooks() : current;
      const needsGoogle = afterPhase1
        .filter(
          (b) =>
            b.title && isMissingData(b) && !shouldSkip(noData, b.id)
        )
        .slice(0, MAX_GOOGLE_PER_SESSION);

      for (const book of needsGoogle) {
        try {
          const query = [book.title, book.author].filter(Boolean).join(" ");
          const results = await searchBooks(query);
          if (results.length > 0) {
            const r = results[0];
            const updates: Partial<Book> = {};
            if (!book.description && r.description)
              updates.description = r.description;
            if (!book.genre && r.categories.length > 0)
              updates.genre = mapCategoryToGenre(r.categories);
            if (!book.pageCount && r.pageCount)
              updates.pageCount = r.pageCount;
            if (
              (!book.publishedDate || book.publishedDate.length <= 4) &&
              r.publishedDate
            )
              updates.publishedDate = r.publishedDate;
            if (!book.thumbnail && r.thumbnail)
              updates.thumbnail = r.thumbnail;

            if (Object.keys(updates).length > 0) {
              updateBook(book.id, updates);
              updated = true;
            } else {
              markNoData(noData, book.id);
            }
          } else {
            markNoData(noData, book.id);
          }
          await new Promise((r) => setTimeout(r, 500));
        } catch (err) {
          if (err instanceof RateLimitError) break;
        }
      }

      // Persist state
      localStorage.setItem(NODATA_KEY, JSON.stringify(noData));
      localStorage.setItem(BACKFILL_KEY, String(Date.now()));
      if (updated) {
        setBooks(getBooks());
      }
    };
    backfillBookData();
  }, []);

  const refreshBooks = useCallback(() => {
    setBooks(getBooks());
  }, []);

  const filteredBooks = sortBooks(
    books.filter((b) => {
      if (activeTab !== "all" && b.status !== activeTab) return false;
      if (selectedGenre !== null) {
        const bookGenre = b.genre || "その他";
        if (bookGenre !== selectedGenre) return false;
      }
      return true;
    }),
    sortKey
  );

  const counts = {
    all: books.length,
    tsundoku: books.filter((b) => b.status === "tsundoku").length,
    reading: books.filter((b) => b.status === "reading").length,
    finished: books.filter((b) => b.status === "finished").length,
    wishlist: books.filter((b) => b.status === "wishlist").length,
  };

  const handleAdd = (data: Parameters<typeof addBook>[0]) => {
    addBook(data);
    refreshBooks();
    setShowForm(false);
    setPrefillData(undefined);
  };

  const handleAmazonEditRegister = (data: {
    title: string;
    author: string;
    genre: string;
    publishedDate: string;
    pageCount: number;
    description: string;
    thumbnail: string | null;
    purchaseUrl: string;
  }) => {
    setPrefillData({
      title: data.title,
      author: data.author,
      genre: data.genre,
      publishedDate: data.publishedDate,
      pageCount: data.pageCount,
      description: data.description,
      status: "tsundoku",
      thumbnail: data.thumbnail,
      purchaseUrl: data.purchaseUrl,
    });
    setShowForm(true);
  };

  const handleUpdate = (data: Parameters<typeof addBook>[0]) => {
    if (!editingBook) return;
    updateBook(editingBook.id, data);
    refreshBooks();
    setEditingBook(undefined);
  };

  const handleDelete = () => {
    if (!editingBook) return;
    deleteBook(editingBook.id);
    refreshBooks();
    setEditingBook(undefined);
  };

  const handleGoalChange = (goal: number) => {
    setYearlyGoal(goal);
    setGoal(goal);
  };

  const handleJournalToggle = (date: string) => {
    const updated = toggleJournalDate(date);
    setJournalDates(updated);
  };

  const handleStartReading = (id: string) => {
    updateBook(id, { status: "reading" });
    refreshBooks();
  };

  return (
    <div className="min-h-screen bg-[#fafafa]">
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-zinc-100">
        <div className="max-w-2xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-zinc-900 tracking-tight">
            読書トラッカーβ
          </h1>
          <button
            onClick={() => setShowForm(true)}
            className="bg-zinc-900 text-white px-3.5 py-1.5 rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors"
          >
            + 追加
          </button>
        </div>
        <div className="max-w-2xl mx-auto px-4 pb-3">
          <AmazonUrlInput
            onRegister={handleAdd}
            onEditRegister={handleAmazonEditRegister}
          />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-5 space-y-4">
        <Dashboard
          books={books}
          yearlyGoal={yearlyGoal}
          onGoalChange={handleGoalChange}
          selectedGenre={selectedGenre}
          onGenreSelect={setSelectedGenre}
        />

        <TsundokuPop
          books={books}
          onStartReading={handleStartReading}
        />

        <ReadingJournal
          checkedDates={journalDates}
          onToggle={handleJournalToggle}
        />

        <div className="flex items-center gap-2">
          <div className="flex-1 min-w-0">
            <StatusTabs
              current={activeTab}
              onChange={setActiveTab}
              counts={counts}
            />
          </div>
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            className="shrink-0 rounded-lg border border-zinc-200 bg-white px-2 py-2 text-xs text-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-400/40 cursor-pointer"
          >
            <option value="reg_desc">登録 新→古</option>
            <option value="reg_asc">登録 古→新</option>
            <option value="pub_desc">出版 新→古</option>
            <option value="pub_asc">出版 古→新</option>
            <option value="rating_desc">評価 高→低</option>
            <option value="rating_asc">評価 低→高</option>
            <option value="pages_asc">ページ数 少→多</option>
            <option value="pages_desc">ページ数 多→少</option>
          </select>
        </div>

        <div className="space-y-2">
          {filteredBooks.length === 0 ? (
            <div className="text-center py-16 text-zinc-400">
              <p className="text-sm">
                {selectedGenre
                  ? `「${selectedGenre}」の本はありません`
                  : activeTab === "all"
                    ? "まだ本が登録されていません"
                    : "このステータスの本はありません"}
              </p>
              {activeTab === "all" && !selectedGenre && (
                <button
                  onClick={() => setShowForm(true)}
                  className="mt-3 text-indigo-500 text-sm hover:underline"
                >
                  最初の1冊を追加する
                </button>
              )}
            </div>
          ) : (
            filteredBooks.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                onClick={() => setEditingBook(book)}
              />
            ))
          )}
        </div>

        <NearbyBookstoreMap />
      </main>

      {showForm && (
        <BookForm
          initialData={prefillData}
          onSubmit={handleAdd}
          onCancel={() => {
            setShowForm(false);
            setPrefillData(undefined);
          }}
        />
      )}

      {editingBook && (
        <BookForm
          book={editingBook}
          onSubmit={handleUpdate}
          onCancel={() => setEditingBook(undefined)}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}
