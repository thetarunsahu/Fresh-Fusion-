import React from "react";
import ReactDOM from "react-dom/client";
import PortalApp from "./portal/PortalApp.jsx";
import "./styles.css";
import "./auto.css";
import "./validation.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <PortalApp />
  </React.StrictMode>,
);
