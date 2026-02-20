import React, { useEffect, useState, useCallback } from "react";
import { useReviewQueue } from "../hooks/useReviewQueue";
import { fetchReviewStats, type ReviewStats } from "../api";
import {
  DashboardLayout,
  Header,
  UploadCard,
  QueueList,
  JobStatus,
  MyStats,
  DocumentPreview,
  ExtractedFields,
  ReviewActions,
  StatsDialog,
  SettingsDialog,
  ConfirmDialog,
} from "../components";
import type { ReviewItem, ConfirmAction } from "../types";

const USER = "reviewer_1";

export function ReviewDashboard() {
  const queue = useReviewQueue(USER);
  const [backendStats, setBackendStats] = useState<ReviewStats | null>(null);
  const [mode, setMode] = useState<"view" | "correct">("view");
  const [corrections, setCorrections] = useState<Record<string, unknown>>({});
  const [statsOpen, setStatsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);

  const { current, items, selected, setSelected } = queue;
  const currentItem = current;

  const refetchStats = useCallback(async () => {
    try {
      const data = await fetchReviewStats();
      setBackendStats(data);
    } catch {
      // keep previous stats on error
    }
  }, []);

  useEffect(() => {
    refetchStats();
  }, [refetchStats]);

  useEffect(() => {
    if (!queue.loading) refetchStats();
  }, [queue.loading, refetchStats]);

  const handleSelect = useCallback(
    (index: number) => {
      setSelected(index);
      setCorrections({});
      setMode("view");
    },
    [setSelected]
  );

  const onApprove = useCallback(() => {
    if (currentItem) setConfirmAction("approve");
  }, [currentItem]);

  const onReject = useCallback(() => {
    if (currentItem) setConfirmAction("reject");
  }, [currentItem]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "j") setSelected((s: number) => Math.min(items.length - 1, s + 1));
      if (e.key === "k") setSelected((s: number) => Math.max(0, s - 1));
      if (e.key === "c") setMode((m) => (m === "view" ? "correct" : "view"));
      if (e.key === "a") onApprove();
      if (e.key === "r") onReject();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [items.length, setSelected, onApprove, onReject]);

  const confirmApprove = useCallback(async () => {
    if (!currentItem) return;
    await queue.submit(currentItem.id, {
      decision: "approve",
      corrections: {},
      user: USER,
    });
    setConfirmAction(null);
    refetchStats();
  }, [currentItem, queue, refetchStats]);

  const confirmReject = useCallback(async () => {
    if (!currentItem) return;
    await queue.submit(currentItem.id, {
      decision: "reject",
      reject_reason: "Not a valid invoice",
      user: USER,
    });
    setConfirmAction(null);
    refetchStats();
  }, [currentItem, queue, refetchStats]);

  const onSubmitCorrections = useCallback(async () => {
    if (!currentItem) return;
    await queue.submit(currentItem.id, {
      decision: "correct",
      corrections,
      user: USER,
    });
    setCorrections({});
    setMode("view");
    refetchStats();
  }, [currentItem, corrections, queue, refetchStats]);

  if (queue.loading) {
    return (
      <div role="status" aria-live="polite" style={{ padding: 24, fontFamily: "system-ui" }}>
        Loading…
      </div>
    );
  }
  if (queue.error) {
    return (
      <div role="alert" style={{ padding: 24, fontFamily: "system-ui", color: "#c00" }}>
        <h2>Error loading queue</h2>
        <p>{queue.error}</p>
        <button type="button" onClick={() => queue.reloadQueue()} style={{ marginTop: 12, padding: "8px 16px" }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      <DashboardLayout
        header={
          <Header
            user={USER}
            onOpenStats={() => setStatsOpen(true)}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        }
        sidebar={
          <QueueList
            items={items}
            selected={selected}
            onSelect={handleSelect}
            onRefresh={queue.reloadQueue}
            onClaimNext={queue.onClaimNext}
            uploadSlot={<UploadCard uploading={queue.uploading} onUpload={queue.onUpload} />}
            jobStatusSlot={<JobStatus jobStatus={queue.jobStatus} />}
            statsSlot={
              <MyStats
                reviewedToday={backendStats?.reviewed_today ?? 0}
                avgReviewSec={Math.round(backendStats?.avg_review_time_seconds ?? 0)}
              />
            }
          />
        }
        main={
          <main style={{ padding: 16, overflow: "auto", minWidth: 0 }}>
            {!currentItem ? (
              <p>No items in queue.</p>
            ) : (
              <>
                <DocumentPreview />
                <section aria-label="Extracted fields" style={{ marginBottom: 16 }}>
                  <h2 style={{ margin: "0 0 12px 0", fontSize: "1rem", fontWeight: 700 }}>
                    EXTRACTED FIELDS
                  </h2>
                  <ExtractedFields
                    item={currentItem as ReviewItem}
                    mode={mode}
                    corrections={corrections}
                    setCorrections={setCorrections}
                    onSubmitCorrections={onSubmitCorrections}
                    setMode={setMode}
                  />
                </section>
                <ReviewActions
                  onApprove={onApprove}
                  onReject={onReject}
                  onToggleCorrect={() => setMode((m) => (m === "view" ? "correct" : "view"))}
                />
              </>
            )}
          </main>
        }
      />
      {statsOpen && (
        <StatsDialog
          reviewedToday={backendStats?.reviewed_today ?? 0}
          avgReviewSec={Math.round(backendStats?.avg_review_time_seconds ?? 0)}
          queueDepth={backendStats?.queue_depth ?? items.length}
          slaCompliancePct={backendStats?.sla_compliance_pct ?? 0}
          onClose={() => setStatsOpen(false)}
        />
      )}
      {settingsOpen && (
        <SettingsDialog onClose={() => setSettingsOpen(false)} />
      )}
      {confirmAction === "approve" && (
        <ConfirmDialog
          titleId="confirm-approve-title"
          title="Approve this item?"
          confirmLabel="Yes, approve"
          onConfirm={confirmApprove}
          onCancel={() => setConfirmAction(null)}
        />
      )}
      {confirmAction === "reject" && (
        <ConfirmDialog
          titleId="confirm-reject-title"
          title="Reject this item?"
          confirmLabel="Yes, reject"
          onConfirm={confirmReject}
          onCancel={() => setConfirmAction(null)}
        />
      )}
    </>
  );
}
