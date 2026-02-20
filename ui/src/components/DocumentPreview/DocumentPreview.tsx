import React from "react";

const sectionStyle: React.CSSProperties = { marginBottom: 16 };
const placeholderStyle: React.CSSProperties = {
  border: "1px solid #eee",
  borderRadius: 8,
  minHeight: 280,
  background: "#f8f9fa",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#666",
};

export function DocumentPreview() {
  return (
    <section aria-label="Document preview" style={sectionStyle}>
      <h2 style={{ margin: "0 0 8px 0", fontSize: "1rem", fontWeight: 700 }}>DOCUMENT PREVIEW</h2>
      <div style={placeholderStyle}>Document viewer (PDF/image) — preview not yet served by API</div>
    </section>
  );
}
