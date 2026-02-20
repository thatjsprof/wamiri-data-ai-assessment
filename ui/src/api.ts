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

export async function fetchQueue() {
  const res = await fetch(`${API_BASE}/v1/queue?limit=50&offset=0`);
  if (!res.ok) throw new Error("failed_to_fetch_queue");
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
