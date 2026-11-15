import { useMemo, useState } from "react";
import { api, qs } from "../api";
import { useData, useOpenParam, useRecord } from "../components/hooks";
import { useLookup } from "../components/lookups";
import { DL, Dialog, Empty, ErrorState, Field, Loading, Panel, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { when } from "../format";
import "./Lessons.css";

const STATUS = [["taught", "Taught"], ["moved", "Moved (24h notice)"], ["missed", "Missed (counts as used)"], ["cancelled", "Cancelled by HILYS"], ["cut_short", "Cut short (power or internet)"]];

function mondayOf(d) { const x = new Date(d); x.setHours(12, 0, 0, 0); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x; }
function iso(d) { return d.toISOString().slice(0, 10); }

export function ReportDialog({ lesson, onClose, onDone, endpoint }) {
  const units = useData(lesson.enrolment || lesson.kind === "trial" ? "/books/" : null);
  const f = useForm({ status: "taught", parent_note: lesson.parent_note || "", private_note: lesson.private_note || "", unit: lesson.unit || lesson.next_unit?.id || "", trial_level: lesson.trial_level || "" });
  const save = () => f.submit(async (v) => onDone(await api(endpoint || `/lessons/${lesson.id}/report/`, { method: "POST", body: { ...v, unit: v.unit || null } })));
  const allUnits = (units.data || []).flatMap((b) => b.units.map((u) => ({ ...u, book_title: b.title })));
  return (
    <Dialog title={`What happened: ${lesson.who}`} wide onClose={onClose}
            footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy} onClick={save}>{f.busy ? "Saving…" : "Save report"}</button></>}>
      <fieldset className="status-pick"><legend>What happened?</legend>
        {STATUS.map(([v, l]) => <label key={v} className={f.values.status === v ? "on" : ""}><input type="radio" name="status" value={v} checked={f.values.status === v} onChange={f.set("status")} />{l}</label>)}
      </fieldset>
      {f.errors.status && <div className="error">{f.errors.status}</div>}
      {lesson.kind === "trial" && f.values.status === "taught" && <Field label="Level you found" id="trial_level" error={f.errors.trial_level}>
        <select className="input" {...f.bind("trial_level")}><option value="">Choose…</option><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="conversation">Conversation</option></select></Field>}
      {lesson.kind !== "trial" && <Field label="Book lesson taught" id="unit" hint={lesson.next_unit ? `Next in the book: ${lesson.next_unit.label}` : undefined}>
        <select className="input" {...f.bind("unit")}><option value="">None</option>{allUnits.map((u) => <option key={u.id} value={u.id}>{u.book_title} · {u.number}: {u.title_nd} ({u.title_en})</option>)}</select></Field>}
      <Field label="Note for the parent" id="parent_note" hint="What the child learned or practised. The family sees this in the app." error={f.errors.parent_note}><textarea className="input" {...f.bind("parent_note")} /></Field>
      <Field label="Private note" id="private_note" hint="Only HILYS staff and the teacher see this."><textarea className="input" {...f.bind("private_note")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function MoveDialog({ lesson, action, onClose, onDone }) {
  const f = useForm({ day: "", time: "17:00" });
  const save = () => f.submit(async (v) => onDone(await api(`/lessons/${lesson.id}/${action}/`, { method: "POST", body: { starts_at: new Date(`${v.day}T${v.time}:00+02:00`).toISOString() } })));
  return (
    <Dialog title={action === "makeup" ? "Book the make-up lesson" : "Move this lesson"} onClose={onClose}
            footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || !f.values.day} onClick={save}>Save</button></>}>
      <div className="form-grid"><Field label="Day" id="day"><input className="input" type="date" {...f.bind("day")} /></Field>
        <Field label="Time in Harare" id="time" hint={`The family is in ${lesson.family_time_zone}.`}><input className="input" type="time" {...f.bind("time")} /></Field></div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function LessonPanel({ id, onClose, onChanged }) {
  const toast = useToast();
  const { data: l, setData, error, reload } = useRecord(`/lessons/${id}/`);
  const [dialog, setDialog] = useState(null);
  if (error) return <Panel title="Lesson" onClose={onClose}><ErrorState error={error} onRetry={reload} /></Panel>;
  if (!l) return <Panel title="Lesson" onClose={onClose}><Loading /></Panel>;
  const done = (r, msg) => { setData(r.id === l.id ? r : l); reload(); setDialog(null); onChanged(); toast(msg); };
  const past = new Date(l.starts_at) < new Date();
  return (
    <Panel title={l.who} subtitle={`${l.kind_label} · ${l.teacher_name}`} onClose={onClose}
      actions={<>
        {l.status === "scheduled" && past && <button className="btn btn-primary btn-sm" onClick={() => setDialog("report")}>Report the lesson</button>}
        {l.status === "scheduled" && <button className="btn btn-ghost btn-sm" onClick={() => setDialog("move_time")}>Move time</button>}
        {l.status !== "scheduled" && <button className="btn btn-ghost btn-sm" onClick={() => setDialog("report")}>Change report</button>}
        {l.makeup_owed && <button className="btn btn-primary btn-sm" onClick={() => setDialog("makeup")}>Book make-up</button>}
      </>}>
      <div className="row"><Pill status={l.status}>{l.status_label}</Pill>{l.makeup_owed && <Pill tone="warn">Make-up owed</Pill>}{l.is_group && <Pill tone="neutral">Group</Pill>}</div>
      <DL rows={[["Harare time", when(l.starts_at)], [`Family's time (${l.family_time_zone})`, l.family_time_zone && when(l.starts_at, l.family_time_zone)],
        ["Length", `${l.minutes} minutes`], ["Family", l.family_name], ["Book lesson", l.unit_label], ["Level found (trial)", l.trial_level],
        ["Note for the parent", l.parent_note], ["Private note", l.private_note], ["Reported", l.reported_at ? when(l.reported_at) : "Not yet"]]} />
      {dialog === "report" && <ReportDialog lesson={l} onClose={() => setDialog(null)} onDone={(r) => done(r, "Lesson reported")} />}
      {(dialog === "makeup" || dialog === "move_time") && <MoveDialog lesson={l} action={dialog} onClose={() => setDialog(null)} onDone={(r) => done(r, dialog === "makeup" ? "Make-up booked" : "Lesson moved")} />}
    </Panel>
  );
}

export default function Lessons() {
  const params = new URLSearchParams(window.location.search);
  const [open, setOpen] = useState(useOpenParam());
  const [week, setWeek] = useState(() => mondayOf(new Date()));
  const [teacher, setTeacher] = useState("");
  const [mode, setMode] = useState(params.get("unreported") ? "unreported" : params.get("makeup_owed") ? "makeup" : "week");
  const [reload, setReload] = useState(0);
  const teachers = useLookup("teachers");
  const end = new Date(week); end.setDate(end.getDate() + 7);
  const path = mode === "week" ? `/lessons/${qs({ from: iso(week), to: iso(end), teacher, page_size: 200, ordering: "starts_at" })}`
    : mode === "unreported" ? `/lessons/${qs({ unreported: 1, teacher, page_size: 200 })}` : `/lessons/${qs({ makeup_owed: "true", teacher, page_size: 200 })}`;
  const { data, loading, error, reload: refetch } = useData(path, [reload]);
  const days = useMemo(() => {
    const out = [...Array(7)].map((_, i) => { const d = new Date(week); d.setDate(d.getDate() + i); return { key: iso(d), d, rows: [] }; });
    for (const l of data?.results || []) {
      const k = new Date(l.starts_at).toLocaleDateString("en-CA", { timeZone: "Africa/Harare" });
      out.find((x) => x.key === k)?.rows.push(l);
    }
    return out;
  }, [data, week]);
  const shift = (n) => { const d = new Date(week); d.setDate(d.getDate() + 7 * n); setWeek(d); };
  const rows = data?.results || [];
  return (
    <div className="page">
      <div className="page-head"><div><h1>Timetable</h1><p>All times in Harare time. Each lesson also shows the family's own time.</p></div></div>
      <div className="dt-tools" style={{ marginBottom: 16 }}>
        <div className="seg" role="group" aria-label="Show">
          {[["week", "Week"], ["unreported", "Not reported"], ["makeup", "Make-ups owed"]].map(([k, l]) => <button key={k} className={mode === k ? "on" : ""} aria-pressed={mode === k} onClick={() => setMode(k)}>{l}</button>)}
        </div>
        <label htmlFor="t-filter" className="sr-only">Teacher</label>
        <select id="t-filter" className="input" style={{ maxWidth: 220 }} value={teacher} onChange={(e) => setTeacher(e.target.value)}><option value="">All teachers</option>{teachers.map((t) => <option key={t.id} value={t.id}>{t.display_name}</option>)}</select>
        {mode === "week" && <div className="row"><button className="btn btn-ghost btn-sm" onClick={() => shift(-1)}>← Previous</button>
          <strong>{week.toLocaleDateString("en-GB", { day: "numeric", month: "short" })} – {new Date(end - 86400000).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</strong>
          <button className="btn btn-ghost btn-sm" onClick={() => shift(1)}>Next →</button><button className="link-btn" onClick={() => setWeek(mondayOf(new Date()))}>This week</button></div>}
      </div>
      {error ? <ErrorState error={error} onRetry={refetch} /> : loading && !data ? <Loading /> : mode === "week" ? (
        <div className="week">
          {days.map((day) => (
            <section key={day.key} className={`day${day.key === new Date().toLocaleDateString("en-CA", { timeZone: "Africa/Harare" }) ? " today" : ""}`} aria-label={day.d.toDateString()}>
              <h2>{day.d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric" })}</h2>
              {day.rows.length === 0 && <p className="muted day-empty">No lessons</p>}
              {day.rows.map((l) => (
                <button key={l.id} className={`lesson-chip st-${l.status}${l.kind !== "regular" ? " k-" + l.kind : ""}`} onClick={() => setOpen(l.id)}>
                  <span className="chip-time">{new Date(l.starts_at).toLocaleTimeString("en-GB", { timeZone: "Africa/Harare", hour: "2-digit", minute: "2-digit" })}</span>
                  <span className="chip-who">{l.who}</span><span className="chip-sub">{l.teacher_name.split(" ")[0]} · {l.status_label}</span>
                </button>
              ))}
            </section>
          ))}
        </div>
      ) : rows.length === 0 ? <Empty title={mode === "unreported" ? "Every past lesson is reported" : "No make-ups owed"}>Ngiyabonga, teachers.</Empty> : (
        <div className="stack">{rows.map((l) => (
          <button key={l.id} className="lesson-row" onClick={() => setOpen(l.id)}><span>{when(l.starts_at)}</span><strong>{l.who}</strong><span className="muted">{l.teacher_name}</span><Pill status={l.status}>{l.status_label}</Pill></button>
        ))}</div>
      )}
      {open && <LessonPanel id={open} onClose={() => setOpen(null)} onChanged={() => setReload((n) => n + 1)} />}
    </div>
  );
}
