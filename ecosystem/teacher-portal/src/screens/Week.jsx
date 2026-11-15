import { useMemo, useState } from "react";
import { api, qs } from "../api";
import { useData } from "../components/hooks";
import { Dialog, Empty, ErrorState, Field, Loading, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { timeOnly, when } from "../format";

const STATUS = [["taught", "Taught"], ["moved", "Moved (24h notice)"], ["missed", "Missed: no notice (counts as used)"], ["cancelled", "I cancelled it"], ["cut_short", "Cut short by power or internet"]];

function Report({ lesson, onClose, onDone }) {
  const units = useData("/teacher/units/");
  const f = useForm({ status: "taught", unit: lesson.unit || lesson.next_unit?.id || "", parent_note: lesson.parent_note || "", private_note: lesson.private_note || "", trial_level: "" });
  const trial = lesson.kind === "trial";
  return (
    <Dialog title={`How did it go? ${lesson.who}`} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy} onClick={() => f.submit(async (v) => onDone(await api(`/teacher/lessons/${lesson.id}/report/`, { method: "POST", body: { ...v, unit: v.unit || null } })))}>{f.busy ? "Saving…" : "Save"}</button></>}>
      <fieldset className="status-pick"><legend>What happened?</legend>
        {STATUS.map(([v, l]) => <label key={v} className={f.values.status === v ? "on" : ""}><input type="radio" name="status" value={v} checked={f.values.status === v} onChange={f.set("status")} />{l}</label>)}</fieldset>
      {f.errors.status && <span className="error">{f.errors.status}</span>}
      {trial && f.values.status === "taught" && <Field label="Level you found" id="trial_level" error={f.errors.trial_level}><select className="input" {...f.bind("trial_level")}>
        <option value="">Choose…</option><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="conversation">Conversation</option></select></Field>}
      {!trial && f.values.status === "taught" && <Field label="Book lesson you taught" id="unit" hint={lesson.next_unit ? `Next for this child: ${lesson.next_unit.label}` : undefined}>
        <select className="input" {...f.bind("unit")}><option value="">None</option>{(units.data || []).map((u) => <option key={u.id} value={u.id}>{u.label}</option>)}</select></Field>}
      <Field label="Note for the parent" id="parent_note" hint="What the child learned or practised. The parent reads this in the app." error={f.errors.parent_note}><textarea className="input" {...f.bind("parent_note")} /></Field>
      <Field label="Private note (only HILYS sees it)" id="private_note"><textarea className="input" {...f.bind("private_note")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Week() {
  const toast = useToast();
  const [reporting, setReporting] = useState(null);
  const [bump, setBump] = useState(0);
  const from = new Date(); from.setDate(from.getDate() - 7);
  const to = new Date(); to.setDate(to.getDate() + 14);
  const { data, loading, error, reload } = useData(`/teacher/lessons/${qs({ from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) })}`, [bump]);
  const now = Date.now();
  const toReport = (data || []).filter((l) => l.status === "scheduled" && new Date(l.starts_at).getTime() < now);
  const days = useMemo(() => {
    const out = {};
    for (const l of data || []) {
      if (new Date(l.starts_at).getTime() < now - 86400000 && l.status !== "scheduled") continue; // older reported lessons stay out of the way
      const k = new Date(l.starts_at).toLocaleDateString("en-GB", { timeZone: "Africa/Harare", weekday: "long", day: "numeric", month: "long" });
      (out[k] = out[k] || []).push(l);
    }
    return Object.entries(out);
  }, [data, now]);
  if (loading && !data) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  return (
    <div>
      <h1>My lessons</h1>
      <p className="muted">Times are Harare time. The family's own time is shown under each lesson.</p>
      {toReport.length > 0 && <div className="t-alert" role="status">{toReport.length} past {toReport.length === 1 ? "lesson needs" : "lessons need"} a report. Lessons are paid once they are reported.</div>}
      {days.length === 0 && <Empty title="No lessons in the next two weeks">New students and trial lessons appear here when HILYS books them.</Empty>}
      {days.map(([day, rows]) => (
        <section key={day} aria-label={day}>
          <h2 className="t-day">{day}</h2>
          {rows.map((l) => {
            const past = new Date(l.starts_at).getTime() < now;
            const needs = l.status === "scheduled" && past;
            return (
              <article key={l.id} className={`t-lesson${needs ? " needs" : l.status !== "scheduled" ? " done" : ""}`}>
                <div className="row"><span className="t-time">{timeOnly(l.starts_at)}</span><strong>{l.who}</strong><div className="spacer" /><Pill status={l.status}>{l.status_label}</Pill></div>
                <span className="t-sub">{l.kind_label} · {l.minutes} min · family's time {when(l.starts_at, l.family_time_zone)} ({l.family_time_zone})</span>
                {l.next_unit && l.status === "scheduled" && <span className="t-sub">Next in the book: {l.next_unit.label}</span>}
                {l.support_notes && <div className="t-support"><strong>Please note:</strong> {l.support_notes}</div>}
                {l.parent_note && l.status !== "scheduled" && <span className="t-sub">Parent note: {l.parent_note}</span>}
                {l.makeup_owed && <Pill tone="warn">Make-up owed: HILYS will book it</Pill>}
                {(past || l.status !== "scheduled") && <button className={`btn btn-sm ${needs ? "btn-primary" : "btn-ghost"}`} style={{ justifySelf: "start" }} onClick={() => setReporting(l)}>{needs ? "Report this lesson" : "Change report"}</button>}
              </article>
            );
          })}
        </section>
      ))}
      {reporting && <Report lesson={reporting} onClose={() => setReporting(null)} onDone={() => { setReporting(null); setBump((n) => n + 1); toast("Thank you. Report saved."); }} />}
    </div>
  );
}
