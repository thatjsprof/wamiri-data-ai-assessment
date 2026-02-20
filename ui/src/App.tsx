import React, { useEffect, useMemo, useState } from "react";
import { claimNext, fetchJob, fetchQueue, submitItem, uploadDocument } from "./api";

type ReviewItem = any;

function formatDeadline(ts: string) {
  const d = new Date(ts);
  const mins = Math.max(0, Math.floor((d.getTime() - Date.now()) / 60000));
  return `${mins}m`;
}

export default function App() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [selected, setSelected] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [user] = useState("reviewer_1");

  // Upload + job tracking
  const [uploading, setUploading] = useState(false);
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any | null>(null);

  const [corrections, setCorrections] = useState<Record<string, any>>({});
  const [mode, setMode] = useState<"view" | "correct">("view");

  async function reloadQueue() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchQueue();
      setItems(data.items || []);
      setSelected(0);
    } catch (e: any) {
      setError(e.message || "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reloadQueue();
  }, []);

  const current = items[selected];

  // Simple polling when there's an active job
  useEffect(() => {
    if (!lastJobId) return;
    let alive = true;

    async function poll() {
      try {
        const s = await fetchJob(lastJobId);
        if (!alive) return;
        setJobStatus(s);
        if (["completed", "review_pending", "failed"].includes(s.status)) return;
        setTimeout(poll, 1200);
      } catch {
        // ignore transient errors during dev
      }
    }

    poll();
    return () => {
      alive = false;
    };
  }, [lastJobId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "j") setSelected((s) => Math.min(items.length - 1, s + 1));
      if (e.key === "k") setSelected((s) => Math.max(0, s - 1));
      if (e.key === "c") setMode((m) => (m === "view" ? "correct" : "view"));
      if (e.key === "a") onApprove();
      if (e.key === "r") onReject();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [items, selected, corrections, mode]);

  async function onUpload(file: File) {
    setUploading(true);
    setError(null);
    try {
      const res = await uploadDocument(file);
      setLastJobId(res.job_id);
      setJobStatus({ status: res.status, job_id: res.job_id, document_id: res.document_id });
      // queue may update after processing; refresh after a short delay
      setTimeout(() => reloadQueue(), 1500);
    } catch (e: any) {
      setError(e.message || "upload_error");
    } finally {
      setUploading(false);
    }
  }

  async function onClaimNext() {
    await claimNext(user);
    await reloadQueue();
  }

  async function onApprove() {
    if (!current) return;
    await submitItem(current.id, { decision: "approve", corrections: {}, user });
    await reloadQueue();
  }

  async function onReject() {
    if (!current) return;
    await submitItem(current.id, { decision: "reject", reject_reason: "Not a valid invoice", user });
    await reloadQueue();
  }

  async function onSubmitCorrections() {
    if (!current) return;
    await submitItem(current.id, { decision: "correct", corrections, user });
    setCorrections({});
    setMode("view");
    await reloadQueue();
  }

  if (loading) return <div style={{ padding: 16 }}>Loading…</div>;
  if (error) return <div style={{ padding: 16 }}>Error: {error}</div>;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", height: "100vh", fontFamily: "system-ui" }}>
      <aside style={{ borderRight: "1px solid #eee", padding: 12, overflow: "auto" }}>
        <h3 style={{ marginTop: 0 }}>DocProc</h3>

        <UploadCard uploading={uploading} onUpload={onUpload} />

        {jobStatus && (
          <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 10, marginBottom: 12 }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>Last job</div>
            <div style={{ fontSize: 12, opacity: 0.75 }}>Job: {jobStatus.job_id}</div>
            <div style={{ fontSize: 12, opacity: 0.75 }}>Doc: {jobStatus.document_id}</div>
            <div style={{ fontSize: 12, marginTop: 6 }}>
              Status: <b>{String(jobStatus.status)}</b>
            </div>
            {jobStatus.review_item_id && (
              <div style={{ fontSize: 12, marginTop: 6 }}>Review item: {jobStatus.review_item_id}</div>
            )}
          </div>
        )}

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Queue ({items.length})</h3>
          <button onClick={reloadQueue}>Refresh</button>
        </div>

        <button onClick={onClaimNext} style={{ width: "100%", margin: "12px 0" }}>
          Claim Next
        </button>

        {items.map((it, idx) => (
          <button
            key={it.id}
            onClick={() => {
              setSelected(idx);
              setCorrections({});
              setMode("view");
            }}
            style={{
              width: "100%",
              textAlign: "left",
              padding: 10,
              marginBottom: 8,
              borderRadius: 10,
              border: idx === selected ? "2px solid #000" : "1px solid #ddd",
              background: "#fff",
              cursor: "pointer",
            }}
          >
            <div style={{ fontWeight: 700 }}>{it.document_id}</div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>
              SLA: {formatDeadline(it.sla_deadline)} • Priority: {it.priority}
            </div>
          </button>
        ))}
      </aside>

      <main style={{ padding: 16, overflow: "auto" }}>
        {!current ? (
          <div>No items.</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 16 }}>
            <section style={{ border: "1px solid #eee", borderRadius: 12, padding: 12 }}>
              <h3>Extraction Snapshot</h3>
              <pre style={{ whiteSpace: "pre-wrap", background: "#fafafa", padding: 12, borderRadius: 10 }}>
                {JSON.stringify(current.extraction, null, 2)}
              </pre>
            </section>

            <section style={{ border: "1px solid #eee", borderRadius: 12, padding: 12 }}>
              <h3>Actions</h3>

              <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                <button onClick={onApprove}>Approve (a)</button>
                <button onClick={() => setMode((m) => (m === "view" ? "correct" : "view"))}>Correct (c)</button>
                <button onClick={onReject}>Reject (r)</button>
              </div>

              <FieldEditor
                label="Invoice #"
                field="invoice_number"
                item={current}
                mode={mode}
                onChange={(v) => setCorrections((c) => ({ ...c, invoice_number: v }))}
              />
              <FieldEditor
                label="Vendor"
                field="vendor_name"
                item={current}
                mode={mode}
                onChange={(v) => setCorrections((c) => ({ ...c, vendor_name: v }))}
              />
              <FieldEditor
                label="Total"
                field="total_amount"
                item={current}
                mode={mode}
                type="number"
                onChange={(v) => setCorrections((c) => ({ ...c, total_amount: Number(v) }))}
              />
              <FieldEditor
                label="Currency"
                field="currency"
                item={current}
                mode={mode}
                onChange={(v) => setCorrections((c) => ({ ...c, currency: v }))}
              />
              <FieldEditor
                label="Date"
                field="invoice_date"
                item={current}
                mode={mode}
                type="date"
                onChange={(v) => setCorrections((c) => ({ ...c, invoice_date: v }))}
              />

              {mode === "correct" && (
                <div style={{ marginTop: 12 }}>
                  <button onClick={onSubmitCorrections}>Submit Corrections</button>
                  <button
                    onClick={() => {
                      setCorrections({});
                      setMode("view");
                    }}
                    style={{ marginLeft: 8 }}
                  >
                    Cancel
                  </button>
                </div>
              )}

              <div style={{ marginTop: 16, fontSize: 12, opacity: 0.7 }}>
                Shortcuts: j/k (navigate), a (approve), r (reject), c (toggle correct)
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

