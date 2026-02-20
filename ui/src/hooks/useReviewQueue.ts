import { useCallback, useEffect, useState } from "react";
import { claimNext, fetchJob, fetchQueue, submitItem, uploadDocument } from "../api";
import type { ReviewItem } from "../types";

const DEFAULT_USER = "reviewer_1";

export function useReviewQueue(user: string = DEFAULT_USER) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<Record<string, unknown> | null>(null);

  const reloadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchQueue(user);
      console.log("Queue data received:", { itemCount: data.items?.length ?? 0, items: data.items });
      setItems(data.items ?? []);
      if (data.items && data.items.length > 0) {
        setSelected(0);
      }
    } catch (e: unknown) {
      const errMsg = (e as Error)?.message ?? "error";
      setError(errMsg);
      console.error("Failed to fetch queue:", errMsg, e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    reloadQueue();
  }, [reloadQueue]);

  const current = items[selected] ?? null;

  useEffect(() => {
    if (!lastJobId) return;
    let alive = true;
    async function poll() {
      try {
        if (!lastJobId) return;
        const s = await fetchJob(lastJobId);
        if (!alive) return;
        setJobStatus(s);
        if (["completed", "review_pending", "failed"].includes(String(s?.status))) return;
        setTimeout(poll, 1200);
      } catch {
        /* ignore */
      }
    }
    poll();
    return () => {
      alive = false;
    };
  }, [lastJobId]);

  const onUpload = useCallback(
    async (file: File) => {
      setUploading(true);
      setError(null);
      try {
        const res = await uploadDocument(file);
        setLastJobId(res.job_id);
        setJobStatus({
          status: res.status,
          job_id: res.job_id,
          document_id: res.document_id,
        });
        setTimeout(() => reloadQueue(), 1500);
      } catch (e: unknown) {
        setError((e as Error)?.message ?? "upload_error");
      } finally {
        setUploading(false);
      }
    },
    [reloadQueue]
  );

  const onClaimNext = useCallback(async () => {
    await claimNext(user);
    await reloadQueue();
  }, [user, reloadQueue]);

  const submit = useCallback(
    async (
      itemId: string,
      payload: { decision: string; corrections?: Record<string, unknown>; reject_reason?: string; user: string }
    ) => {
      await submitItem(itemId, payload);
      await reloadQueue();
    },
    [reloadQueue]
  );

  return {
    items,
    selected,
    setSelected,
    loading,
    error,
    uploading,
    jobStatus,
    current,
    reloadQueue,
    onUpload,
    onClaimNext,
    submit,
  };
}
