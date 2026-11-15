import { useState } from "react";
import { useAuth } from "../auth";
import "./Login.css";

export default function Login() {
  const { signIn } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError("");
    try { await signIn(username, password); } catch (err) { setError(err.message); setBusy(false); }
  }
  return (
    <main className="login">
      <div className="login-art" aria-hidden="true">
        <img src="/logo.jpg" alt="" width="160" height="160" />
        <p className="login-nd">Salibonani!</p>
        <p className="login-en">Diversity is power</p>
      </div>
      <form className="login-card" onSubmit={submit}>
        <h1>HILYS staff</h1>
        <p className="muted">Sign in to run lessons, families and money.</p>
        <div className="field"><label htmlFor="username">Username</label>
          <input id="username" className="input" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required /></div>
        <div className="field"><label htmlFor="password">Password</label>
          <input id="password" className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
        {error && <div className="form-error" role="alert">{error}</div>}
        <button className="btn btn-primary" disabled={busy || !username || !password}>{busy ? "Signing in…" : "Sign in"}</button>
        <p className="muted small">Teachers use the teacher portal. Parents use the HILYS app.</p>
      </form>
    </main>
  );
}
