import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import DataTable from "../components/DataTable";
import { useData, useOpenParam, useRecord } from "../components/hooks";
import { useLookup } from "../components/lookups";
import { DL, Dialog, Empty, ErrorState, Field, Loading, Panel, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { WEEKDAYS, date } from "../format";
import "./Enrolments.css";

const STAGES = [["trial", "Trial"], ["waiting", "Waiting to start"], ["active", "Active"], ["paused", "Paused"], ["finished", "Finished"], ["stopped", "Stopped"]];
const LABEL = Object.fromEntries(STAGES);

function SlotsEditor({ value, onChange }) {
  const slots = value || [];
  const update = (i, k, v) => onChange(slots.map((s, j) => (j === i ? { ...s, [k]: k === "weekday" ? Number(v) : v } : s)));
  return (
    <div className="slots">
      {slots.map((s, i) => (
        <div key={i} className="slot">
          <label className="sr-only" htmlFor={`slot-d-${i}`}>Day</label>
          <select id={`slot-d-${i}`} className="input" value={s.weekday} onChange={(e) => update(i, "weekday", e.target.value)}>{WEEKDAYS.map((d, n) => <option key={d} value={n}>{d}</option>)}</select>
          <label className="sr-only" htmlFor={`slot-t-${i}`}>Time in Harare</label>
          <input id={`slot-t-${i}`} className="input" type="time" value={s.time} onChange={(e) => update(i, "time", e.target.value)} />
          <button type="button" className="icon-btn" aria-label="Remove this time" onClick={() => onChange(slots.filter((_, j) => j !== i))}>×</button>
        </div>
      ))}
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange([...slots, { weekday: 1, time: "17:30" }])}>Add a weekly time</button>
    </div>
  );
}

function EnrolmentForm({ enrolment, studentId, onClose, onDone }) {
  const teachers = useLookup("teachers");
  const packages = useLookup("packages").filter((p) => p.kind === "package");
  const books = useLookup("books");
  const students = useData(enrolment ? null : "/students/?page_size=200");
  const f = useForm(enrolment ? { ...enrolment } : { student: studentId || "", teacher: "", package: "", book: "", level: "beginner", group_name: "", weekly_slots: [], start_date: "", notes: "" });
  const save = () => f.submit(async (v) => {
    const body = { ...v, teacher: v.teacher || null, package: v.package || null, book: v.book || null, start_date: v.start_date || null };
    for (const k of ["history", "next_gates", "stage", "stage_label"]) delete body[k];
    onDone(enrolment ? await api(`/enrolments/${enrolment.id}/`, { method: "PATCH", body }) : await api("/enrolments/", { method: "POST", body }));
  });
  return (
    <Dialog title={enrolment ? `Edit ${enrolment.student_name}'s enrolment` : "Enrol a child"} wide onClose={onClose}
            footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || !f.values.student} onClick={save}>{f.busy ? "Saving…" : "Save"}</button></>}>
      <div className="form-grid">
        {!enrolment && <Field label="Child" id="student" error={f.errors.student}><select className="input" {...f.bind("student")}><option value="">Choose…</option>{(students.data?.results || []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></Field>}
        <Field label="Teacher" id="teacher"><select className="input" {...f.bind("teacher")}><option value="">Not chosen yet</option>{teachers.map((t) => <option key={t.id} value={t.id}>{t.display_name}</option>)}</select></Field>
        <Field label="Package" id="package" hint="From the price book."><select className="input" {...f.bind("package")}><option value="">Not chosen yet</option>{packages.map((p) => <option key={p.id} value={p.id}>{p.name} · {p.currency} {p.price}</option>)}</select></Field>
        <Field label="Level" id="level"><select className="input" {...f.bind("level")}><option value="">Not checked yet</option><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="conversation">Conversation</option></select></Field>
        <Field label="Book" id="book"><select className="input" {...f.bind("book")}><option value="">None</option>{books.map((b) => <option key={b.id} value={b.id}>{b.title}{b.is_ready ? "" : " (not ready yet)"}</option>)}</select></Field>
        <Field label="Group name" id="group_name" hint="Children in the same group lesson share this name."><input className="input" {...f.bind("group_name")} /></Field>
        <Field label="Starts on" id="start_date"><input className="input" type="date" {...f.bind("start_date")} /></Field>
        <Field label="Weekly lesson times (Harare time)" id="weekly_slots" wide error={f.errors.weekly_slots}><SlotsEditor value={f.values.weekly_slots} onChange={f.set("weekly_slots")} /></Field>
        <Field label="Notes" id="notes" wide><textarea className="input" {...f.bind("notes")} /></Field>
      </div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function MoveDialog({ e, to, onClose, onDone }) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const blocked = e.next_gates[to] || [];
  const needsReason = ["paused", "stopped"].includes(to);
  async function go() {
    setBusy(true); setError("");
    try { onDone(await api(`/enrolments/${e.id}/move/`, { method: "POST", body: { stage: to, reason } })); }
    catch (err) { setError(err.message); setBusy(false); }
  }
  return (
    <Dialog title={`Move to ${LABEL[to]}`} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={busy || blocked.length > 0 || (needsReason && !reason.trim())} onClick={go}>Move</button></>}>
      {blocked.length > 0 ? <div className="gate-list"><strong>Not yet. First:</strong><ul>{blocked.map((b) => <li key={b}>{b}</li>)}</ul></div>
        : <p style={{ margin: 0 }}>{to === "active" ? "Lessons for this month are added to the timetable." : "Ready to move."}</p>}
      {needsReason && <Field label="Why?" id="reason"><textarea id="reason" className="input" value={reason} onChange={(ev) => setReason(ev.target.value)} /></Field>}
      {error && <div className="form-error" role="alert">{error}</div>}
    </Dialog>
  );
}

