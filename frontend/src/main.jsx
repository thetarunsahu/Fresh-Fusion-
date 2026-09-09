import React from "react";
import ReactDOM from "react-dom/client";
import PortalApp from "./portal/PortalApp.jsx";
import ErrorBoundary from "./shared/ErrorBoundary.jsx";
import "./styles.css";
import "./auto.css";
import "./validation.css";
import "./figma-ui.css";
import "./figma-ui-extensions.css";
import "./figma-ui-portal.css";
import "./runtime-safety.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ErrorBoundary>
      <PortalApp />
    </ErrorBoundary>
  </React.StrictMode>,
);
