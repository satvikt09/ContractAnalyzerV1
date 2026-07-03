import React, { useState, useEffect } from "react";

type Props = {
  children: React.ReactNode;
  navLeftLabel?: string;
  username?: string;
  currentTime?: string;
};

export default function MainLayout({
  children,
  navLeftLabel = "Contract Analysis Agent",
  username = "User",
}: Props) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [liveDateTime, setLiveDateTime] = useState("");

  useEffect(() => {
    const updateDateTime = () => {
      const now = new Date();
      const dateStr = now.toLocaleDateString("en-US", {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
      });
      const timeStr = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      setLiveDateTime(`${dateStr} ${timeStr}`);
    };

    updateDateTime();
    const interval = setInterval(updateDateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={`rail-shell ${isSidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <style>{`
        .rail-shell {
          display: grid !important;
          grid-template-columns: 280px 1fr;
          transition: grid-template-columns 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .rail-shell.sidebar-collapsed {
          grid-template-columns: 0px 1fr !important;
        }
        .rail-shell .side-bar {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          overflow: hidden;
          white-space: nowrap;
        }
        .rail-shell .bottom-item {
          white-space: normal;
        }
        .rail-shell.sidebar-collapsed .side-bar {
          width: 0 !important;
          max-width: 0 !important;
          min-width: 0 !important;
          opacity: 0 !important;
          border-right: none !important;
          padding: 0 !important;
        }
        .sidebar-toggle-btn:hover {
          color: #810055 !important;
          background-color: #f3f4f6 !important;
        }
        .header-datetime {
          margin-left: 16px;
          color: #6B7280;
          font-size: 14px;
          font-weight: 500;
          display: flex;
          align-items: center;
        }
      `}</style>

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
              <a className="bottom-item active" href="#" aria-current="page">Contract Analyser</a>
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
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
              className="sidebar-toggle-btn"
              aria-label="Toggle Sidebar"
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "8px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "8px",
                transition: "all 0.2s ease",
                color: "#4B5563"
              }}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                {isHovered ? (
                  isSidebarCollapsed ? (
                    // Right arrow to expand
                    <>
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </>
                  ) : (
                    // Left arrow to collapse
                    <>
                      <line x1="19" y1="12" x2="5" y2="12" />
                      <polyline points="12 19 5 12 12 5" />
                    </>
                  )
                ) : (
                  // Hamburger
                  <>
                    <line x1="4" y1="6" x2="20" y2="6" />
                    <line x1="4" y1="12" x2="20" y2="12" />
                    <line x1="4" y1="18" x2="20" y2="18" />
                  </>
                )}
              </svg>
            </button>
            <div className="app-logo">
              <img src="/logo.svg" alt="App Logo" />
            </div>
            <div className="header-context">{navLeftLabel}</div>
            <div className="header-datetime">
              {liveDateTime}
            </div>
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