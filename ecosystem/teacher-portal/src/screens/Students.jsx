import { useState } from "react";
import { api } from "../api";
import { useData } from "../components/hooks";
import { Dialog, Empty, ErrorState, Loading, Pill, useToast } from "../components/ui";
import { WEEKDAYS } from "../format";

const PARTS = ["Says the 5 vowels", "Reads syllables", "Makes the 3 clicks", "Reads 8 words", "Reads 3 sentences", "Talks a little"];

function Progress({ s, onClose }) {
  const { data, loading, error } = useData(`/teacher/students/${s.student}/progress/`);
  return (
    <Dialog title={`${s.name}: ${s.book}`} onClose={onClose}>
      {loading && <Loading />}{error && <ErrorState error={error} />}
      {data && <>
        <strong>{data.done} of {data.total} lessons done</strong>
        <div className="bar"><span style={{ width: `${(100 * data.done) / data.total}%` }} /></div>
        <ol style={{ paddingLeft: 22, margin: 0 }}>{data.units.map((u) => <li key={u.number} style={{ color: u.done ? "var(--good)" : undefined }}>{u.done ? "✓ " : ""}{u.title_nd} <span className="muted">({u.title_en})</span></li>)}</ol>
        {data.checks.length > 0 && <p className="muted">End-of-book checks: {data.checks.map((c) => `${c.checked_on}: ${c.score}/6, ${c.result}`).join("; ")}</p>}
      </>}
    </Dialog>
  );
}

function Check({ s, onClose, onDone }) {
  const [parts, setParts] = useState([false, false, false, false, false, false]);
  const [notes, setNotes] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const score = parts.filter(Boolean).length;
  return (
    <Dialog title={`End-of-book check: ${s.name}`} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={busy} onClick={async () => { setBusy(true); setErr(""); try { onDone(await api("/teacher/book-check/", { method: "POST", body: { student: s.student, book: s.book_id, parts, practice_notes: notes } })); } catch (e) { setErr(e.message); setBusy(false); } }}>Save check</button></>}>
      <p className="muted" style={{ margin: 0 }}>Tick each part the child did with little or no help. Praise every try.</p>
      <fieldset className="parts"><legend className="sr-only">Parts</legend>{PARTS.map((p, i) => <label key={p} className={parts[i] ? "on" : ""}><input type="checkbox" checked={parts[i]} onChange={() => setParts(parts.map((x, j) => (j === i ? !x : x)))} />{i + 1}. {p}</label>)}</fieldset>
      <strong>{score} of 6 · {score >= 5 ? "Certificate" : score >= 3 ? "Certificate, with things to practise" : "Not yet: repeat lessons and try again"}</strong>
      <div className="field"><label htmlFor="notes">Things to practise</label><textarea id="notes" className="input" value={notes} onChange={(e) => setNotes(e.target.value)} /></div>
      {err && <div className="form-error" role="alert">{err}</div>}
    </Dialog>
  );
}

export default function Students() {
  const toast = useToast();
  const [bump, setBump] = useState(0);
  const { data, loading, error, reload } = useData("/teacher/students/", [bump]);
  const [view, setView] = useState(null);
  const [check, setCheck] = useState(null);
  if (loading && !data) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  return (
    <div>
      <h1>My students</h1>
      <p className="muted">Only the children you teach.</p>
      {data.length === 0 && <Empty title="No students yet">HILYS adds children here when they enrol with you.</Empty>}
      {data.map((s) => (
        <article key={s.enrolment} className="t-lesson">
          <div className="row"><strong style={{ fontSize: 17 }}>{s.name}</strong>{s.group_name && <Pill tone="neutral">{s.group_name}</Pill>}<div className="spacer" /><Pill status={s.stage === "Active" ? "active" : s.stage === "Paused" ? "paused" : "waiting"}>{s.stage}</Pill></div>
          <span className="t-sub">{s.level} · {s.package} · {s.weekly_slots.map((x) => `${WEEKDAYS[x.weekday]} ${x.time}`).join(", ") || "No weekly times yet"}</span>
          {s.progress && <><span className="t-sub">{s.book}: {s.progress.done} of {s.progress.total} lessons</span><div className="bar"><span style={{ width: `${(100 * s.progress.done) / s.progress.total}%` }} /></div></>}
          <div className="row">{s.book && <button className="btn btn-ghost btn-sm" onClick={() => setView(s)}>Book progress</button>}
            {s.progress && s.progress.done >= s.progress.total - 1 && <button className="btn btn-primary btn-sm" onClick={() => setCheck(s)}>End-of-book check</button>}</div>
        </article>
      ))}
      {view && <Progress s={view} onClose={() => setView(null)} />}
      {check && <Check s={check} onClose={() => setCheck(null)} onDone={(r) => { setCheck(null); setBump((n) => n + 1); toast(r.certificate ? `Sizwe! Certificate ${r.certificate} made.` : "Check saved."); }} />}
    </div>
  );
}
