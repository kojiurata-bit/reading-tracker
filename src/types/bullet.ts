export type BulletType = "task" | "event" | "note";
export type TaskState = "open" | "done" | "migrated" | "scheduled" | "cancelled";

export interface BulletEntry {
  id: string;
  type: BulletType;
  content: string;
  state: TaskState;
  date: string; // YYYY-MM-DD
  priority: boolean;
  createdAt: string;
  updatedAt: string;
  collection?: string;
}

export interface Collection {
  id: string;
  name: string;
  createdAt: string;
}

export const BULLET_SYMBOLS: Record<BulletType, string> = {
  task: "•",
  event: "○",
  note: "–",
};

export const STATE_SYMBOLS: Record<TaskState, string> = {
  open: "",
  done: "×",
  migrated: ">",
  scheduled: "<",
  cancelled: "",
};
