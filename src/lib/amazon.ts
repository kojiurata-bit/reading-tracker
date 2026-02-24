/**
 * Amazon URL parsing utilities.
 * Extracts ASINs (often ISBN-10 for physical books) from Amazon product URLs.
 */

const AMAZON_HOSTS = [
  "amazon.co.jp",
  "www.amazon.co.jp",
  "amazon.com",
  "www.amazon.com",
  "m.amazon.co.jp",
  "m.amazon.com",
];

const SHORT_HOSTS = ["amzn.to", "amzn.asia"];

/**
 * Checks whether a string looks like an Amazon product URL.
 */
export function isAmazonUrl(input: string): boolean {
  try {
    const url = new URL(input);
    const host = url.hostname.toLowerCase();
    return (
      AMAZON_HOSTS.includes(host) ||
      SHORT_HOSTS.includes(host) ||
      host.startsWith("amazon.")
    );
  } catch {
    return false;
  }
}

/**
 * Returns true if the URL is a short link (amzn.to / amzn.asia)
 * that cannot be resolved client-side.
 */
export function isShortUrl(input: string): boolean {
  try {
    const url = new URL(input);
    return SHORT_HOSTS.includes(url.hostname.toLowerCase());
  } catch {
    return false;
  }
}

/**
 * Extracts the 10-character ASIN from an Amazon product URL.
 * Supports patterns: /dp/XXX, /gp/product/XXX, /product/XXX, /ASIN/XXX
 * Returns null if no ASIN found.
 */
export function extractAsin(url: string): string | null {
  const match = url.match(
    /(?:\/dp\/|\/gp\/product\/|\/product\/|\/ASIN\/)([A-Z0-9]{10})/i
  );
  return match ? match[1] : null;
}

/**
 * Determines if an ASIN is likely an ISBN-10 (starts with a digit)
 * vs a Kindle/digital ASIN (starts with "B").
 */
export function isLikelyIsbn(asin: string): boolean {
  return /^\d/.test(asin);
}

/**
 * Attempts to extract a book title from the Amazon URL path.
 * Amazon Japan URLs often contain the title as the first path segment:
 *   /本のタイトル/dp/XXXXXXXXXX
 * Returns decoded, cleaned title or null.
 */
export function extractTitleFromUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    const segments = parsed.pathname.split("/").filter(Boolean);

    // Find the segment right before "dp", "gp", "product", or "ASIN"
    const dpIndex = segments.findIndex((s) =>
      /^(dp|gp|product|ASIN)$/i.test(s)
    );

    if (dpIndex > 0) {
      const raw = decodeURIComponent(segments[dpIndex - 1]);
      // Replace hyphens and underscores with spaces, trim
      const cleaned = raw.replace(/[-_]+/g, " ").trim();
      // Filter out very short or purely numeric segments
      if (cleaned.length > 1 && !/^\d+$/.test(cleaned)) {
        return cleaned;
      }
    }

    return null;
  } catch {
    return null;
  }
}

/**
 * Cleans the full Amazon URL to a canonical product page URL.
 */
export function cleanAmazonUrl(url: string): string {
  const asin = extractAsin(url);
  if (!asin) return url;

  try {
    const parsed = new URL(url);
    const host = parsed.hostname;
    return `https://${host}/dp/${asin}`;
  } catch {
    return url;
  }
}
