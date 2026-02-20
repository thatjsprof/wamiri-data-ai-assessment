import React from "react";

type HeaderProps = {
  user: string;
  onOpenStats: () => void;
  onOpenSettings: () => void;
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "12px 20px",
  borderBottom: "1px solid #eee",
  background: "#fff",
};

export function Header({ user, onOpenStats, onOpenSettings }: HeaderProps) {
  return (
    <header style={headerStyle}>
      <h1 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700 }}>Review Dashboard</h1>
      <nav aria-label="Dashboard actions">
        <button type="button" onClick={onOpenStats} aria-label="Open stats" style={{ marginRight: 8, padding: "6px 12px" }}>
          Stats
        </button>
        <button type="button" onClick={onOpenSettings} aria-label="Open settings" style={{ marginRight: 8, padding: "6px 12px" }}>
          Settings
        </button>
        <span aria-label="Current user" style={{ padding: "6px 12px", fontWeight: 600 }}>
          {user}
        </span>
      </nav>
    </header>
  );
}
