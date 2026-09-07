import {
  LayoutDashboard,
  ScanLine,
  Microscope,
  ListTree,
  Database,
  History,
  Leaf,
} from "lucide-react";
const pages = [
  ["overview", "Overview", LayoutDashboard],
  ["inspection", "Live Inspection", ScanLine],
  ["investigation", "Investigation", Microscope],
  ["evidence", "Evidence", ListTree],
  ["validation", "Dataset & Validation", Database],
  ["history", "History", History],
];

export default function WorkspaceLayout({ page, navigate, children, toolbar }) {
  return (
    <div className="workspace">
      <aside className="workspaceSidebar">
        <a
          className="workspaceBrand"
          href="#overview"
          onClick={() => navigate("overview")}
        >
          <span className="logoMark">
            <Leaf size={21} />
          </span>
          <span>
            <b>FreshFusion</b>
            <small>Fruit Quality Investigation</small>
          </span>
        </a>
        <span className="navCaption">INVESTIGATION WORKSPACE</span>
        <nav aria-label="Main navigation">
          {pages.map(([id, label, Icon]) => (
            <button
              key={id}
              className={page === id ? "active" : ""}
              aria-current={page === id ? "page" : undefined}
              onClick={() => navigate(id)}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebarNote">
          <b>Evidence before conclusions.</b>
          <p>
            Apple · Banana
            <br />
            Experimental SIH prototype
          </p>
        </div>
      </aside>
      <div className="workspaceMain">
        <header className="workspaceToolbar">{toolbar}</header>
        <main id="main-content">{children}</main>
        <footer className="workspaceFooter">
          Experimental assessment · Requires calibration and validation · No
          food-safety certification
        </footer>
      </div>
    </div>
  );
}
