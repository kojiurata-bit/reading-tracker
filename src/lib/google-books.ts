export interface GoogleBookResult {
  id: string;
  title: string;
  authors: string[];
  categories: string[];
  publishedDate: string;
  pageCount: number;
  thumbnail: string | null;
  description: string | null;
}

interface VolumeInfo {
  title?: string;
  authors?: string[];
  categories?: string[];
  publishedDate?: string;
  pageCount?: number;
  description?: string;
  imageLinks?: { smallThumbnail?: string; thumbnail?: string };
}

interface VolumeItem {
  id: string;
  volumeInfo: VolumeInfo;
}

function mapVolumeToResult(item: VolumeItem): GoogleBookResult {
  const info = item.volumeInfo;
  return {
    id: item.id,
    title: info.title ?? "",
    authors: info.authors ?? [],
    categories: info.categories ?? [],
    publishedDate: info.publishedDate ?? "",
    pageCount: info.pageCount ?? 0,
    thumbnail:
      info.imageLinks?.thumbnail ??
      info.imageLinks?.smallThumbnail ??
      null,
    description: info.description ?? null,
  };
}

/**
 * Maps English Google Books categories to Japanese Amazon-style genre labels.
 * Returns the best matching Japanese genre or the original category if no match.
 */
const CATEGORY_MAP: Record<string, string> = {
  // Literature & Fiction
  "Fiction": "文学・評論",
  "Literary Fiction": "文学・評論",
  "Literature": "文学・評論",
  "Literary Criticism": "文学・評論",
  "Poetry": "文学・評論",
  "Drama": "文学・評論",
  // Philosophy & Thought
  "Philosophy": "人文・思想",
  "Psychology": "人文・思想",
  "Religion": "人文・思想",
  "Self-Help": "人文・思想",
  "Body, Mind & Spirit": "人文・思想",
  // Social Science & Politics
  "Social Science": "社会・政治・法律",
  "Political Science": "社会・政治・法律",
  "Law": "社会・政治・法律",
  "True Crime": "社会・政治・法律",
  // Nonfiction
  "Nonfiction": "ノンフィクション",
  "Biography & Autobiography": "ノンフィクション",
  // History & Geography
  "History": "歴史・地理",
  "Travel": "旅行ガイド・マップ",
  // Business & Economics
  "Business & Economics": "ビジネス・経済",
  "Business": "ビジネス・経済",
  "Economics": "ビジネス・経済",
  // Science & Technology
  "Science": "科学・テクノロジー",
  "Technology & Engineering": "科学・テクノロジー",
  "Mathematics": "科学・テクノロジー",
  "Nature": "科学・テクノロジー",
  // Medical
  "Medical": "医学・薬学・看護学・歯科学",
  "Health & Fitness": "暮らし・健康・子育て",
  // Computers & IT
  "Computers": "コンピュータ・IT",
  // Art & Design
  "Art": "アート・建築・デザイン",
  "Architecture": "アート・建築・デザイン",
  "Design": "アート・建築・デザイン",
  "Photography": "アート・建築・デザイン",
  "Music": "楽譜・スコア・音楽書",
  "Performing Arts": "エンターテイメント",
  // Hobbies
  "Crafts & Hobbies": "趣味・実用",
  "Cooking": "趣味・実用",
  "Gardening": "趣味・実用",
  "Games & Activities": "趣味・実用",
  "Humor": "趣味・実用",
  "Pets": "趣味・実用",
  // Sports
  "Sports & Recreation": "スポーツ・アウトドア",
  // Education
  "Education": "教育・学参・受験",
  "Study Aids": "資格・検定・就職",
  "Language Arts & Disciplines": "語学・辞事典・年鑑",
  "Foreign Language Study": "英語学習",
  // Juvenile
  "Juvenile Fiction": "絵本・児童書",
  "Juvenile Nonfiction": "絵本・児童書",
  // Comics
  "Comics & Graphic Novels": "コミック",
  // Young Adult
  "Young Adult Fiction": "ライトノベル",
  "Young Adult Nonfiction": "ライトノベル",
  // Family
  "Family & Relationships": "暮らし・健康・子育て",
  "House & Home": "暮らし・健康・子育て",
  // Reference
  "Reference": "語学・辞事典・年鑑",
  // Antiques
  "Antiques & Collectibles": "古書・希少本",
};

