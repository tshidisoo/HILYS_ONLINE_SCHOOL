import { createContext, useContext, useEffect, useRef, useState } from "react";
import "./ui.css";

const TONES = {
  // One meaning per colour across the whole app.
  good: ["paid", "taught", "active", "won", "done", "answered", "on_time", "accepted", "approved", "certificate", "converted"],
  warn: ["part_paid", "due_soon", "waiting", "paused", "trial", "trial_booked", "trial_done", "missed", "cut_short", "doing", "practice", "offer", "draft", "in_progress", "received"],
  bad: ["late", "overdue", "cancelled", "stopped", "lost", "repeat", "refused"],
  info: ["issued", "new", "scheduled", "contacted", "open", "talking", "moved", "finished"],
};
export function toneFor(status) {
  for (const [tone, list] of Object.entries(TONES)) if (list.includes(status)) return tone;
  return "neutral";
}
export function Pill({ status, children, tone }) {
  return <span className={`pill tone-${tone || toneFor(status)}`}>{children}</span>;
}

export function Loading({ label = "Loading…" }) {
  return <div className="state" role="status"><span className="spinner" aria-hidden="true" />{label}</div>;
}
export function ErrorState({ error, onRetry }) {
  return (
    <div className="state state-error" role="alert">
      <strong>We could not load this.</strong>
      <span>{error?.message}</span>
      {onRetry && <button className="btn btn-ghost btn-sm" onClick={onRetry}>Try again</button>}
    </div>
  );
}
export function Empty({ title, children, action }) {
  return (
    <div className="state state-empty">
      <strong>{title}</strong>
      {children && <span>{children}</span>}
      {action}
    </div>
  );
}

// Toasts
const ToastCtx = createContext(() => {});
export function ToastProvider({ children }) {
  const [msg, setMsg] = useState("");
  useEffect(() => { if (!msg) return; const t = setTimeout(() => setMsg(""), 3200); return () => clearTimeout(t); }, [msg]);
  return <ToastCtx.Provider value={setMsg}>{children}{msg && <div className="toast" role="status">{msg}</div>}</ToastCtx.Provider>;
}
export const useToast = () => useContext(ToastCtx);

// Modal dialog with focus kept inside; Escape closes.
export function Dialog({ title, onClose, children, footer, wide }) {
  const ref = useRef(null);
  useEffect(() => {
    const prev = document.activeElement;
    ref.current?.querySelector("input, select, textarea, button")?.focus();
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); prev?.focus?.(); };
  }, [onClose]);
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`dialog${wide ? " dialog-wide" : ""}`} role="dialog" aria-modal="true" aria-labelledby="dialog-title" ref={ref}>
        <div className="dialog-head"><h2 id="dialog-title">{title}</h2><button className="icon-btn" onClick={onClose} aria-label="Close">×</button></div>
        <div className="dialog-body">{children}</div>
        {footer && <div className="dialog-foot">{footer}</div>}
      </div>
    </div>
  );
}

export function Confirm({ title, message, confirmLabel = "Yes, go ahead", danger, onConfirm, onClose, needReason }) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function go() {
    setBusy(true); setError("");
    try { await onConfirm(reason); onClose(); } catch (e) { setError(e.message); setBusy(false); }
  }
  return (
    <Dialog title={title} onClose={onClose} footer={<>
      <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className={`btn ${danger ? "btn-danger" : "btn-primary"}`} disabled={busy || (needReason && !reason.trim())} onClick={go}>{busy ? "Working…" : confirmLabel}</button>
    </>}>
      <p style={{ marginTop: 0 }}>{message}</p>
      {needReason && <Field label={needReason} id="confirm-reason"><textarea id="confirm-reason" className="input" value={reason} onChange={(e) => setReason(e.target.value)} /></Field>}
      {error && <div className="form-error" role="alert">{error}</div>}
    </Dialog>
  );
}

export function Field({ label, id, hint, error, children, wide }) {
  return (
    <div className={`field${wide ? " wide" : ""}`}>
      <label htmlFor={id}>{label}</label>
      {children}
      {hint && !error && <span className="hint" id={`${id}-hint`}>{hint}</span>}
      {error && <span className="error" id={`${id}-error`} role="alert">{error}</span>}
    </div>
  );
}

// Side panel for a record's detail, with tabs.
export function Panel({ title, subtitle, onClose, tabs, tab, setTab, actions, children }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="overlay overlay-panel" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="panel" role="dialog" aria-modal="true" aria-labelledby="panel-title">
        <div className="panel-head">
          <div><h2 id="panel-title">{title}</h2>{subtitle && <div className="muted">{subtitle}</div>}</div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">×</button>
        </div>
        {actions && <div className="panel-actions">{actions}</div>}
        {tabs && (
          <div className="tabs" role="tablist">
            {tabs.map((t) => (
              <button key={t} role="tab" aria-selected={tab === t} className={`tab${tab === t ? " on" : ""}`} onClick={() => setTab(t)}>{t}</button>
            ))}
          </div>
        )}
        <div className="panel-body">{children}</div>
      </aside>
    </div>
  );
}

export function Stat({ label, value, tone }) {
  return <div className={`stat${tone ? " stat-" + tone : ""}`}><span className="stat-value">{value}</span><span className="stat-label">{label}</span></div>;
}

export function DL({ rows }) {
  return <dl className="dl">{rows.filter(Boolean).map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v ?? "—"}</dd></div>)}</dl>;
}
