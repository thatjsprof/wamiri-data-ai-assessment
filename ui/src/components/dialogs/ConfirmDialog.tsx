import React from "react";

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.3)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 10,
};

const panelStyle: React.CSSProperties = {
  background: "#fff",
  padding: 24,
  borderRadius: 12,
};

type ConfirmDialogProps = {
  titleId: string;
  title: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({ titleId, title, confirmLabel, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <div role="dialog" aria-modal="true" aria-labelledby={titleId} style={overlayStyle}>
      <div style={panelStyle}>
        <h2 id={titleId}>{title}</h2>
        <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
          <button type="button" onClick={onConfirm}>
            {confirmLabel}
          </button>
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