export function mapCategoryToGenre(categories: string[]): string {
  for (const cat of categories) {
    // Try exact match first
    if (CATEGORY_MAP[cat]) return CATEGORY_MAP[cat];
    // Try partial match
    for (const [key, value] of Object.entries(CATEGORY_MAP)) {
      if (cat.toLowerCase().includes(key.toLowerCase())) return value;
    }
  }
  return categories[0] ?? "";
}

const API_KEY = process.env.NEXT_PUBLIC_GOOGLE_BOOKS_API_KEY ?? "";
const keyParam = API_KEY ? `&key=${API_KEY}` : "";

/** Thrown when the Google Books API rate limit is exceeded. */
export class RateLimitError extends Error {
  constructor() {
    super("Google Books API rate limit exceeded");
    this.name = "RateLimitError";
  }
}

export async function searchBooks(
  query: string
): Promise<GoogleBookResult[]> {
  if (!query.trim()) return [];

  const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(query)}&maxResults=8&langRestrict=ja&printType=books${keyParam}`;

  const res = await fetch(url);
  if (res.status === 429) throw new RateLimitError();
  if (!res.ok) return [];

  const data = await res.json();
  if (!data.items) return [];

  return data.items.map((item: VolumeItem) => mapVolumeToResult(item));
}

/**
 * Searches for a book by ISBN.
 * Fetches from OpenBD and Google Books in parallel, then merges:
 *   - OpenBD: reliable JP book data (pageCount, publishedDate, description, genre)
 *   - Google Books: better thumbnail images
 */
export async function searchByIsbn(
  isbn: string
): Promise<GoogleBookResult | null> {
  // Fetch from both sources in parallel
  const openBDPromise = import("./openbd")
    .then(({ searchByIsbnOpenBD }) => searchByIsbnOpenBD(isbn))
    .catch(() => null);

  const googlePromise = fetch(
    `https://www.googleapis.com/books/v1/volumes?q=isbn:${isbn}&maxResults=1&printType=books${keyParam}`
  )
    .then(async (res) => {
      if (res.status === 429) throw new RateLimitError();
      if (!res.ok) return null;
      const data = await res.json();
      if (!data.items || data.items.length === 0) return null;
      return mapVolumeToResult(data.items[0]);
    })
    .catch((err) => {
      if (err instanceof RateLimitError) return "RATE_LIMITED" as const;
      return null;
    });

  const [openBDResult, googleRaw] = await Promise.all([
    openBDPromise,
    googlePromise,
  ]);

  const googleResult = googleRaw === "RATE_LIMITED" ? null : googleRaw;

  if (openBDResult) {
    // Merge: prefer OpenBD data, supplement missing fields from Google Books
    if (googleResult) {
      if (!openBDResult.thumbnail && googleResult.thumbnail) {
        openBDResult.thumbnail = googleResult.thumbnail;
      }
      if (!openBDResult.description && googleResult.description) {
        openBDResult.description = googleResult.description;
      }
      if (!openBDResult.pageCount && googleResult.pageCount) {
        openBDResult.pageCount = googleResult.pageCount;
      }
      if (
        (!openBDResult.publishedDate || openBDResult.publishedDate.length <= 4) &&
        googleResult.publishedDate
      ) {
        openBDResult.publishedDate = googleResult.publishedDate;
      }
      if (openBDResult.categories.length === 0 && googleResult.categories.length > 0) {
        openBDResult.categories = googleResult.categories;
      }
    }
    return openBDResult;
  }

  // OpenBD had nothing — if Google was rate-limited, throw
  if (googleRaw === "RATE_LIMITED") throw new RateLimitError();

  return googleResult;
}
