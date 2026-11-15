import { useState } from "react";
import { api } from "../api";
import { useData } from "../components/hooks";
import { useLookup } from "../components/lookups";
import { Dialog, Empty, ErrorState, Field, Loading, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { money } from "../format";
import "./Enrolments.css";

const STAGES = [["talking", "Talking"], ["trial", "Trial or pilot"], ["offer", "Offer sent"], ["won", "Won"], ["lost", "Lost"]];

function OppForm({ opp, onClose, onDone }) {
  const families = useLookup("families");
  const f = useForm(opp || { title: "", organisation: "", family: "", value: "", currency: "USD", expected_close: "", notes: "" });
  return (
    <Dialog title={opp ? "Edit opportunity" : "New opportunity"} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !f.values.title} onClick={() => f.submit(async (v) => onDone(opp ? await api(`/pipeline/${opp.id}/`, { method: "PATCH", body: { ...v, family: v.family || null, expected_close: v.expected_close || null } }) : await api("/pipeline/", { method: "POST", body: { ...v, family: v.family || null, expected_close: v.expected_close || null } })))}>Save</button></>}>
      <Field label="What is it?" id="title" error={f.errors.title}><input className="input" {...f.bind("title")} /></Field>
      <div className="form-grid">
        <Field label="Organisation" id="organisation" hint="An association or school not yet on record."><input className="input" {...f.bind("organisation")} /></Field>
        <Field label="Or a family" id="family"><select className="input" {...f.bind("family")}><option value="">None</option>{families.map((x) => <option key={x.id} value={x.id}>{x.parent_name}</option>)}</select></Field>
        <Field label="Value per month" id="value"><input className="input" type="number" min="0" {...f.bind("value")} /></Field>
        <Field label="Currency" id="currency"><select className="input" {...f.bind("currency")}><option>USD</option><option>GBP</option><option>ZAR</option></select></Field>
        <Field label="Expected to close" id="expected_close"><input className="input" type="date" {...f.bind("expected_close")} /></Field>
      </div>
      <Field label="Notes" id="notes"><textarea className="input" {...f.bind("notes")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function MoveOpp({ opp, to, onClose, onDone }) {
  const f = useForm({ lost_to: "", lost_reason: "" });
  return (
    <Dialog title={`Move to ${STAGES.find((s) => s[0] === to)[1]}`} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || (to === "lost" && (!f.values.lost_to || !f.values.lost_reason))} onClick={() => f.submit(async (v) => onDone(await api(`/pipeline/${opp.id}/move/`, { method: "POST", body: { stage: to, ...v } })))}>Move</button></>}>
      {to === "lost" ? <><Field label="Lost to whom or what?" id="lost_to"><input className="input" {...f.bind("lost_to")} /></Field><Field label="Why?" id="lost_reason" error={f.errors.lost_reason}><textarea className="input" {...f.bind("lost_reason")} /></Field></>
        : <p style={{ margin: 0 }}>{opp.title}</p>}
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Pipeline() {
  const toast = useToast();
  const [bump, setBump] = useState(0);
  const { data, loading, error, reload } = useData("/pipeline/?page_size=200", [bump]);
  const summary = useData("/pipeline/summary/", [bump]);
  const [edit, setEdit] = useState(null);
  const [move, setMove] = useState(null);
  const done = (msg) => { setEdit(null); setMove(null); setBump((n) => n + 1); toast(msg); };
  if (loading && !data) return <div className="page"><Loading /></div>;
  if (error) return <div className="page"><ErrorState error={error} onRetry={reload} /></div>;
  const rows = data.results;
  return (
    <div className="page">
      <div className="page-head"><div><h1>Pipeline</h1><p>Bigger deals: several children, associations, heritage schools.</p></div><div className="spacer" /><button className="btn btn-primary" onClick={() => setEdit({})}>New opportunity</button></div>
      {summary.data && Object.entries(summary.data).map(([c, s]) => <div key={c} className="row" style={{ marginBottom: 16, gap: 24 }}>
        <span><span className="muted">Open</span> <strong>{money(s.open_value, c)}</strong></span><span><span className="muted">Weighted</span> <strong>{money(s.weighted, c)}</strong></span>
        <span><span className="muted">Won this month</span> <strong>{money(s.won_this_month, c)}</strong></span><span><span className="muted">Lost this month</span> <strong>{money(s.lost_this_month, c)}</strong></span></div>)}
      {rows.length === 0 ? <Empty title="No opportunities yet" action={<button className="btn btn-primary btn-sm" onClick={() => setEdit({})}>New opportunity</button>}>Add talks with associations and heritage schools here.</Empty> : (
        <div className="board">{STAGES.map(([s, label]) => {
          const col = rows.filter((r) => r.stage === s);
          return <section key={s} className="board-col" aria-label={label}><h2>{label} <span className="muted">{col.length}</span></h2>
            {col.map((r) => <div key={r.id} className="board-card" style={{ cursor: "default" }}>
              <button className="link-btn" style={{ textAlign: "left", textDecoration: "none", color: "var(--ink)" }} onClick={() => setEdit(r)}><strong>{r.title}</strong></button>
              <span className="muted">{r.who}</span><span>{money(r.value, r.currency)} · {r.chance}%</span>
              {r.stage === "lost" && <span className="muted">Lost to {r.lost_to}: {r.lost_reason}</span>}
              {!["won", "lost"].includes(r.stage) && <label className="sr-only" htmlFor={`mv-${r.id}`}>Move {r.title}</label>}
              {!["won", "lost"].includes(r.stage) && <select id={`mv-${r.id}`} className="input" value="" onChange={(e) => e.target.value && setMove({ opp: r, to: e.target.value })}>
                <option value="">Move to…</option>{STAGES.filter(([k]) => k !== s).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>}
            </div>)}</section>;
        })}</div>)}
      {edit && <OppForm opp={edit.id ? edit : null} onClose={() => setEdit(null)} onDone={() => done("Saved")} />}
      {move && <MoveOpp opp={move.opp} to={move.to} onClose={() => setMove(null)} onDone={() => done("Moved")} />}
    </div>
  );
}
