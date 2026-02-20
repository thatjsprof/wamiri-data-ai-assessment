import React from "react";
import type { ReviewItem, ReviewMode, FieldSpec } from "../../types";

const FIELD_SPECS: FieldSpec[] = [
  { label: "Invoice #", key: "invoice_number" },
  { label: "Vendor", key: "vendor_name" },
  { label: "Total", key: "total_amount", type: "number" },
  { label: "Currency", key: "currency" },
  { label: "Date", key: "invoice_date", type: "date" },
];

const containerStyle: React.CSSProperties = {
  border: "1px solid #eee",
  borderRadius: 8,
  padding: 12,
  background: "#fff",
};

type ExtractedFieldsProps = {
  item: ReviewItem;
  mode: ReviewMode;
  corrections: Record<string, unknown>;
  setCorrections: (v: Record<string, unknown> | ((prev: Record<string, unknown>) => Record<string, unknown>)) => void;
  onSubmitCorrections: () => void;
  setMode: (v: ReviewMode) => void;
};

export function ExtractedFields({
  item,
  mode,
  corrections,
  setCorrections,
  onSubmitCorrections,
  setMode,
}: ExtractedFieldsProps) {
  const fields = item?.extraction && "fields" in item.extraction
    ? (item.extraction.fields as Record<string, unknown>)
    : (item?.extraction as Record<string, unknown>) ?? {};

  // Get confidence scores from extraction payload
  const confidence = item?.extraction && "confidence" in item.extraction
    ? (item.extraction.confidence as Record<string, number>)
    : {};

  return (
    <div style={containerStyle}>
      {FIELD_SPECS.map(({ label, key, type }) => {
        const val = corrections[key] !== undefined ? corrections[key] : fields[key];
        // Use real confidence from backend, or fallback to heuristic
        const confScore = confidence[key] ?? (val != null ? 0.85 : 0.0);
        const pct = Math.round(confScore * 100);
        const confLabel = confScore >= 0.75 ? "✓" : "⚠";
        return (
          <div
            key={key}
            style={{
              display: "grid",
              gridTemplateColumns: "120px 1fr auto",
              gap: 8,
              alignItems: "center",
              marginBottom: 10,
            }}
          >
            <span style={{ fontWeight: 600 }}>{label}:</span>
            {mode === "correct" ? (
              <input
                type={type ?? "text"}
                aria-label={label}
                defaultValue={val != null ? String(val) : ""}
                onChange={(e) =>
                  setCorrections((c) => ({
                    ...c,
                    [key]: type === "number" ? Number(e.target.value) : e.target.value,
                  }))
                }
                style={{ padding: 8, border: "1px solid #ddd", borderRadius: 6 }}
              />
            ) : (
              <span style={{ padding: 8, background: "#fafafa", borderRadius: 6 }}>
                {val != null && val !== "" ? String(val) : "—"}
              </span>
            )}
            <span aria-label={`Confidence ${pct}%`} style={{ fontSize: 14 }}>
              {confLabel} {pct}%
            </span>
          </div>
        );
      })}
      {mode === "correct" && (
        <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
          <button type="button" onClick={onSubmitCorrections}>
            Submit Corrections
          </button>
          <button
            type="button"
            onClick={() => {
              setCorrections({});
              setMode("view");
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
