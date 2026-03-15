import { BulletEntry, Collection } from "@/types/bullet";

const ENTRIES_KEY = "bullet-journal-entries";
const COLLECTIONS_KEY = "bullet-journal-collections";

function getEntries(): BulletEntry[] {
  if (typeof window === "undefined") return [];
  const data = localStorage.getItem(ENTRIES_KEY);
  return data ? JSON.parse(data) : [];
}

function saveEntries(entries: BulletEntry[]): void {
  localStorage.setItem(ENTRIES_KEY, JSON.stringify(entries));
}

export function getEntriesByDate(date: string): BulletEntry[] {
  return getEntries()
    .filter((e) => e.date === date && !e.collection)
    .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
}

export function getEntriesByMonth(yearMonth: string): BulletEntry[] {
  return getEntries()
    .filter((e) => e.date.startsWith(yearMonth) && !e.collection)
    .sort((a, b) => a.date.localeCompare(b.date) || new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
}

export function getEntriesByCollection(collectionId: string): BulletEntry[] {
  return getEntries()
    .filter((e) => e.collection === collectionId)
    .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
}

export function addEntry(
  entry: Omit<BulletEntry, "id" | "createdAt" | "updatedAt">
): BulletEntry {
  const entries = getEntries();
  const now = new Date().toISOString();
  const newEntry: BulletEntry = {
    ...entry,
    id: crypto.randomUUID(),
    createdAt: now,
    updatedAt: now,
  };
  entries.push(newEntry);
  saveEntries(entries);
  return newEntry;
}

export function updateEntry(
  id: string,
  updates: Partial<BulletEntry>
): BulletEntry | null {
  const entries = getEntries();
  const index = entries.findIndex((e) => e.id === id);
  if (index === -1) return null;
  entries[index] = {
    ...entries[index],
    ...updates,
    updatedAt: new Date().toISOString(),
  };
  saveEntries(entries);
  return entries[index];
}

export function deleteEntry(id: string): boolean {
  const entries = getEntries();
  const filtered = entries.filter((e) => e.id !== id);
  if (filtered.length === entries.length) return false;
  saveEntries(filtered);
  return true;
}

export function migrateEntry(id: string, newDate: string): BulletEntry | null {
  return updateEntry(id, { state: "migrated", date: newDate });
}

// Collections
export function getCollections(): Collection[] {
  if (typeof window === "undefined") return [];
  const data = localStorage.getItem(COLLECTIONS_KEY);
  return data ? JSON.parse(data) : [];
}

function saveCollections(collections: Collection[]): void {
  localStorage.setItem(COLLECTIONS_KEY, JSON.stringify(collections));
}

export function addCollection(name: string): Collection {
  const collections = getCollections();
  const newCollection: Collection = {
    id: crypto.randomUUID(),
    name,
    createdAt: new Date().toISOString(),
  };
  collections.push(newCollection);
  saveCollections(collections);
  return newCollection;
}

export function deleteCollection(id: string): boolean {
  const collections = getCollections();
  const filtered = collections.filter((c) => c.id !== id);
  if (filtered.length === collections.length) return false;
  saveCollections(filtered);
  // Also delete all entries in this collection
  const entries = getEntries();
  saveEntries(entries.filter((e) => e.collection !== id));
  return true;
}

export function getDatesWithEntries(yearMonth: string): Set<string> {
  const entries = getEntries().filter(
    (e) => e.date.startsWith(yearMonth) && !e.collection
  );
  return new Set(entries.map((e) => e.date));
}

export function getOpenTaskCount(): number {
  return getEntries().filter((e) => e.type === "task" && e.state === "open").length;
}
