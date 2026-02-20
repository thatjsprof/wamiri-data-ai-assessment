import React from "react";

const sectionStyle: React.CSSProperties = {
  border: "1px solid #eee",
  borderRadius: 8,
  padding: 12,
  marginTop: "auto",
};

type MyStatsProps = {
  reviewedToday: number;
  avgReviewSec: number;
};

export function MyStats({ reviewedToday, avgReviewSec }: MyStatsProps) {
  return (
    <section aria-label="My stats" style={sectionStyle}>
      <h3 style={{ margin: "0 0 8px 0", fontSize: "0.9rem", fontWeight: 700 }}>MY STATS</h3>
      <div style={{ fontSize: 14 }}>Today: {reviewedToday}</div>
      <div style={{ fontSize: 14 }}>Avg: {avgReviewSec}s</div>
    </section>
  );
}
