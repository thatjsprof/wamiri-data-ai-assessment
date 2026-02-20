import React, { useState } from "react";

type UploadCardProps = {
  uploading: boolean;
  onUpload: (file: File) => void;
};

const cardStyle: React.CSSProperties = {
  border: "1px solid #eee",
  borderRadius: 8,
  padding: 10,
};

export function UploadCard({ uploading, onUpload }: UploadCardProps) {
  const [file, setFile] = useState<File | null>(null);
  return (
    <div style={cardStyle}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Upload</div>
      <input
        type="file"
        accept="application/pdf,image/png,image/jpeg"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        aria-label="Choose file to upload"
      />
      <button
        type="button"
        disabled={!file || uploading}
        onClick={() => file && onUpload(file)}
        style={{ width: "100%", marginTop: 8 }}
      >
        {uploading ? "Uploading…" : "Upload & Process"}
      </button>
    </div>
  );
}
