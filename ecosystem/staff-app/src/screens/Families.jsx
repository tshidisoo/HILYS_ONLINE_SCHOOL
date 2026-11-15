import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import Bin from "../components/Bin";
import DataTable from "../components/DataTable";
import { useData, useOpenParam, useRecord } from "../components/hooks";
import { clearLookup } from "../components/lookups";
import { Confirm, DL, Dialog, Empty, Field, Panel, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { COUNTRIES, TIME_ZONES, ago, date, money, when } from "../format";
import "./Families.css";

function balanceText(b) {
  const owed = Object.entries(b?.owed || {});
  return owed.length ? owed.map(([c, v]) => money(v, c)).join(" + ") : "Nothing owed";
}

export function FamilyForm({ family, onClose, onDone }) {
  const { user } = useAuth();
  const f = useForm(family || { parent_name: "", email: "", phone: "", whatsapp: "", country: "GB", city: "", time_zone: "Europe/London", payer_name: "", notes: "", founding_family: false });
  const save = () => f.submit(async (v) => {
    const body = { ...v }; delete body.students; delete body.balance;
    const r = family ? await api(`/families/${family.id}/`, { method: "PATCH", body }) : await api("/families/", { method: "POST", body });
    clearLookup("families");
    onDone(r);
  });
  const phoneDup = (f.errors.phone || "").includes("already exists");
  return (
    <Dialog title={family ? "Edit family" : "Add a family"} wide onClose={onClose}
            footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || !f.values.parent_name} onClick={save}>{f.busy ? "Saving…" : "Save"}</button></>}>
      <div className="form-grid">
        <Field label="Parent's name" id="parent_name" error={f.errors.parent_name}><input className="input" {...f.bind("parent_name")} /></Field>
        <Field label="Who pays, if someone else" id="payer_name" hint="For example a grandparent. Shown on invoices."><input className="input" {...f.bind("payer_name")} /></Field>
        <Field label="Email" id="email" hint="Also their username for the parent app." error={f.errors.email}><input className="input" type="email" {...f.bind("email")} /></Field>
        <Field label="Phone" id="phone" error={f.errors.phone}><input className="input" inputMode="tel" {...f.bind("phone")} /></Field>
        <Field label="WhatsApp, if different" id="whatsapp"><input className="input" inputMode="tel" {...f.bind("whatsapp")} /></Field>
        <Field label="Country" id="country"><select className="input" {...f.bind("country")}>{Object.entries(COUNTRIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></Field>
        <Field label="City" id="city"><input className="input" {...f.bind("city")} /></Field>
        <Field label="Family's time zone" id="time_zone" hint="Lesson times are shown to the family in this zone."><select className="input" {...f.bind("time_zone")}>{TIME_ZONES.map((t) => <option key={t}>{t}</option>)}</select></Field>
        <Field label="Notes" id="notes" wide><textarea className="input" {...f.bind("notes")} /></Field>
        <label className="check wide"><input type="checkbox" checked={!!f.values.founding_family} onChange={f.set("founding_family")} /> One of the founding families</label>
        {phoneDup && user.permissions.can_override_rules && <Field label="Save anyway: why does this phone match another family?" id="override_reason" wide hint="Only the owner can do this. The reason is kept in the audit log."><input className="input" {...f.bind("override_reason")} /></Field>}
      </div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function ChildForm({ family, child, onClose, onDone }) {
  const f = useForm(child ? { ...child, support_notes: "" } : { family: family.id, first_name: "", last_name: family.parent_name.split(" ").slice(-1)[0], birth_year: "", level: "", notes: "", support_notes: "" });
  const save = () => f.submit(async (v) => {
    const body = { ...v, birth_year: v.birth_year || null };
    if (child && !body.support_notes) delete body.support_notes;
    onDone(child ? await api(`/students/${child.id}/`, { method: "PATCH", body }) : await api("/students/", { method: "POST", body }));
  });
  return (
    <Dialog title={child ? `Edit ${child.first_name}` : "Add a child"} onClose={onClose}
            footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || !f.values.first_name} onClick={save}>Save</button></>}>
      <div className="form-grid">
        <Field label="First name" id="first_name" error={f.errors.first_name}><input className="input" {...f.bind("first_name")} /></Field>
        <Field label="Last name" id="last_name"><input className="input" {...f.bind("last_name")} /></Field>
        <Field label="Year of birth" id="birth_year" error={f.errors.birth_year}><input className="input" type="number" min="2005" max="2025" {...f.bind("birth_year")} /></Field>
        <Field label="Level" id="level" hint="From the free trial lesson."><select className="input" {...f.bind("level")}><option value="">Not checked yet</option><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="conversation">Conversation</option></select></Field>
        <Field label="Support notes (private)" id="support_notes" wide hint={child?.has_support_notes ? "Notes are saved. Type here only to replace them." : "Learning or health needs the teacher should know. Kept encrypted; opening them is logged."}><textarea className="input" {...f.bind("support_notes")} /></Field>
      </div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function Messages({ familyId }) {
  const { data, reload, error } = useData(`/families/${familyId}/messages/`);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  async function send(e) {
    e.preventDefault(); setBusy(true);
    try { await api(`/families/${familyId}/messages/`, { method: "POST", body: { body } }); setBody(""); reload(); } finally { setBusy(false); }
  }
  if (error) return <div className="form-error">{error.message}</div>;
  return (
    <div className="msgs">
      {(data || []).length === 0 && <Empty title="No messages yet">Messages the family sends from the app appear here.</Empty>}
      {(data || []).map((m) => <div key={m.id} className={`msg${m.from_family ? " from-family" : ""}`}><strong>{m.sender_name}</strong><p>{m.body}</p><span className="muted">{ago(m.created_at)}</span></div>)}
      <form onSubmit={send} className="msg-form"><label htmlFor="msg" className="sr-only">Message to the family</label>
        <textarea id="msg" className="input" placeholder="Write to the family…" value={body} onChange={(e) => setBody(e.target.value)} />
        <button className="btn btn-primary" disabled={busy || !body.trim()}>Send</button></form>
    </div>
  );
}

function FamilyPanel({ id, onClose, onChanged }) {
  const toast = useToast();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: fam, reload, error } = useRecord(`/families/${id}/`);
  const [tab, setTab] = useState("Overview");
  const [dialog, setDialog] = useState(null);
  const [login, setLogin] = useState(null);
  const docs = useData(tab === "Money" ? `/documents/?family=${id}&page_size=50` : null);
  const pays = useData(tab === "Money" ? `/payments/?family=${id}&page_size=50` : null);
  const enrols = useData(tab === "Children" ? `/enrolments/?student__family=${id}` : null);
  const timeline = useData(tab === "Timeline" ? `/families/${id}/timeline/` : null);
  if (error) return <Panel title="Family" onClose={onClose}><div className="form-error">{error.message}</div></Panel>;
  if (!fam) return <Panel title="Family" onClose={onClose}><p className="muted">Loading…</p></Panel>;
  const done = (msg) => { reload(); onChanged(); toast(msg); setDialog(null); };
  return (
    <Panel title={fam.parent_name} subtitle={`${COUNTRIES[fam.country] || ""}${fam.city ? ` · ${fam.city}` : ""} · ${fam.time_zone}`} onClose={onClose}
      tabs={["Overview", "Children", "Money", "Messages", "Timeline"]} tab={tab} setTab={setTab}
      actions={<>
        <button className="btn btn-ghost btn-sm" onClick={() => setDialog("edit")}>Edit</button>
        <button className="btn btn-ghost btn-sm" onClick={() => setDialog("child")}>Add a child</button>
        <button className="btn btn-primary btn-sm" onClick={() => navigate(`/documents?new=invoice&family=${fam.id}`)}>New invoice</button>
        {!fam.has_login && <button className="btn btn-ghost btn-sm" onClick={() => setDialog("login")}>Give app login</button>}
        <button className="btn btn-ghost btn-sm" onClick={() => api("/documents/statement/", { method: "POST", body: { family: fam.id } }).then((d) => navigate(`/documents?open=${d.id}`)).catch((e) => toast(e.message))}>Statement</button>
      </>}>
      {fam.needs_cleanup && <div className="card card-tight tone-warn"><strong>Needs cleanup:</strong> {fam.cleanup_reasons.join("; ")}</div>}
      {tab === "Overview" && <>
        <div className="fam-balance card card-tight"><span className="muted">Balance</span><strong>{balanceText(fam.balance)}</strong>
          {Object.entries(fam.balance?.credit || {}).map(([c, v]) => <span key={c} className="muted">Paid ahead: {money(v, c)}</span>)}</div>
        <DL rows={[["Email", fam.email], ["Phone", fam.phone], ["WhatsApp", fam.whatsapp], ["Who pays", fam.payer_name || fam.parent_name], ["Owner at HILYS", fam.owner_name],
          ["Parent app", fam.has_login ? "Has a login" : "No login yet"], ["Came from", fam.source], ["Founding family", fam.founding_family ? "Yes" : "No"], ["Notes", fam.notes]]} />
      </>}
      {tab === "Children" && <div className="stack">
        {fam.students.length === 0 && <Empty title="No children yet" action={<button className="btn btn-primary btn-sm" onClick={() => setDialog("child")}>Add a child</button>} />}
        {fam.students.map((s) => {
          const es = (enrols.data?.results || []).filter((e) => e.student === s.id);
          return (
            <div key={s.id} className="card card-tight child-card">
              <div className="row"><h3>{s.name}</h3>{s.level_label && <Pill tone="info">{s.level_label}</Pill>}<div className="spacer" />
                {s.has_support_notes && <button className="link-btn" onClick={() => api(`/students/${s.id}/support_notes/`).then((r) => setDialog({ notes: r.support_notes, name: s.first_name }))}>Support notes</button>}
                <button className="link-btn" onClick={() => setDialog({ child: s })}>Edit</button></div>
              {s.birth_year && <span className="muted">Born {s.birth_year}</span>}
              {es.map((e) => <button key={e.id} className="enrol-line" onClick={() => navigate(`/enrolments?open=${e.id}`)}>
                <Pill status={e.stage}>{e.stage_label}</Pill><span>{e.package_name || "No package yet"} · {e.teacher_name || "No teacher yet"}</span></button>)}
              {enrols.data && es.length === 0 && <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/enrolments?new=1&student=${s.id}`)}>Enrol {s.first_name}</button>}
            </div>);
        })}
      </div>}
      {tab === "Money" && <div className="stack">
        <h3>Documents</h3>
        {(docs.data?.results || []).length === 0 && <p className="muted">No documents yet.</p>}
        {(docs.data?.results || []).map((d) => <button key={d.id} className="money-line" onClick={() => navigate(`/documents?open=${d.id}`)}>
          <span>{d.kind_label} {d.number || "(draft)"}</span><span className="muted">{date(d.issue_date)}</span><span>{money(d.total, d.currency)}</span><Pill status={d.is_overdue ? "overdue" : d.status}>{d.is_overdue ? "Overdue" : d.status_label}</Pill></button>)}
        <h3>Payments</h3>
        {(pays.data?.results || []).length === 0 && <p className="muted">No payments yet.</p>}
        {(pays.data?.results || []).map((p) => <div key={p.id} className="money-line"><span>{p.method_label} {p.reference}</span><span className="muted">{date(p.received_on)}</span><span>{money(p.amount, p.currency)}</span>{p.reversed_at ? <Pill status="cancelled">Reversed</Pill> : <Pill status="paid">Received</Pill>}</div>)}
      </div>}
      {tab === "Messages" && <Messages familyId={fam.id} />}
      {tab === "Timeline" && <ol className="timeline">{(timeline.data || []).map((e, i) => <li key={i}><span className="muted">{date(e.at)}</span><strong>{e.what}</strong>{e.detail && <span className="muted">{e.detail}</span>}</li>)}
        {timeline.data?.length === 0 && <Empty title="Nothing has happened yet" />}</ol>}

      {dialog === "edit" && <FamilyForm family={fam} onClose={() => setDialog(null)} onDone={() => done("Family saved")} />}
      {dialog === "child" && <ChildForm family={fam} onClose={() => setDialog(null)} onDone={() => done("Child added")} />}
      {dialog?.child && <ChildForm family={fam} child={dialog.child} onClose={() => setDialog(null)} onDone={() => done("Child saved")} />}
      {dialog?.notes !== undefined && <Dialog title={`Support notes: ${dialog.name}`} onClose={() => setDialog(null)}><p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{dialog.notes}</p><p className="muted">Opening these notes is logged.</p></Dialog>}
      {dialog === "login" && <Confirm title="Give the family an app login?" message={`The username is ${fam.email || "their email (add one first)"}. You will see a one-time password to send them.`} confirmLabel="Create login"
        onClose={() => setDialog(null)} onConfirm={() => api(`/families/${fam.id}/create_login/`, { method: "POST" }).then((r) => { setLogin(r); reload(); })} />}
      {login && <Dialog title="App login created" onClose={() => setLogin(null)}><p style={{ margin: 0 }}>Send these to the parent on WhatsApp. The password is shown only once.</p>
        <DL rows={[["Username", login.username], ["Password", <code key="p">{login.password}</code>]]} /></Dialog>}
    </Panel>
  );
}

export default function Families() {
  const [open, setOpen] = useState(useOpenParam());
  const [adding, setAdding] = useState(false);
  const [reload, setReload] = useState(0);
  const [bin, setBin] = useState(false);
  const { user } = useAuth();
  return (
    <div className="page">
      <div className="page-head"><div><h1>Families</h1><p>The parent who pays, and the children who learn.</p></div><div className="spacer" />
        {user.permissions.is_leadership && <button className="btn btn-ghost" onClick={() => setBin(true)}>Deleted</button>}
        <button className="btn btn-primary" onClick={() => setAdding(true)}>Add a family</button></div>
      <DataTable path="/families/" reloadKey={reload} onOpen={(r) => setOpen(r.id)} searchLabel="Search parents, children, phones"
        initial={{ needs_cleanup: new URLSearchParams(window.location.search).get("needs_cleanup") || "" }}
        filters={[{ key: "country", label: "Country", options: Object.entries(COUNTRIES) }, { key: "needs_cleanup", label: "Cleanup", options: [["true", "Needs cleanup"]] }, { key: "founding_family", label: "Founding", options: [["true", "Founding families"]] }]}
        empty={<Empty title="No families yet" action={<button className="btn btn-primary btn-sm" onClick={() => setAdding(true)}>Add a family</button>}>Families are usually made from a lead after the free trial.</Empty>}
        columns={[
          { key: "parent_name", label: "Parent", sort: "parent_name", render: (r) => <><div className="cell-main">{r.parent_name} {r.is_demo && <span className="demo-tag">DEMO</span>}</div><div className="cell-sub">{r.email || r.phone}</div></> },
          { key: "children", label: "Children", render: (r) => r.students.map((s) => s.first_name).join(", ") || "—" },
          { key: "country", label: "Where", render: (r) => `${r.city ? r.city + ", " : ""}${r.country}` },
          { key: "balance", label: "Owes", align: "right", render: (r) => balanceText(r.balance) },
          { key: "flags", label: "", render: (r) => <>{r.needs_cleanup && <Pill tone="warn">Needs cleanup</Pill>}{r.founding_family && <Pill tone="info">Founding</Pill>}</> },
        ]} />
      {open && <FamilyPanel id={open} onClose={() => setOpen(null)} onChanged={() => setReload((n) => n + 1)} />}
      {adding && <FamilyForm onClose={() => setAdding(false)} onDone={(r) => { setAdding(false); setReload((n) => n + 1); setOpen(r.id); }} />}
      {bin && <Bin base="/families/" label={(r) => r.parent_name} onClose={() => setBin(false)} onRestored={() => setReload((n) => n + 1)} />}
    </div>
  );
}
