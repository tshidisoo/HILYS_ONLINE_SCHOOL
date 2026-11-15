import { useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { api } from "./api";
import { useAuth } from "./auth";
import ErrorBoundary from "./components/ErrorBoundary";
import { Loading } from "./components/ui";
import Pay from "./screens/Pay";
import Students from "./screens/Students";
import Week from "./screens/Week";

function Login() {
  const { signIn } = useAuth();
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <main className="t-login">
      <img src="/logo.jpg" alt="" width="96" height="96" />
      <h1>HILYS teachers</h1>
      <p className="muted">Your lessons, your students and your pay.</p>
      <form onSubmit={async (e) => { e.preventDefault(); setBusy(true); setErr(""); try { await signIn(u, p); } catch (x) { setErr(x.message); setBusy(false); } }} className="stack">
        <div className="field"><label htmlFor="username">Username</label><input id="username" className="input" autoComplete="username" value={u} onChange={(e) => setU(e.target.value)} /></div>
        <div className="field"><label htmlFor="password">Password</label><input id="password" className="input" type="password" autoComplete="current-password" value={p} onChange={(e) => setP(e.target.value)} /></div>
        {err && <div className="form-error" role="alert">{err}</div>}
        <button className="btn btn-primary" disabled={busy || !u || !p}>{busy ? "Signing in…" : "Sign in"}</button>
      </form>
    </main>
  );
}

export default function App() {
  const { user, checking, signOut } = useAuth();
  const location = useLocation();
  if (checking) return <Loading label="Opening…" />;
  if (!user) return <Login />;
  return (
    <div className="t-shell">
      <a className="skip" href="#main">Skip to the main content</a>
      <header className="t-top">
        <img src="/logo.jpg" alt="" width="32" height="32" /><strong>HILYS</strong><span className="muted">Teachers</span>
        <div className="spacer" /><span className="t-name">{user.first_name}</span>
        <button className="btn btn-ghost btn-sm" onClick={signOut}>Sign out</button>
      </header>
      <main id="main" className="t-main" tabIndex={-1}>
        <ErrorBoundary resetKey={location.pathname}>
          <Routes>
            <Route path="/" element={<Week />} />
            <Route path="/students" element={<Students />} />
            <Route path="/pay" element={<Pay />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </main>
      <nav className="t-nav" aria-label="Main">
        <NavLink to="/" end>My lessons</NavLink><NavLink to="/students">My students</NavLink><NavLink to="/pay">My pay</NavLink>
      </nav>
    </div>
  );
}
