export function formatSlaHours(ts: string): string {
  const d = new Date(ts);
  const hours = Math.max(0, Math.floor((d.getTime() - Date.now()) / 3600000));
  return `${hours}h`;
}

export type SlaUrgency = "red" | "yellow" | "green";

export function slaUrgency(ts: string): SlaUrgency {
  const d = new Date(ts);
  const hours = (d.getTime() - Date.now()) / 3600000;
  if (hours <= 2) return "red";
  if (hours <= 4) return "yellow";
  return "green";
}

export function displayId(docId: string): string {
  if (!docId) return "—";
  return docId.length > 12 ? `INV-${docId.slice(0, 8)}` : docId;
}

export function confidenceLevel(val: unknown): { label: string; pct: number } {
  if (val == null || String(val).trim() === "") return { label: "⚠", pct: 0 };
  const s = String(val).trim();
  if (s.length >= 3 && /^[\d.,]+$/.test(s)) return { label: "✓", pct: 92 };
  if (s.length >= 2) return { label: "✓", pct: 85 };
  return { label: "⚠", pct: 65 };
}

export const SLA_URGENCY_ICON: Record<SlaUrgency, string> = {
  red: "🔴",
  yellow: "🟡",
  green: "🟢",
};
