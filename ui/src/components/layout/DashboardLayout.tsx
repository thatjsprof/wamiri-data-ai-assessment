import React from "react";

const rootStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  height: "100vh",
  fontFamily: "system-ui",
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "320px 1fr",
  flex: 1,
  minHeight: 0,
};

type DashboardLayoutProps = {
  sidebar: React.ReactNode;
  main: React.ReactNode;
  header: React.ReactNode;
};

export function DashboardLayout({ header, sidebar, main }: DashboardLayoutProps) {
  return (
    <div style={rootStyle}>
      {header}
      <div style={gridStyle}>
        {sidebar}
        {main}
      </div>
    </div>
  );
}
