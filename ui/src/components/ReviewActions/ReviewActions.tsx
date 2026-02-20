import React from "react";

type ReviewActionsProps = {
  onApprove: () => void;
  onReject: () => void;
  onToggleCorrect: () => void;
};

export function ReviewActions({ onApprove, onReject, onToggleCorrect }: ReviewActionsProps) {
  return (
    <section aria-label="Review actions">
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="button" onClick={onApprove} aria-label="Approve (shortcut a)">
          Approve
        </button>
        <button type="button" onClick={onToggleCorrect} aria-label="Toggle correct mode (shortcut c)">
          Correct
        </button>
        <button type="button" onClick={onReject} aria-label="Reject (shortcut r)">
          Reject
        </button>
      </div>
      <p style={{ marginTop: 12, fontSize: 12, color: "#666" }}>
        Shortcuts: j/k navigate, a approve, r reject, c toggle correct
      </p>
    </section>
  );
}
