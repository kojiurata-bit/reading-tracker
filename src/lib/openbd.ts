/**
 * OpenBD API client for Japanese book ISBN lookups.
 * https://openbd.jp/
 *
 * Advantages over Google Books:
 * - No rate limit / no API key required
 * - Better coverage for Japanese books (ISBN-based)
 * - Provides page count, description, cover image, C-code categories
 */

import { GoogleBookResult } from "./google-books";

// ---------- Types ----------

interface OpenBDSummary {
  isbn: string;
  title: string;
  author: string;
  publisher: string;
  pubdate: string;
  cover: string;
  volume: string;
  series: string;
}

interface OpenBDExtent {
  ExtentType: string;
  ExtentValue: string;
  ExtentUnit: string;
}

interface OpenBDTextContent {
  TextType: string;
  Text: string;
}

interface OpenBDSubject {
  SubjectSchemeIdentifier: string;
  SubjectCode: string;
  SubjectHeadingText?: string;
}

interface OpenBDResponse {
  summary: OpenBDSummary;
  onix: {
    DescriptiveDetail?: {
      Extent?: OpenBDExtent[];
      Subject?: OpenBDSubject[];
    };
    CollateralDetail?: {
      TextContent?: OpenBDTextContent[];
    };
  };
  hanmoto?: {
    genrecodetrc?: number;
  };
}

// ---------- ISBN-10 → ISBN-13 conversion ----------

function isbn10to13(isbn10: string): string {
  const base = "978" + isbn10.slice(0, 9);
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(base[i]) * (i % 2 === 0 ? 1 : 3);
  }
  const check = (10 - (sum % 10)) % 10;
  return base + check;
}

// ---------- C-code → Genre mapping ----------

/**
 * Maps the 2-digit content portion (last 2 digits) of a Japanese C-code
 * to our GENRE_OPTIONS labels.
 *
 * C-code format: Cxxxx (audience + form + content)
 * We extract the last 2 digits for content classification.
 */
const CCODE_GENRE_MAP: Record<string, string> = {
  // 1x: Philosophy / Humanities
  "10": "人文・思想", "11": "人文・思想", "12": "人文・思想",
  "14": "人文・思想", "15": "人文・思想", "16": "人文・思想",
  // 2x: History / Geography
  "20": "歴史・地理", "21": "歴史・地理", "22": "歴史・地理",
  "23": "歴史・地理", "26": "旅行ガイド・マップ",
  // 3x: Social science / Politics / Business / Education
  "30": "社会・政治・法律", "31": "社会・政治・法律",
  "32": "社会・政治・法律", "36": "社会・政治・法律",
  "33": "ビジネス・経済", "34": "ビジネス・経済",
  "37": "教育・学参・受験",
  // 4x: Natural science / Medicine
  "40": "科学・テクノロジー", "41": "科学・テクノロジー",
  "42": "科学・テクノロジー", "43": "科学・テクノロジー",
  "44": "科学・テクノロジー", "45": "科学・テクノロジー",
  "47": "医学・薬学・看護学・歯科学", "49": "医学・薬学・看護学・歯科学",
  // 5x: Technology / IT / Living
  "50": "科学・テクノロジー", "51": "科学・テクノロジー",
  "52": "科学・テクノロジー", "53": "科学・テクノロジー",
  "54": "科学・テクノロジー",
  "55": "コンピュータ・IT",
  "58": "暮らし・健康・子育て", "59": "暮らし・健康・子育て",
  // 6x: Industry / Business
  "60": "ビジネス・経済", "61": "ビジネス・経済",
  "63": "ビジネス・経済",
  // 7x: Art / Music / Entertainment / Sports / Comics
  "70": "アート・建築・デザイン", "71": "アート・建築・デザイン",
  "72": "アート・建築・デザイン", "73": "アート・建築・デザイン",
  "74": "アート・建築・デザイン", "75": "アート・建築・デザイン",
  "76": "楽譜・スコア・音楽書",
  "77": "エンターテイメント",
  "78": "スポーツ・アウトドア",
  "79": "コミック",
  // 8x: Language
  "80": "語学・辞事典・年鑑", "81": "語学・辞事典・年鑑",
  "82": "英語学習", "83": "英語学習", "84": "英語学習",
  "85": "英語学習", "86": "英語学習", "87": "英語学習",
  "88": "英語学習", "89": "英語学習",
  // 9x: Literature
  "90": "文学・評論", "91": "文学・評論", "92": "文学・評論",
  "93": "文学・評論", "95": "文学・評論", "97": "文学・評論",
  "98": "絵本・児童書",
};

