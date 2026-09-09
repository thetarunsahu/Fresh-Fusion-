import {
  Bot,
  Database,
  History,
  LayoutDashboard,
  Microscope,
  ScanLine,
  Settings2,
  ShieldCheck,
} from "lucide-react";

const pages = [
  ["overview", "Overview", LayoutDashboard],
  ["inspection", "Live Inspection", ScanLine],
  ["investigation", "Investigation", Microscope],
  ["ai", "AI Copilot", Bot],
  ["validation", "Dataset & Validation", Database],
  ["history", "History & Evidence", History],
  ["system", "System", Settings2],
];

export default function WorkspaceLayout({ page, navigate, children, toolbar }) {
  return (
    <div className="workspace">
      <aside className="workspaceSidebar">
        <a className="workspaceBrand" href="#overview" onClick={() => navigate("overview")}>
          <span className="logoMark ffTextLogo">FF</span>
          <span className="brandCopy">
            <b>FreshFusion</b>
            <small>Fruit Quality Intelligence</small>
          </span>
        </a>

        <nav aria-label="Main navigation">
          {pages.map(([id, label, Icon]) => (
            <button
              key={id}
              className={page === id ? "active" : ""}
              aria-label={label}
              aria-current={page === id ? "page" : undefined}
              onClick={() => navigate(id)}
            >
              <span className="navIcon"><Icon size={16} /></span>
              <span className="navLabel">{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebarNote">
          <div className="sidebarNoteTitle">
            <ShieldCheck size={14} />
            <b>EVIDENCE FIRST</b>
          </div>
          <p>Experimental assessment<br />Calibration required</p>
        </div>
      </aside>

      <div className="workspaceMain">
        <header className="workspaceToolbar">{toolbar}</header>
        <main id="main-content">{children}</main>
        <footer className="workspaceFooter">
          <span>FreshFusion · Evidence-grounded fruit quality investigation</span>
          <span>Experimental assessment · Calibration required · No food-safety certification</span>
        </footer>
      </div>
    </div>
  );
}
