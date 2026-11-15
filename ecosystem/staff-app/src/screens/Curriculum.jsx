import { useState } from "react";
import { api, openPdf } from "../api";
import DataTable from "../components/DataTable";
import { useData } from "../components/hooks";
import { Dialog, Empty, ErrorState, Field, Loading, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { date } from "../format";
import "./Curriculum.css";

const PARTS = ["Says the 5 vowels", "Reads syllables", "Makes the 3 clicks", "Reads 8 words", "Reads 3 sentences", "Talks a little"];

function CheckForm({ books, onClose, onDone }) {
  const students = useData("/students/?page_size=200");
  const f = useForm({ student: "", book: books[0]?.id || "", parts: [false, false, false, false, false, false], practice_notes: "", checked_on: new Date().toISOString().slice(0, 10) });
  const score = f.values.parts.filter(Boolean).length;
  const result = score >= 5 ? ["good", "Certificate"] : score >= 3 ? ["warn", "Certificate, with things to practise"] : ["bad", "Not yet: repeat lessons and try again"];
  const toggle = (i) => f.setValues((v) => ({ ...v, parts: v.parts.map((p, j) => (j === i ? !p : p)) }));
  return (
    <Dialog title="End-of-book check" wide onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !f.values.student} onClick={() => f.submit(async (v) => onDone(await api("/book-checks/", { method: "POST", body: v })))}>Save check</button></>}>
      <div className="form-grid">
        <Field label="Child" id="student" error={f.errors.student}><select className="input" {...f.bind("student")}><option value="">Choose…</option>{(students.data?.results || []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></Field>
        <Field label="Book" id="book"><select className="input" {...f.bind("book")}>{books.map((b) => <option key={b.id} value={b.id}>{b.title}</option>)}</select></Field>
      </div>
      <fieldset className="parts"><legend>Tick each part the child did with little or no help</legend>
        {PARTS.map((p, i) => <label key={p} className={f.values.parts[i] ? "on" : ""}><input type="checkbox" checked={f.values.parts[i]} onChange={() => toggle(i)} /> {i + 1}. {p}</label>)}
      </fieldset>
      <div className="row"><strong>{score} of 6</strong><Pill tone={result[0]}>{result[1]}</Pill></div>
      <Field label="Things to practise" id="practice_notes" hint="Shared with the parent with the certificate."><textarea className="input" {...f.bind("practice_notes")} /></Field>
      <p className="muted" style={{ margin: 0 }}>The pass rule (5–6 certificate, 3–4 certificate with practice, 0–2 repeat) is a draft for Sija to adjust.</p>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Curriculum() {
  const toast = useToast();
  const { data: books, loading, error, reload } = useData("/books/");
  const [checking, setChecking] = useState(false);
  const [bump, setBump] = useState(0);
  const [tab, setTab] = useState("book");
  if (loading && !books) return <div className="page"><Loading /></div>;
  if (error) return <div className="page"><ErrorState error={error} onRetry={reload} /></div>;
  const book = books.find((b) => b.code === "book-1");
  return (
    <div className="page">
      <div className="page-head"><div><h1>Book 1 and certificates</h1><p>The 35 lessons, end-of-book checks and certificates.</p></div><div className="spacer" />
        <button className="btn btn-primary" onClick={() => setChecking(true)}>Record an end-of-book check</button></div>
      <div className="tabs" role="tablist" style={{ padding: 0, marginBottom: 16 }}>
        {[["book", "Book 1 lessons"], ["checks", "Checks"], ["certs", "Certificates"]].map(([k, l]) => <button key={k} role="tab" aria-selected={tab === k} className={`tab${tab === k ? " on" : ""}`} onClick={() => setTab(k)}>{l}</button>)}
      </div>
      {tab === "book" && (book ? <ol className="unit-grid">{book.units.map((u) => (
        <li key={u.id} className="unit-card"><span className="unit-no">{u.number}</span><div><strong>{u.title_nd}</strong><div className="muted">{u.title_en}</div>
          <div className="unit-meta"><Pill tone="neutral">{u.kind}</Pill>{u.culture && <span className="muted">Culture: {u.culture}</span>}</div></div></li>))}</ol>
        : <Empty title="Book 1 is not loaded">Run the import_book1 command on the server.</Empty>)}
      {tab === "checks" && <DataTable path="/book-checks/" reloadKey={bump} empty={<Empty title="No checks yet">Record one when a child finishes Book 1.</Empty>}
        columns={[{ key: "student_name", label: "Child" }, { key: "checked_on", label: "Date", render: (r) => date(r.checked_on) }, { key: "score", label: "Score", render: (r) => `${r.score} of 6` },
          { key: "result", label: "Result", render: (r) => <Pill status={r.result}>{r.result_label}</Pill> }, { key: "teacher_name", label: "Checked by" }, { key: "practice_notes", label: "To practise" }]} />}
      {tab === "certs" && <DataTable path="/certificates/" reloadKey={bump} empty={<Empty title="No certificates yet">A certificate is made when a check scores 3 or more.</Empty>}
        columns={[{ key: "number", label: "Number" }, { key: "student_name", label: "Child" }, { key: "book_title", label: "Book" }, { key: "issued_on", label: "Date", render: (r) => date(r.issued_on) },
          { key: "pdf", label: "", render: (r) => <button className="btn btn-ghost btn-sm" onClick={() => openPdf(`/certificates/${r.id}/pdf/`).catch((e) => toast(e.message))}>Open PDF</button> }]} />}
      {checking && <CheckForm books={books.filter((b) => b.is_ready)} onClose={() => setChecking(false)} onDone={(r) => { setChecking(false); setBump((n) => n + 1); toast(r.certificate ? `Certificate ${r.certificate.number} made` : "Check saved"); }} />}
    </div>
  );
}