function UploadCard(props: { uploading: boolean; onUpload: (f: File) => void }) {
  const [file, setFile] = useState<File | null>(null);

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 10, marginBottom: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Upload</div>
      <input
        type="file"
        accept="application/pdf,image/png,image/jpeg"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
      />
      <button
        disabled={!file || props.uploading}
        onClick={() => file && props.onUpload(file)}
        style={{ width: "100%", marginTop: 8 }}
      >
        {props.uploading ? "Uploading…" : "Upload & Process"}
      </button>
      <div style={{ fontSize: 12, opacity: 0.7, marginTop: 8 }}>
        Accepts PDF or images. OCR runs via Textract.
      </div>
    </div>
  );
}

function FieldEditor(props: {
  label: string;
  field: string;
  item: any;
  mode: "view" | "correct";
  onChange: (v: any) => void;
  type?: string;
}) {
  const fields = props.item.extraction?.fields || {};
  const val = fields[props.field] ?? "";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8, alignItems: "center", marginBottom: 10 }}>
      <div style={{ fontWeight: 600 }}>{props.label}</div>
      {props.mode === "correct" ? (
        <input
          aria-label={props.label}
          defaultValue={val}
          type={props.type || "text"}
          onChange={(e) => props.onChange(e.target.value)}
          style={{ padding: 8, borderRadius: 10, border: "1px solid #ddd" }}
        />
      ) : (
        <div style={{ padding: 8, borderRadius: 10, border: "1px solid #eee", background: "#fafafa" }}>
          {String(val)}
        </div>
      )}
    </div>
  );
}
