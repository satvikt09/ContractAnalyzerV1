import React from "react";

type Props = {
  children: React.ReactNode;
  navLeftLabel?: string;
  username?: string;
  currentTime?: string;
};

export default function MainLayout({
  children,
  navLeftLabel = "Enterprise Contract Analyzer",
  username = "User",
  currentTime = new Date().toLocaleDateString("en-US", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  }),
}: Props) {
  return (
    <div className="rail-shell">
      <aside className="side-bar">
        <div className="sidebar">
          <div className="sidebar-header">
            <div className="logo-container">
              <div className="logo">
                <img src="/logo.svg" alt="Logo" />
                <div>
                  <div className="logo-main">GEG</div>
                  <div className="logo-sub">Generative AI Platform</div>
                </div>
              </div>
            </div>
          </div>

          <div className="sidebar-content">
            <div className="bottom-header">Conversations</div>
            <a className="bottom-item" href="#">New conversation</a>
            <div className="bottom-note">Saved chats coming soon</div>

            <div className="bottom-header">Workspaces</div>
            <details className="workspace-expander" open>
              <summary>PED</summary>
              <a className="bottom-item" href="#">PED Knowledge Assistant</a>
              <a className="bottom-item active" href="#" aria-current="page">Contractual Analyzer</a>
              <a className="bottom-item" href="#">Engineering Spec Summary Chat</a>
              <a className="bottom-item" href="#">Workspace Console</a>
            </details>

            <details className="workspace-expander">
              <summary>BSI</summary>
              <a className="bottom-item" href="#">BSI Knowledge Assistant</a>
              <a className="bottom-item" href="#">BSI Tonality</a>
              <a className="bottom-item" href="#">BSI Tonality Chat</a>
            </details>

            <details className="workspace-expander">
              <summary>Interio</summary>
              <a className="bottom-item" href="#">Order Booking Agents</a>
              <a className="bottom-item" href="#">Order Booking Agents Chat</a>
              <a className="bottom-item" href="#">Multi-Address Code Gen Agent</a>
            </details>

            <details className="workspace-expander">
              <summary>Digital</summary>
              <a className="bottom-item" href="#">Digital Knowledge Assistant</a>
            </details>

            <details className="workspace-expander">
              <summary>SSD</summary>
              <a className="bottom-item" href="#">SSD Knowledge Assistant</a>
              <a className="bottom-item" href="#">Service Testimonials Agent</a>
              <a className="bottom-item" href="#">SSD - DigiNxt Agent</a>
            </details>

            <details className="workspace-expander settings-expander" open>
              <summary>Settings</summary>
              <div className="bottom-item">Hi {username}</div>
              <a className="bottom-item" href="#">Admin Console</a>
              <a className="bottom-item" href="#">Sign out</a>
            </details>
          </div>
        </div>
      </aside>

      <div className="center-panel">
        <div className="header">
          <div className="header-left">
            <div className="app-logo">
              <img src="/logo.svg" alt="App Logo" />
            </div>
            <div className="header-context">{navLeftLabel}</div>
          </div>
        </div>

        <div className="main page-fade">
          <div className="main-container">
            <div className="main-content">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}