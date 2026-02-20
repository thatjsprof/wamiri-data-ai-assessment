import React from "react";
import { formatSlaHours, slaUrgency, SLA_URGENCY_ICON, displayId } from "../../utils/format";
import type { ReviewItem } from "../../types";

const asideStyle: React.CSSProperties = {
  borderRight: "1px solid #eee",
  padding: 12,
  overflow: "auto",
  display: "flex",
  flexDirection: "column",
  gap: 12,
};

type QueueListProps = {
  items: ReviewItem[];
  selected: number;
  onSelect: (index: number) => void;
  onRefresh: () => void;
  onClaimNext: () => void;
  uploadSlot: React.ReactNode;
  jobStatusSlot?: React.ReactNode;
  statsSlot: React.ReactNode;
};

export function QueueList({
  items,
  selected,
  onSelect,
  onRefresh,
  onClaimNext,
  uploadSlot,
  jobStatusSlot,
  statsSlot,
}: QueueListProps) {
  return (
    <aside style={asideStyle}>
      {uploadSlot}
      {jobStatusSlot}
      <section aria-label="Queue">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <h2 style={{ margin: 0, fontSize: "1rem", fontWeight: 700 }}>QUEUE ({items.length})</h2>
          <button type="button" onClick={onRefresh} aria-label="Refresh queue">
            Refresh
          </button>
        </div>
        <button type="button" onClick={onClaimNext} style={{ width: "100%", marginBottom: 12, padding: 10 }}>
          Claim Next
        </button>
        {items.length === 0 ? (
          <div style={{ padding: 12, textAlign: "center", color: "#666", fontSize: 14 }}>
            No items in queue
          </div>
        ) : (
          items.map((it, idx) => {
            const urgency = slaUrgency(it.sla_deadline);
            const icon = SLA_URGENCY_ICON[urgency];
            return (
              <button
                key={it.id}
                type="button"
                onClick={() => onSelect(idx)}
                aria-label={`Queue item ${displayId(it.document_id)}, SLA ${formatSlaHours(it.sla_deadline)}`}
                aria-pressed={idx === selected}
                style={{
                  width: "100%",
                  textAlign: "left",
                  padding: 10,
                  marginBottom: 6,
                  borderRadius: 8,
                  border: idx === selected ? "2px solid #000" : "1px solid #ddd",
                  background: "#fff",
                  cursor: "pointer",
                }}
              >
                <span aria-hidden="true">{icon} </span>
                {displayId(it.document_id)} <span aria-hidden="true">[{formatSlaHours(it.sla_deadline)}]</span>
                {it.status === "claimed" && (
                  <span style={{ fontSize: 11, opacity: 0.7, display: "block", marginTop: 4 }}>
                    Claimed
                  </span>
                )}
              </button>
            );
          })
        )}
      </section>
      {statsSlot}
    </aside>
  );
}