/**
 * Extracts a genre from C-code subjects.
 * Returns a mapped genre string or empty string if no match.
 */
function genreFromCCode(subjects: OpenBDSubject[]): string {
  for (const sub of subjects) {
    // SubjectSchemeIdentifier "78" = C-code
    if (sub.SubjectSchemeIdentifier === "78" && sub.SubjectCode) {
      const code = sub.SubjectCode;
      // C-code format: 4 digits (audience + form + content)
      // Content = last 2 digits
      if (code.length >= 4) {
        const content = code.slice(-2);
        if (CCODE_GENRE_MAP[content]) return CCODE_GENRE_MAP[content];
      }
    }
  }
  return "";
}

// ---------- Public API ----------

/**
 * Looks up a book by ISBN using the OpenBD API.
 * Accepts both ISBN-10 and ISBN-13.
 * Returns a GoogleBookResult-compatible object or null if not found.
 */
export async function searchByIsbnOpenBD(
  isbn: string
): Promise<GoogleBookResult | null> {
  // Normalize to ISBN-13
  const cleanIsbn = isbn.replace(/[-\s]/g, "");
  const isbn13 = cleanIsbn.length === 10 ? isbn10to13(cleanIsbn) : cleanIsbn;

  const res = await fetch(`https://api.openbd.jp/v1/get?isbn=${isbn13}`);
  if (!res.ok) return null;

  const data: (OpenBDResponse | null)[] = await res.json();
  if (!data || !data[0]) return null;

  const book = data[0];
  const summary = book.summary;
  if (!summary.title) return null;

  // Page count from ONIX Extent (ExtentType "11" = pages, ExtentUnit "03" = pages)
  const extents = book.onix?.DescriptiveDetail?.Extent ?? [];
  const pageExtent = extents.find((e) => e.ExtentType === "11");
  const pageCount = pageExtent ? parseInt(pageExtent.ExtentValue) || 0 : 0;

  // Description from ONIX TextContent (prefer "03" = long, then "02" = short)
  const texts = book.onix?.CollateralDetail?.TextContent ?? [];
  const descText =
    texts.find((t) => t.TextType === "03") ??
    texts.find((t) => t.TextType === "02");
  const description = descText?.Text?.replace(/<[^>]*>/g, "") ?? null;

  // Published date: "YYYYMMDD" → "YYYY-MM-DD"
  let publishedDate = "";
  if (summary.pubdate) {
    const pd = summary.pubdate;
    if (pd.length === 8) {
      publishedDate = `${pd.slice(0, 4)}-${pd.slice(4, 6)}-${pd.slice(6, 8)}`;
    } else if (pd.length === 6) {
      publishedDate = `${pd.slice(0, 4)}-${pd.slice(4, 6)}`;
    } else {
      publishedDate = pd;
    }
  }

  // Genre from C-code subjects
  const subjects = book.onix?.DescriptiveDetail?.Subject ?? [];
  const genre = genreFromCCode(subjects);
  const categories = genre ? [genre] : [];

  return {
    id: `openbd-${isbn13}`,
    title: summary.title,
    authors: summary.author ? [summary.author] : [],
    categories,
    publishedDate,
    pageCount,
    thumbnail: summary.cover || null,
    description,
  };
}
