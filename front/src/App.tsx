import React, { useState } from "react";
import axios from "axios";
import MainLayout from "./layouts/MainLayout";
import Login from "./components/Login";

type UploadedFile = {
  name: string;
  size: number;
};

export default function App() {
  const currentPath = window.location.pathname;

  // View state: if path is /login, show Login view
  if (currentPath === "/login" || currentPath === "/login/") {
    return <Login />;
  }

  // Dashboard states
  const [executiveSummary, setExecutiveSummary] = useState<any>(null);
  const [complianceResults, setComplianceResults] = useState<any[]>([]);
  const [riskResults, setRiskResults] = useState<any[]>([]);
  const [mitigationResults, setMitigationResults] = useState<any[]>([]);
  const [reportPath, setReportPath] = useState("");
  const [config, setConfig] = useState<any>({});
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [sessionKey, setSessionKey] = useState<string>("");
  const [loadingMessage, setLoadingMessage] = useState<string>("Initializing analysis...");

  // UI states
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [activeTab, setActiveTab] = useState<"compliance" | "risk" | "mitigation">("compliance");

  // Upload file API handler
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    setLoadingMessage("Uploading document...");
    setError("");
    setWarnings([]);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    let pollInterval: any = null;
    const startPollingProgress = () => {
      pollInterval = setInterval(async () => {
        try {
          const res = await axios.get("/api/upload-progress/");
          if (res.data && res.data.progress_message) {
            setLoadingMessage(res.data.progress_message);
          }
        } catch (err) {
          // ignore progress errors
        }
      }, 800);
    };

    startPollingProgress();

    try {
      const response = await axios.post("/api/upload/", formData);
      if (response.data) {
        setUploadedFiles(response.data.files || []);
        setExecutiveSummary(response.data.executive_summary || null);
        setComplianceResults(response.data.compliance_results || []);
        setRiskResults(response.data.risk_results || []);
        setMitigationResults(response.data.mitigation_results || []);
        setReportPath(response.data.report_path || "");
        setConfig(response.data.config || {});
        setSessionKey(response.data.session_key || "");

        if (response.data.warnings && response.data.warnings.length > 0) {
          setWarnings(response.data.warnings);
        }
        if (response.data.error) {
          setError(response.data.error);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Error uploading files");
    } finally {
      setIsUploading(false);
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    }
  };

  // Remove file API handler
  const handleFileRemove = async (filename: string) => {
    setError("");
    try {
      const response = await axios.post("/api/remove_file/", { filename });
      if (response.data) {
        setUploadedFiles(response.data.files || []);
        if (!response.data.files || response.data.files.length === 0) {
          // Clear all analysis results if no files left
          setExecutiveSummary(null);
          setComplianceResults([]);
          setRiskResults([]);
          setMitigationResults([]);
          setReportPath("");
          setWarnings([]);
          setSessionKey("");
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Error removing file");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  // Helper to escape CSV values and download file
  const downloadCSV = (headers: string[], rows: any[][], filename: string) => {
    const escapeCsvValue = (val: any) => {
      if (val === null || val === undefined) return "";
      let stringVal = String(val).trim();
      stringVal = stringVal.replace(/"/g, '""');
      if (stringVal.includes(",") || stringVal.includes('"') || stringVal.includes("\n") || stringVal.includes("\r")) {
        return `"${stringVal}"`;
      }
      return stringVal;
    };

    const csvContent = [
      headers.map(escapeCsvValue).join(","),
      ...rows.map((row) => row.map(escapeCsvValue).join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadComplianceCSV = () => {
    const headers = ["Clause", "Requirement"];
    if (config?.showClauseSummaryColumn === true) {
      headers.push("Key Details Summary");
    }
    if (config?.showStatusColumn === true) {
      headers.push("Compliance Status");
    }
    headers.push("Evidence Reference", "Assessor Remarks");
    if (config?.showHistoricalActionColumn === true) {
      headers.push("Historical Action Taken");
    }

    const rows = complianceResults.map((clause) => {
      const row = [clause.clause, clause.requirement];
      if (config?.showClauseSummaryColumn === true) {
        row.push(clause.clause_summary || "");
      }
      if (config?.showStatusColumn === true) {
        row.push(clause.status || "");
      }
      row.push(clause.evidence || "", clause.remarks || "");
      if (config?.showHistoricalActionColumn === true) {
        row.push(clause.historical_action || "");
      }
      return row;
    });

    downloadCSV(headers, rows, "compliance_evaluation_report.csv");
  };

  const downloadRiskCSV = () => {
    const headers = [
      "Clause",
      "Requirement",
      "RAG Priority",
      "Identified Risk",
      "Technical Rationale",
      "Suggested Mitigation",
      "Evidence Context",
    ];

    const rows = riskResults.map((row) => [
      row.clause,
      row.requirement,
      row.rag,
      row.risk,
      row.rationale,
      row.mitigation,
      row.evidence,
    ]);

    downloadCSV(headers, rows, "risk_assessment_report.csv");
  };

  const downloadMitigationCSV = () => {
    const headers = [
      "Clause Reference",
      "Related Risk",
      "Mitigation Recommendation Guideline",
    ];

    const rows = mitigationResults.map((row) => [
      row.clause,
      row.risk,
      row.mitigation,
    ]);

    downloadCSV(headers, rows, "mitigation_strategy_guidelines.csv");
  };

  // Determine analysis status text
  const getAnalysisStatus = () => {
    if (complianceResults.length > 0) {
      return "Compliance analysis completed";
    }
    return "Analysis status will be shown here";
  };

  return (
    <MainLayout>
      <style>{`
        .main-container, .main-content {
          width: 100%;
          max-width: none;
          padding: 0 !important;
          margin: 0 !important;
        }
        .main {
          padding: 0 !important;
        }
        .dashboard-container {
          padding: 32px;
          background-color: #F9FAFB;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          gap: 28px;
          box-sizing: border-box;
          width: 100%;
        }
        .intro-banner {
          background: linear-gradient(135deg, #810055 0%, #4a0033 100%);
          color: #ffffff;
          padding: 40px;
          border-radius: 20px;
          box-shadow: 0 4px 20px rgba(129, 0, 85, 0.12);
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .intro-banner h1 {
          margin: 0;
          font-size: 32px;
          font-weight: 700;
          color: #ffffff;
          letter-spacing: -0.02em;
        }
        .intro-banner p {
          margin: 0;
          color: #f3e8ff;
          font-size: 16px !important;
          line-height: 1.6;
          opacity: 0.95;
          max-width: 800px;
        }
        .card {
          background: #fff;
          border: 1px solid #E5E7EB;
          border-radius: 20px;
          box-shadow: 0 1px 3px rgba(16, 24, 40, .05);
          padding: 32px;
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .dropzone-card {
          border: 2px dashed #D1D5DB;
          border-radius: 20px;
          padding: 60px 40px;
          text-align: center;
          background: #FFFFFF;
          cursor: pointer;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 16px;
          box-shadow: 0 1px 3px rgba(16, 24, 40, 0.05);
        }
        .dropzone-card:hover, .dropzone-card.is-dragging {
          border-color: #810055;
          background: #FFF9FD;
          box-shadow: 0 8px 30px rgba(129, 0, 85, 0.06);
          transform: translateY(-2px);
        }
        .dropzone-icon-wrapper {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 80px;
          height: 80px;
          border-radius: 50%;
          background: #FFF0FA;
          color: #810055;
          margin-bottom: 8px;
          transition: transform 0.2s ease;
        }
        .dropzone-card:hover .dropzone-icon-wrapper {
          transform: scale(1.05);
        }
        .dropzone-icon-wrapper svg {
          width: 38px;
          height: 38px;
        }
        .dropzone-title {
          font-size: 18px;
          font-weight: 600;
          color: #111827;
        }
        .dropzone-subtitle {
          font-size: 14px;
          color: #6B7280;
        }
        .file-chips-container {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-top: 8px;
        }
        .file-row-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: #F9FAFB;
          border: 1px solid #E5E7EB;
          border-radius: 12px;
          padding: 16px 20px;
          transition: border-color 0.15s ease;
        }
        .file-row-item:hover {
          border-color: #C7D2FE;
        }
        .file-details {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .file-icon {
          color: #810055;
          display: flex;
          align-items: center;
        }
        .file-name {
          font-weight: 600;
          color: #1F2937;
          font-size: 15px;
        }
        .file-size {
          font-size: 13px;
          color: #6B7280;
          margin-top: 2px;
        }
        .file-remove-btn {
          border: 1px solid #E5E7EB;
          background: #ffffff;
          color: #EF4444;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          padding: 8px 16px;
          border-radius: 8px;
          transition: all 0.15s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .file-remove-btn:hover {
          background: #FEF2F2;
          border-color: #FCA5A5;
        }
        .loading-container {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          background: #FFF5FB;
          border: 1px solid #FFDDF4;
          border-radius: 16px;
          margin-top: 12px;
        }
        .loading-spinner {
          width: 28px;
          height: 28px;
          border: 3.5px solid #FFF0FA;
          border-top: 3.5px solid #810055;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .loading-text {
          font-size: 15px;
          font-weight: 600;
          color: #810055;
        }
        .status-badge-complete {
          background: #DCFCE7;
          color: #166534;
          border: 1px solid #BBF7D0;
          padding: 6px 14px;
          border-radius: 999px;
          font-size: 13px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .results-container {
          display: flex;
          flex-direction: column;
          gap: 28px;
          margin-top: 12px;
        }
        .results-header-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 16px;
          padding-bottom: 8px;
        }
        .results-title {
          font-size: 26px;
          font-weight: 700;
          color: #111827;
          margin: 0;
          letter-spacing: -0.02em;
        }
        .download-report-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: #810055;
          color: #ffffff !important;
          text-decoration: none;
          font-weight: 600;
          padding: 12px 24px;
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(129, 0, 85, 0.15);
          transition: all 0.2s ease;
          font-size: 15px;
        }
        .download-report-btn:hover {
          background: #6a0048;
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(129, 0, 85, 0.25);
        }
        .executive-card {
          border: 1px solid #E5E7EB;
          border-radius: 20px;
          background: #fff;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(16, 24, 40, .05);
          border-left: 5px solid #810055;
        }
        .executive-header {
          background: #F9FAFB;
          border-bottom: 1px solid #E5E7EB;
          padding: 20px 28px;
          font-weight: 700;
          color: #111827;
          font-size: 20px !important;
        }
        .executive-body {
          padding: 28px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .executive-body p {
          font-size: 16px !important;
          line-height: 1.6;
          margin: 0;
          color: #374151;
        }
        .executive-body h6 {
          font-size: 17px !important;
          font-weight: 600;
          color: #111827;
          margin: 20px 0 8px 0;
        }
        .executive-body ul {
          margin: 0;
          padding-left: 24px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .executive-body li {
          font-size: 15px !important;
          line-height: 1.6;
          color: #4B5563;
        }
        
        /* Tab Navigation */
        .tab-nav {
          display: flex;
          gap: 4px;
          border-bottom: 1px solid #E5E7EB;
          padding-bottom: 2px;
          margin-top: 12px;
        }
        .tab-btn {
          background: none;
          border: none;
          padding: 14px 24px;
          font-size: 15px;
          font-weight: 600;
          color: #6B7280;
          cursor: pointer;
          position: relative;
          transition: all 0.2s ease;
          border-radius: 8px 8px 0 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .tab-btn:hover {
          color: #810055;
          background: #FFF5FB;
        }
        .tab-btn.active {
          color: #810055;
        }
        .tab-btn.active::after {
          content: "";
          position: absolute;
          bottom: -3px;
          left: 0;
          right: 0;
          height: 3px;
          background: #810055;
          border-radius: 99px;
        }

        /* Custom Table Card */
        .table-card {
          background: #ffffff;
          border: 1px solid #E5E7EB;
          border-radius: 20px;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(16, 24, 40, 0.05);
        }
        .table-card-header {
          padding: 20px 28px;
          border-bottom: 1px solid #E5E7EB;
          background: #ffffff;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .table-card-title {
          font-size: 18px;
          font-weight: 600;
          color: #111827;
          margin: 0;
        }
        .download-table-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: #ffffff;
          border: 1px solid #E5E7EB;
          color: #374151;
          font-weight: 600;
          padding: 8px 16px;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 14px;
          text-decoration: none;
        }
        .download-table-btn:hover {
          background: #FFF5FB;
          border-color: #810055;
          color: #810055;
        }
        .analysis-table-container {
          overflow-x: auto;
          width: 100%;
        }
        .analysis-table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
          font-size: 14px;
          color: #374151;
        }
        .analysis-table th {
          background-color: #F9FAFB;
          color: #4B5563;
          font-weight: 600;
          padding: 16px 20px;
          border-bottom: 1px solid #E5E7EB;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .analysis-table td {
          padding: 16px 20px;
          border-bottom: 1px solid #F3F4F6;
          vertical-align: top;
          line-height: 1.5;
        }
        .analysis-table tbody tr:last-child td {
          border-bottom: none;
        }
        .analysis-table tbody tr:hover {
          background-color: #FFFDFD;
        }
        .status-pill {
          display: inline-flex;
          align-items: center;
          padding: 4px 10px;
          border-radius: 999px;
          font-size: 13px;
          font-weight: 600;
        }
        .status-pill.met {
          background: #DCFCE7;
          color: #166534;
        }
        .status-pill.partial {
          background: #FEF3C7;
          color: #D97706;
        }
        .status-pill.not-met {
          background: #FEF2F2;
          color: #B91C1C;
        }
        .status-error {
          background: #FEF2F2;
          border: 1px solid #FECACA;
          color: #B91C1C;
          border-radius: 12px;
          padding: 16px;
          font-size: .95rem;
          font-weight: 500;
        }
        .status-warning {
          background: #FFFBEB;
          border: 1px solid #FDE68A;
          color: #7C2D12;
          border-radius: 12px;
          padding: 16px;
          font-size: .95rem;
        }
        .status-notice {
          background: #ECFDF5;
          border: 1px solid #A7F3D0;
          color: #065F46;
          border-radius: 12px;
          padding: 16px;
          font-size: .95rem;
        }
      `}</style>

      <div className="dashboard-container">
        {/* Intro Banner */}
        <div className="intro-banner">
          <h1>{config?.heroTitle || "📄 AI-Powered Contract Review Platform"}</h1>
          <p>
            {config?.heroSubtitle ||
              "Upload and review agreements instantly. Our Generative AI engine extracts critical clauses, highlights compliance statuses, maps project risks, and details mitigation guidelines."}
          </p>
        </div>

        {/* Upload Card */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#111827" }}>Upload Document</h3>
            {complianceResults.length > 0 && (
              <div className="status-badge-complete">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {getAnalysisStatus()}
              </div>
            )}
          </div>

          <div
            className={`dropzone-card ${isDragging ? "is-dragging" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("uploadFiles")?.click()}
          >
            <div className="dropzone-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div className="dropzone-title">
              Drag &amp; drop your contract file here, or click to browse
            </div>
            <div className="dropzone-subtitle">
              Accepts PDF, DOC, and DOCX files
            </div>
            <input
              id="uploadFiles"
              type="file"
              name="files"
              accept=".pdf,.docx,.doc"
              multiple
              style={{ display: "none" }}
              onChange={(e) => handleFileUpload(e.target.files)}
            />
          </div>

          {/* Uploaded Documents List */}
          {uploadedFiles.length > 0 && (
            <div style={{ marginTop: "4px" }}>
              <div className="file-chips-container">
                {uploadedFiles.map((file, i) => (
                  <div className="file-row-item" key={i}>
                    <div className="file-details">
                      <div className="file-icon">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                          <line x1="16" y1="13" x2="8" y2="13" />
                          <line x1="16" y1="17" x2="8" y2="17" />
                          <polyline points="10 9 9 9 8 9" />
                        </svg>
                      </div>
                      <div>
                        <div className="file-name">{file.name}</div>
                        <div className="file-size">{(file.size / 1024).toFixed(1)} KB</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="file-remove-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleFileRemove(file.name);
                      }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Loading Animation */}
          {isUploading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <div className="loading-text">
                {loadingMessage}
              </div>
            </div>
          )}
        </div>

        {/* Dynamic Alerts */}
        {error && (
          <div id="statusError" className="status-error" role="alert">
            {error}
          </div>
        )}

        {notice && (
          <div id="statusNotice" className="status-notice" aria-live="polite">
            {notice}
          </div>
        )}

        {warnings.length > 0 && (
          <div id="statusWarnings" className="status-warning" aria-live="polite">
            <strong style={{ display: "block", marginBottom: "6px" }}>Upload Checklist Notices:</strong>
            <ul id="statusWarningsList" style={{ margin: 0, paddingLeft: "20px" }}>
              {warnings.map((w, i) => (
                <li key={i} style={{ marginBottom: "4px" }}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Results Panels */}
        {(executiveSummary || complianceResults.length > 0 || riskResults.length > 0 || mitigationResults.length > 0) && (
          <div className="results-container">
            <div className="results-header-actions">
              <h2 className="results-title">Analysis Dashboard</h2>
              {reportPath && (
                <a
                  href="/api/download-report/"
                  className="download-report-btn"
                  target="_blank"
                  rel="noreferrer"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Download DOCX Report
                </a>
              )}
            </div>

            {/* Executive Summary Card */}
            {executiveSummary && config?.showExecutiveSummary === true && (
              <div className="executive-card">
                <div className="executive-header">
                  Executive Summary
                </div>
                <div className="executive-body">
                  <p>
                    <strong>Overall Risk Rating:</strong>{" "}
                    <span style={{
                      padding: "4px 12px",
                      borderRadius: "999px",
                      fontWeight: 700,
                      fontSize: "13px",
                      backgroundColor: executiveSummary?.overall_rating?.toLowerCase().includes("high") ? "#FEF2F2" : "#ECFDF5",
                      color: executiveSummary?.overall_rating?.toLowerCase().includes("high") ? "#B91C1C" : "#065F46",
                      border: executiveSummary?.overall_rating?.toLowerCase().includes("high") ? "1px solid #FCA5A5" : "1px solid #6EE7B7",
                      display: "inline-block",
                      marginLeft: "8px"
                    }}>
                      {executiveSummary?.overall_rating}
                    </span>
                  </p>
                  <p style={{ marginTop: "16px" }}>
                    {executiveSummary?.executive_narrative}
                  </p>

                  <h6>Key Findings</h6>
                  <ul>
                    {(executiveSummary?.top_findings || []).map((item: string, i: number) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>

                  <h6>Recommendation</h6>
                  <p>{executiveSummary?.recommendation}</p>
                </div>
              </div>
            )}

            {/* Sleek Tabbed Panel Area */}
            <div className="tab-nav">
              <button
                type="button"
                className={`tab-btn ${activeTab === "compliance" ? "active" : ""}`}
                onClick={() => setActiveTab("compliance")}
              >
                📋 Compliance Check
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === "risk" ? "active" : ""}`}
                onClick={() => setActiveTab("risk")}
              >
                ⚠️ Risk Assessment
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === "mitigation" ? "active" : ""}`}
                onClick={() => setActiveTab("mitigation")}
              >
                🛡️ Mitigation Recommendations
              </button>
            </div>

            {/* Tab 1: Compliance Results */}
            {activeTab === "compliance" && (
              <div className="table-card">
                <div className="table-card-header">
                  <h3 className="table-card-title">Compliance Evaluation Table</h3>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      className="download-table-btn"
                      onClick={downloadComplianceCSV}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      Export CSV
                    </button>
                    <a
                      href={`/api/download-table-docx/?type=compliance&session_key=${sessionKey}`}
                      className="download-table-btn"
                      target="_blank"
                      rel="noreferrer"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      Export DOCX
                    </a>
                  </div>
                </div>
                {complianceResults.length > 0 ? (
                  <div className="analysis-table-container">
                    <table className="analysis-table">
                      <thead>
                        <tr>
                          <th>Clause</th>
                          <th>Requirement</th>
                          {config?.showClauseSummaryColumn === true && (
                            <th>Key Details Summary</th>
                          )}
                          {config?.showStatusColumn === true && (
                            <th>Compliance Status</th>
                          )}
                          <th>Evidence Reference</th>
                          <th>Assessor Remarks</th>
                          {config?.showHistoricalActionColumn === true && (
                            <th>Historical Action Taken</th>
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {complianceResults.map((clause, i) => (
                          <tr key={i}>
                            <td style={{ fontWeight: 600, color: "#111827", whiteSpace: "nowrap" }}>{clause.clause}</td>
                            <td style={{ minWidth: "220px" }}>{clause.requirement}</td>
                            {config?.showClauseSummaryColumn === true && (
                              <td>{clause.clause_summary}</td>
                            )}
                            {config?.showStatusColumn === true && (
                              <td>
                                <span className={`status-pill ${clause.status === "Met" ? "met" : clause.status === "Partially Met" ? "partial" : "not-met"
                                  }`}>
                                  {clause.status === "Met" ? "✓ Met" : clause.status === "Partially Met" ? "⚠ Partial" : "✕ Not Met"}
                                </span>
                              </td>
                            )}
                            <td>{clause.evidence}</td>
                            <td>{clause.remarks}</td>
                            {config?.showHistoricalActionColumn === true && (
                              <td>{clause.historical_action}</td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: "28px", color: "#6B7280", textAlign: "center" }}>
                    No compliance check results extracted.
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Risk Assessment Results */}
            {activeTab === "risk" && (
              <div className="table-card">
                <div className="table-card-header">
                  <h3 className="table-card-title">Risk Matrix & Evidence</h3>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      className="download-table-btn"
                      onClick={downloadRiskCSV}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      Export CSV
                    </button>
                    <a
                      href={`/api/download-table-docx/?type=risk&session_key=${sessionKey}`}
                      className="download-table-btn"
                      target="_blank"
                      rel="noreferrer"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      Export DOCX
                    </a>
                  </div>
                </div>
                {riskResults.length > 0 ? (
                  <div className="analysis-table-container">
                    <table className="analysis-table">
                      <thead>
                        <tr>
                          <th>Clause</th>
                          <th>Requirement</th>
                          <th>RAG Priority</th>
                          <th>Identified Risk</th>
                          <th>Technical Rationale</th>
                          <th>Suggested Mitigation</th>
                          <th>Evidence Context</th>
                        </tr>
                      </thead>
                      <tbody>
                        {riskResults.map((row, i) => (
                          <tr key={i}>
                            <td style={{ fontWeight: 600, color: "#111827", whiteSpace: "nowrap" }}>{row.clause}</td>
                            <td style={{ minWidth: "180px" }}>{row.requirement}</td>
                            <td style={{ whiteSpace: "nowrap" }}>
                              <span style={{
                                padding: "4px 10px",
                                borderRadius: "999px",
                                fontSize: "13px",
                                fontWeight: 700,
                                backgroundColor: row.rag === "Green" ? "#DCFCE7" : row.rag === "Amber" ? "#FEF3C7" : "#FEF2F2",
                                color: row.rag === "Green" ? "#166534" : row.rag === "Amber" ? "#D97706" : "#B91C1C",
                              }}>
                                {row.rag === "Green" ? "🟢 Green" : row.rag === "Amber" ? "🟠 Amber" : "🔴 Red"}
                              </span>
                            </td>
                            <td>{row.risk}</td>
                            <td>{row.rationale}</td>
                            <td>{row.mitigation}</td>
                            <td>{row.evidence}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: "28px", color: "#6B7280", textAlign: "center" }}>
                    No risk assessment results extracted.
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Mitigation Recommendation Results */}
            {activeTab === "mitigation" && (
              <div className="table-card">
                <div className="table-card-header">
                  <h3 className="table-card-title">Mitigation Strategy Guidelines</h3>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      className="download-table-btn"
                      onClick={downloadMitigationCSV}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      Export CSV
                    </button>
                    <a
                      href={`/api/download-table-docx/?type=mitigation&session_key=${sessionKey}`}
                      className="download-table-btn"
                      target="_blank"
                      rel="noreferrer"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      Export DOCX
                    </a>
                  </div>
                </div>
                {mitigationResults.length > 0 ? (
                  <div className="analysis-table-container">
                    <table className="analysis-table">
                      <thead>
                        <tr>
                          <th style={{ width: "20%" }}>Clause Reference</th>
                          <th style={{ width: "35%" }}>Related Risk</th>
                          <th style={{ width: "45%" }}>Mitigation Recommendation Guideline</th>
                        </tr>
                      </thead>
                      <tbody>
                        {mitigationResults.map((row, i) => (
                          <tr key={i}>
                            <td style={{ fontWeight: 600, color: "#111827", whiteSpace: "nowrap" }}>{row.clause}</td>
                            <td>{row.risk}</td>
                            <td>{row.mitigation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: "28px", color: "#6B7280", textAlign: "center" }}>
                    No mitigation strategy guidelines extracted.
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}