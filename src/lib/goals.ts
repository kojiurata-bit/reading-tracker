const GOAL_KEY = "reading-tracker-goal";
const JOURNAL_KEY = "reading-tracker-journal";

export function getYearlyGoal(): number {
  if (typeof window === "undefined") return 0;
  const val = localStorage.getItem(GOAL_KEY);
  return val ? parseInt(val, 10) : 0;
}

export function setYearlyGoal(goal: number): void {
  localStorage.setItem(GOAL_KEY, String(goal));
}

export function getJournalDates(): string[] {
  if (typeof window === "undefined") return [];
  const data = localStorage.getItem(JOURNAL_KEY);
  return data ? JSON.parse(data) : [];
}

export function toggleJournalDate(date: string): string[] {
  const dates = getJournalDates();
  const idx = dates.indexOf(date);
  if (idx >= 0) {
    dates.splice(idx, 1);
  } else {
    dates.push(date);
  }
  localStorage.setItem(JOURNAL_KEY, JSON.stringify(dates));
  return dates;
}
