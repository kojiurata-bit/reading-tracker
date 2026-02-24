import { Book, GENRE_OPTIONS } from "@/types/book";
import { mapCategoryToGenre } from "@/lib/google-books";

const STORAGE_KEY = "reading-tracker-books";

export function getBooks(): Book[] {
  if (typeof window === "undefined") return [];
  const data = localStorage.getItem(STORAGE_KEY);
  if (!data) return [];
  const books: Book[] = JSON.parse(data);
  let migrated = false;
  for (const book of books) {
    if ((book.status as string) === "unread") {
      book.status = "tsundoku";
      migrated = true;
    }
    // Migrate publishedYear → publishedDate
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const raw = book as any;
    if (raw.publishedYear !== undefined && raw.publishedDate === undefined) {
      book.publishedDate = raw.publishedYear ?? "";
      delete raw.publishedYear;
      migrated = true;
    }
    if (book.publishedDate === undefined) {
      book.publishedDate = "";
      migrated = true;
    }
    if (book.purchaseUrl === undefined) {
      book.purchaseUrl = "";
      migrated = true;
    }
    if (book.thumbnail === undefined) {
      book.thumbnail = null;
      migrated = true;
    }
    if (book.description === undefined) {
      (book as Book).description = "";
      migrated = true;
    }
    if (book.pageCount === undefined) {
      book.pageCount = 0;
      migrated = true;
    }
    // Migrate English genres to Japanese Amazon-style labels
    const validGenres: Set<string> = new Set(GENRE_OPTIONS);
    if (book.genre && !validGenres.has(book.genre)) {
      const mapped = mapCategoryToGenre([book.genre]);
      if (validGenres.has(mapped)) {
        book.genre = mapped;
        migrated = true;
      }
    }
  }
  if (migrated) saveBooks(books);
  return books;
}

export function saveBooks(books: Book[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(books));
}

export function addBook(
  book: Omit<Book, "id" | "createdAt" | "updatedAt">
): Book {
  const books = getBooks();
  const now = new Date().toISOString();
  const newBook: Book = {
    ...book,
    id: crypto.randomUUID(),
    createdAt: now,
    updatedAt: now,
  };
  books.unshift(newBook);
  saveBooks(books);
  return newBook;
}

export function updateBook(id: string, updates: Partial<Book>): Book | null {
  const books = getBooks();
  const index = books.findIndex((b) => b.id === id);
  if (index === -1) return null;
  books[index] = {
    ...books[index],
    ...updates,
    updatedAt: new Date().toISOString(),
  };
  saveBooks(books);
  return books[index];
}

export function deleteBook(id: string): boolean {
  const books = getBooks();
  const filtered = books.filter((b) => b.id !== id);
  if (filtered.length === books.length) return false;
  saveBooks(filtered);
  return true;
}
