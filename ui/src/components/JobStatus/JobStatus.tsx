import React from "react";

const cardStyle: React.CSSProperties = {
  border: "1px solid #eee",
  borderRadius: 8,
  padding: 10,
  marginBottom: 12,
  fontSize: 12,
};

const statusColors: Record<string, string> = {
  queued: "#666",
  processing: "#0066cc",
  completed: "#00aa00",
  review_pending: "#ff8800",
  failed: "#cc0000",
};

type JobStatusProps = {
  jobStatus: Record<string, unknown> | null;
};

export function JobStatus({ jobStatus }: JobStatusProps) {
  if (!jobStatus) return null;

  const status = String(jobStatus.status || "");
  const statusColor = statusColors[status] || "#666";

  return (
    <div style={cardStyle}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>Last Job</div>
      {jobStatus.job_id != null && (
        <div style={{ opacity: 0.75, marginBottom: 4 }}>
          Job: {String(jobStatus.job_id).slice(0, 8)}...
        </div>
      )}
      {jobStatus.document_id != null && (
        <div style={{ opacity: 0.75, marginBottom: 6 }}>
          Doc: {String(jobStatus.document_id).slice(0, 8)}...
        </div>
      )}
      <div style={{ marginTop: 6 }}>
        Status:{" "}
        <span style={{ fontWeight: 600, color: statusColor }}>
          {status || "unknown"}
        </span>
      </div>
      {jobStatus.review_item_id != null && (
        <div style={{ marginTop: 6, fontSize: 11, opacity: 0.7 }}>
          Review: {String(jobStatus.review_item_id).slice(0, 8)}...
        </div>
      )}
    </div>
  );
}