function EnrolmentPanel({ id, onClose, onChanged }) {
  const toast = useToast();
  const navigate = useNavigate();
  const { data: e, setData, reload, error } = useRecord(`/enrolments/${id}/`);
  const [dialog, setDialog] = useState(null);
  const [tab, setTab] = useState("Details");
  const progress = useData(e?.book && tab === "Progress" ? `/books/${e.book}/progress/?student=${e.student}` : null);
  const lessons = useData(tab === "Lessons" ? `/lessons/?enrolment=${id}&ordering=-starts_at&page_size=40` : null);
  if (error) return <Panel title="Enrolment" onClose={onClose}><ErrorState error={error} onRetry={reload} /></Panel>;
  if (!e) return <Panel title="Enrolment" onClose={onClose}><Loading /></Panel>;
  return (
    <Panel title={e.student_name} subtitle={`${e.family_name} family`} onClose={onClose} tabs={["Details", "Progress", "Lessons", "History"]} tab={tab} setTab={setTab}
      actions={<>
        {Object.keys(e.next_gates).map((to) => <button key={to} className={`btn btn-sm ${e.next_gates[to].length ? "btn-ghost" : "btn-primary"}`} onClick={() => setDialog(to)}>{`Move to ${LABEL[to]}`}{e.next_gates[to].length ? " ⚠" : ""}</button>)}
        <button className="btn btn-ghost btn-sm" onClick={() => setDialog("edit")}>Edit</button>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/families?open=${e.family}`)}>Family</button>
      </>}>
      <div className="row"><Pill status={e.stage}>{e.stage_label}</Pill>{e.group_name && <Pill tone="neutral">{e.group_name}</Pill>}</div>
      {tab === "Details" && <DL rows={[["Teacher", e.teacher_name], ["Package", e.package_name], ["Level", e.level], ["Book", e.book_title],
        ["Weekly times (Harare)", e.weekly_slots.map((s) => `${WEEKDAYS[s.weekday]} ${s.time}`).join(", ") || "None yet"], ["Started", date(e.start_date)], ["Notes", e.notes]]} />}
      {tab === "Progress" && (!e.book ? <Empty title="No book chosen">Choose a book to follow progress.</Empty> : progress.loading ? <Loading /> : progress.data && <>
        <div className="progress-head"><strong>{progress.data.done} of {progress.data.total} lessons done</strong>
          <div className="bar" role="progressbar" aria-valuenow={progress.data.done} aria-valuemin={0} aria-valuemax={progress.data.total}><span style={{ width: `${(100 * progress.data.done) / progress.data.total}%` }} /></div></div>
        <ol className="units">{progress.data.units.map((u) => <li key={u.number} className={u.done ? "done" : ""}><span>{u.number}</span>{u.title_nd} <span className="muted">· {u.title_en}</span></li>)}</ol>
      </>)}
      {tab === "Lessons" && <div className="stack">{(lessons.data?.results || []).map((l) => <button key={l.id} className="money-line" onClick={() => navigate(`/lessons?open=${l.id}`)}>
        <span>{new Date(l.starts_at).toLocaleString("en-GB", { timeZone: "Africa/Harare", dateStyle: "medium", timeStyle: "short" })}</span><span className="muted">{l.unit_label}</span><span /><Pill status={l.status}>{l.status_label}</Pill></button>)}
        {lessons.data?.results?.length === 0 && <Empty title="No lessons yet">Lessons appear when the enrolment becomes Active.</Empty>}</div>}
      {tab === "History" && <ol className="timeline">{e.history.map((h, i) => <li key={i}><span className="muted">{date(h.at)} · {h.by_name}</span><strong>{LABEL[h.from_stage] || "Start"} → {LABEL[h.to_stage]}</strong>{h.reason && <span>{h.reason}</span>}</li>)}</ol>}
      {dialog === "edit" && <EnrolmentForm enrolment={e} onClose={() => setDialog(null)} onDone={(r) => { setData(r); setDialog(null); onChanged(); toast("Saved"); }} />}
      {dialog && dialog !== "edit" && <MoveDialog e={e} to={dialog} onClose={() => setDialog(null)} onDone={(r) => { setData(r); setDialog(null); onChanged(); toast(`Moved to ${LABEL[r.stage]}`); }} />}
    </Panel>
  );
}

function Board({ reloadKey, onOpen }) {
  const { data, loading, error, reload } = useData(`/enrolments/?page_size=200`, [reloadKey]);
  if (loading && !data) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  const rows = data.results;
  return (
    <div className="board">
      {STAGES.filter(([s]) => s !== "stopped").map(([s, label]) => {
        const col = rows.filter((r) => r.stage === s);
        return (
          <section key={s} className="board-col" aria-label={label}>
            <h2>{label} <span className="muted">{col.length}</span></h2>
            {col.length === 0 && <p className="muted board-empty">None</p>}
            {col.map((r) => {
              const next = Object.values(r.next_gates)[0] || [];
              return (
                <button key={r.id} className="board-card" onClick={() => onOpen(r.id)}>
                  <strong>{r.student_name}</strong><span className="muted">{r.package_name || "No package"}</span>
                  <span className="muted">{r.teacher_name || "No teacher"}</span>
                  {["trial", "waiting"].includes(s) && next.length > 0 && <span className="board-gate">Next: {next[0]}</span>}
                </button>
              );
            })}
          </section>
        );
      })}
    </div>
  );
}

export default function Enrolments() {
  const params = new URLSearchParams(window.location.search);
  const [open, setOpen] = useState(useOpenParam());
  const [view, setView] = useState(params.get("stage") ? "list" : "board");
  const [adding, setAdding] = useState(params.get("new") ? { student: params.get("student") } : null);
  const [reload, setReload] = useState(0);
  const bump = () => setReload((n) => n + 1);
  return (
    <div className="page">
      <div className="page-head"><div><h1>Enrolments</h1><p>Each child's journey from the free trial to finishing a book.</p></div><div className="spacer" />
        <div className="seg" role="group" aria-label="View"><button className={view === "board" ? "on" : ""} aria-pressed={view === "board"} onClick={() => setView("board")}>Board</button><button className={view === "list" ? "on" : ""} aria-pressed={view === "list"} onClick={() => setView("list")}>List</button></div>
        <button className="btn btn-primary" onClick={() => setAdding({})}>Enrol a child</button></div>
      {view === "board" ? <Board reloadKey={reload} onOpen={setOpen} /> : (
        <DataTable path="/enrolments/" reloadKey={reload} onOpen={(r) => setOpen(r.id)} initial={{ stage: params.get("stage") || "" }} searchLabel="Search children or families"
          filters={[{ key: "stage", label: "Stage", options: STAGES }, { key: "level", label: "Level", options: [["beginner", "Beginner"], ["intermediate", "Intermediate"], ["conversation", "Conversation"]] }]}
          columns={[
            { key: "student_name", label: "Child", render: (r) => <><div className="cell-main">{r.student_name}</div><div className="cell-sub">{r.family_name}</div></> },
            { key: "stage", label: "Stage", sort: "stage", render: (r) => <Pill status={r.stage}>{r.stage_label}</Pill> },
            { key: "teacher_name", label: "Teacher" }, { key: "package_name", label: "Package" },
            { key: "slots", label: "Weekly times", render: (r) => r.weekly_slots.map((s) => `${WEEKDAYS[s.weekday].slice(0, 3)} ${s.time}`).join(", ") || "—" },
          ]} />)}
      {open && <EnrolmentPanel id={open} onClose={() => setOpen(null)} onChanged={bump} />}
      {adding && <EnrolmentForm studentId={adding.student} onClose={() => setAdding(null)} onDone={(r) => { setAdding(null); bump(); setOpen(r.id); }} />}
    </div>
  );
}
