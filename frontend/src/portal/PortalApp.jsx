import { useEffect, useState } from "react";
import App from "../App";
import { authMe, clearAuthToken, getAuthToken } from "../api";
import AuthPage from "./AuthPage";
import Landing from "./Landing";
import "./portal.css";

const publicPages = new Set(["home", "login"]);
const pageFromHash = () => location.hash.slice(1) || "home";

export default function PortalApp() {
  const [page, setPage] = useState(pageFromHash);
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(Boolean(getAuthToken()));

  const navigate = (next) => {
    location.hash = next;
    setPage(next);
    window.scrollTo(0, 0);
  };

  useEffect(() => {
    const change = () => setPage(pageFromHash());
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);

  useEffect(() => {
    let disposed = false;
    if (!getAuthToken()) {
      setCheckingSession(false);
      return undefined;
    }
    setCheckingSession(true);
    authMe()
      .then((nextUser) => {
        if (!disposed) setUser(nextUser);
      })
      .catch(() => {
        clearAuthToken();
        if (!disposed) setUser(null);
      })
      .finally(() => {
        if (!disposed) setCheckingSession(false);
      });
    return () => {
      disposed = true;
    };
  }, []);

  useEffect(() => {
    if (user && page === "login") {
      location.hash = "overview";
      setPage("overview");
      window.scrollTo(0, 0);
    }
  }, [user, page]);

  const onAuthenticated = (nextUser) => {
    setUser(nextUser);
    navigate("overview");
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
    navigate("home");
  };

  if (checkingSession) {
    return (
      <div className="sessionSplash">
        <div className="sessionSpinner" />
        <b>Restoring FreshFusion session</b>
        <span>Validating your signed access token…</span>
      </div>
    );
  }

  if (page === "home") return <Landing user={user} navigate={navigate} />;
  if (page === "login") {
    if (user) {
      return (
        <div className="sessionSplash">
          <div className="sessionSpinner" />
          <b>Opening FreshFusion workspace</b>
          <span>Your authenticated session is ready…</span>
        </div>
      );
    }
    return <AuthPage onAuthenticated={onAuthenticated} navigate={navigate} />;
  }

  if (!user && !publicPages.has(page)) {
    return <AuthPage onAuthenticated={onAuthenticated} navigate={navigate} />;
  }

  return <App user={user} onLogout={logout} />;
}
