export const API_BASE = "http://localhost:8000";

export async function uploadDocument(file: File) {
  const fd = new FormData();
  fd.append("file", file);

  const res = await fetch(`${API_BASE}/v1/process`, { method: "POST", body: fd });
  if (!res.ok) throw new Error("upload_failed");
  return res.json();
}

export async function fetchJob(jobId: string) {
  const res = await fetch(`${API_BASE}/v1/jobs/${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error("job_fetch_failed");
  return res.json();
}

export async function fetchQueue(user?: string) {
  const url = new URL(`${API_BASE}/v1/queue`);
  url.searchParams.set("limit", "50");
  url.searchParams.set("offset", "0");
  if (user) {
    url.searchParams.set("user", user);
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`failed_to_fetch_queue: ${res.status} ${text}`);
  }
  return res.json();
}

export async function claimNext(user: string) {
  const res = await fetch(`${API_BASE}/v1/queue/claim?user=${encodeURIComponent(user)}`, { method: "POST" });
  if (!res.ok) throw new Error("failed_to_claim");
  return res.json();
}

export async function submitItem(id: string, payload: any) {
  const res = await fetch(`${API_BASE}/v1/queue/${id}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("failed_to_submit");
  return res.json();
}

export type ReviewStats = {
  queue_depth: number;
  reviewed_today: number;
  avg_review_time_seconds: number;
  sla_compliance_pct: number;
};

export async function fetchReviewStats(): Promise<ReviewStats> {
  const res = await fetch(`${API_BASE}/v1/queue/stats`);
  if (!res.ok) throw new Error("failed_to_fetch_stats");
  return res.json();
}
