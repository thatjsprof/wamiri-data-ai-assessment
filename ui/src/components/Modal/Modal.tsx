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
  maxWidth: 400,
};

type ModalProps = {
  "aria-labelledby": string;
  titleId: string;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
};

export function Modal({ "aria-labelledby": ariaLabelledBy, titleId, title, onClose, children }: ModalProps) {
  return (
    <div role="dialog" aria-modal="true" aria-labelledby={titleId} style={overlayStyle}>
      <div style={panelStyle}>
        <h2 id={titleId}>{title}</h2>
        {children}
        <button type="button" onClick={onClose} style={{ marginTop: 16 }}>
          Close
        </button>
      </div>
    </div>
  );
}
