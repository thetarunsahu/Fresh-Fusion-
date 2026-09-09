import {
  Bot,
  Database,
  History,
  LayoutDashboard,
  Leaf,
  Microscope,
  ScanLine,
  Settings2,
  ShieldCheck,
  Sparkles,
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
      <div className="workspaceBackdrop" aria-hidden="true" />
      <aside className="workspaceSidebar">
        <a
          className="workspaceBrand"
          href="#overview"
          onClick={() => navigate("overview")}
        >
          <span className="logoMark">
            <Leaf size={21} />
          </span>
          <span className="brandCopy">
            <b>FreshFusion</b>
            <small>Fruit Quality Intelligence</small>
          </span>
        </a>

        <div className="prototypeBadge">
          <Sparkles size={14} />
          <span>SIH Investigation Prototype</span>
        </div>

        <span className="navCaption">WORKSPACE</span>
        <nav aria-label="Main navigation">
          {pages.map(([id, label, Icon], index) => (
            <button
              key={id}
              className={page === id ? "active" : ""}
              aria-label={label}
              aria-current={page === id ? "page" : undefined}
              onClick={() => navigate(id)}
            >
              <span className="navIcon">
                <Icon size={18} />
              </span>
              <span className="navLabel">{label}</span>
              <span className="navIndex">0{index + 1}</span>
            </button>
          ))}
        </nav>

        <div className="sidebarNote">
          <div className="sidebarNoteTitle">
            <ShieldCheck size={16} />
            <b>Evidence before conclusions</b>
          </div>
          <p>
            Apple · Banana
            <br />
            Multimodal experimental assessment
          </p>
        </div>
      </aside>

      <div className="workspaceMain">
        <header className="workspaceToolbar">{toolbar}</header>
        <main id="main-content">{children}</main>
        <footer className="workspaceFooter">
          <span>FreshFusion · Evidence-grounded fruit quality investigation</span>
          <span>
            Experimental assessment · Calibration required · No food-safety
            certification
          </span>
        </footer>
      </div>
    </div>
  );
}
