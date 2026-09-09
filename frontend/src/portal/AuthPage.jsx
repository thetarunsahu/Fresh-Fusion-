import { useState } from "react";
import { ArrowLeft, Eye, EyeOff, Leaf, LockKeyhole, ShieldCheck, Sparkles, UserRound } from "lucide-react";
import { login, register, setAuthToken } from "../api";

export default function AuthPage({ onAuthenticated, navigate }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("operator");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const result = mode === "login"
        ? await login(email, password)
        : await register({ email, password, full_name: fullName, role });
      setAuthToken(result.access_token);
      onAuthenticated(result.user);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="authPage">
      <section className="authStoryPanel">
        <button className="backToHome" onClick={() => navigate("home")}>
          <ArrowLeft size={16} /> Back to FreshFusion
        </button>
        <div className="authStoryBrand">
          <span className="portalLogo"><Leaf size={24} /></span>
          <div><b>FreshFusion</b><small>Fruit Quality Intelligence</small></div>
        </div>
        <div className="authStoryCopy">
          <div className="portalKicker"><Sparkles size={15} /> Secure investigation workspace</div>
          <h1>Evidence deserves an accountable operator.</h1>
          <p>
            Authentication separates user access from device ingestion and gives
            human review a clear identity trail. The current SIH prototype uses
            persisted users and signed JWT sessions.
          </p>
          <div className="authFeatureList">
            <div><ShieldCheck size={18} /><span><b>Role-aware access</b><small>Admin · Operator · Reviewer</small></span></div>
            <div><LockKeyhole size={18} /><span><b>Signed sessions</b><small>JWT access token with expiry</small></span></div>
            <div><UserRound size={18} /><span><b>Accountable review</b><small>User identity can be attached to audit actions</small></span></div>
          </div>
        </div>
        <div className="authStoryFoot">
          Device authentication and secure ESP32 pairing remain a separate production-hardening step.
        </div>
      </section>

      <section className="authFormPanel">
        <div className="authFormWrap">
          <div className="authModeSwitch" role="tablist" aria-label="Authentication mode">
            <button className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setMessage(""); }}>Sign in</button>
            <button className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setMessage(""); }}>Create account</button>
          </div>

          <div className="authFormHeading">
            <span>{mode === "login" ? "WELCOME BACK" : "JOIN THE WORKSPACE"}</span>
            <h2>{mode === "login" ? "Sign in to FreshFusion" : "Create your FreshFusion account"}</h2>
            <p>{mode === "login" ? "Continue to the protected investigation workspace." : "The first registered account becomes the local administrator."}</p>
          </div>

          <form onSubmit={submit} className="authForm">
            {mode === "register" && (
              <label>
                <span>Full name</span>
                <input value={fullName} onChange={(e) => setFullName(e.target.value)} minLength={2} maxLength={120} autoComplete="name" placeholder="Tarun Kumar Sahu" required />
              </label>
            )}
            <label>
              <span>Email</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" placeholder="you@example.com" required />
            </label>
            <label>
              <span>Password</span>
              <div className="passwordField">
                <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} maxLength={128} autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder="Minimum 8 characters" required />
                <button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((value) => !value)}>
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </label>
            {mode === "register" && (
              <label>
                <span>Workspace role</span>
                <select value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="operator">Operator</option>
                  <option value="reviewer">Reviewer</option>
                </select>
                <small>Admin cannot be self-selected; only the first local account is bootstrapped as Admin.</small>
              </label>
            )}

            {message && <div className="authMessage" role="alert">{message}</div>}

            <button className="authSubmit" type="submit" disabled={busy}>
              {busy ? "Please wait…" : mode === "login" ? "Sign in securely" : "Create account"}
            </button>
          </form>

          <div className="authSecurityNote">
            <ShieldCheck size={17} />
            <div>
              <b>Prototype security boundary</b>
              <p>User authentication is real and server-validated. ESP32/device authentication is intentionally tracked as a separate production feature so hardware integration is not broken by the dashboard login layer.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
