import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { StatusBadge } from "./StatusBadge";
import "./Layout.css";

interface LayoutProps {
  apiOnline: boolean;
  apiLoading: boolean;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  version: string;
}

export function Layout({ apiOnline, apiLoading, apiKey, onApiKeyChange, version }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="layout">
      <Sidebar apiKey={apiKey} onApiKeyChange={onApiKeyChange} />
      <div className="layout-main">
        <div className="layout-topbar">
          <div className="layout-topbar-left">
            <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
              ☰
            </button>
            <StatusBadge online={apiOnline} loading={apiLoading} />
          </div>
          <div className="layout-topbar-right">
            <span className="layout-topbar-title">v{version}</span>
          </div>
        </div>
        <div className="layout-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
