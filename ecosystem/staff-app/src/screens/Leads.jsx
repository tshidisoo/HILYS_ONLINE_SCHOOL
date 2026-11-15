import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import DataTable from "../components/DataTable";
import { useOpenParam, useRecord } from "../components/hooks";
import { useLookup } from "../components/lookups";
import { Confirm, DL, Dialog, Empty, Field, Panel, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { COUNTRIES, ago, date, when } from "../format";

const STATUS = [["new", "New"], ["contacted", "Contacted"], ["trial_booked", "Trial booked"], ["trial_done", "Trial done"], ["converted", "Became a family"], ["dismissed", "Dismissed"]];
const CLOCK = { late: ["bad", "Late"], due_soon: ["warn", "Due soon"], on_time: ["info", "On time"], answered: ["good", "Answered"] };

export function LeadForm({ onDone, onClose }) {
  const f = useForm({ parent_name: "", phone: "", email: "", country: "GB", child_name: "", child_age: "", interest: "live", source: "WhatsApp", message: "" });
  const save = () => f.submit(async (v) => { const r = await api("/leads/", { method: "POST", body: { ...v, child_age: v.child_age || null } }); onDone(r); });
  return (
    <Dialog title="Add a lead" onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || (!f.values.phone && !f.values.email)} onClick={save}>{f.busy ? "Saving…" : "Save lead"}</button></>}>
      <div className="form-grid">
        <Field label="Parent's name" id="parent_name" error={f.errors.parent_name}><input className="input" {...f.bind("parent_name")} /></Field>
        <Field label="Where they heard of us" id="source"><select className="input" {...f.bind("source")}>{["WhatsApp", "Phone", "Referral from a family", "Facebook", "Walk-in", "Website"].map((s) => <option key={s}>{s}</option>)}</select></Field>
        <Field label="Phone or WhatsApp" id="phone" hint="Phone or email is needed so we can reply." error={f.errors.phone}><input className="input" {...f.bind("phone")} inputMode="tel" /></Field>
        <Field label="Email" id="email" error={f.errors.email}><input className="input" type="email" {...f.bind("email")} /></Field>
        <Field label="Country" id="country"><select className="input" {...f.bind("country")}>{Object.entries(COUNTRIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></Field>
        <Field label="Interested in" id="interest"><select className="input" {...f.bind("interest")}><option value="live">Live lessons</option><option value="video">Video course</option><option value="plus">HILYS Plus</option><option value="not_sure">Not sure yet</option></select></Field>
        <Field label="Child's first name" id="child_name"><input className="input" {...f.bind("child_name")} /></Field>
        <Field label="Child's age" id="child_age" error={f.errors.child_age}><input className="input" type="number" min="3" max="18" {...f.bind("child_age")} /></Field>
        <Field label="What they said" id="message" wide><textarea className="input" {...f.bind("message")} /></Field>
      </div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function TrialDialog({ lead, onClose, onDone }) {
  const teachers = useLookup("teachers");
  const f = useForm({ teacher: "", day: "", time: "17:00" });
  const save = () => f.submit(async (v) => {
    const starts_at = new Date(`${v.day}T${v.time}:00+02:00`).toISOString(); // typed in Harare time
    onDone(await api(`/leads/${lead.id}/book_trial/`, { method: "POST", body: { teacher: v.teacher, starts_at } }));
  });
  return (
    <Dialog title={`Book a free trial for ${lead.child_name || "the child"}`} onClose={onClose}
            footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || !f.values.teacher || !f.values.day} onClick={save}>Book trial</button></>}>
      <Field label="Teacher" id="teacher" error={f.errors.teacher}><select className="input" {...f.bind("teacher")}><option value="">Choose…</option>{teachers.map((t) => <option key={t.id} value={t.id}>{t.display_name}</option>)}</select></Field>
      <div className="form-grid">
        <Field label="Day" id="day"><input className="input" type="date" {...f.bind("day")} /></Field>
        <Field label="Time in Harare" id="time" hint={lead.time_zone ? `The family is in ${lead.time_zone}.` : undefined}><input className="input" type="time" {...f.bind("time")} /></Field>
      </div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function LeadPanel({ id, onClose, onChanged }) {
  const toast = useToast();
  const navigate = useNavigate();
  const { data: lead, setData: setLead, reload: load, error: loadError } = useRecord(`/leads/${id}/`);
  const [tab, setTab] = useState("Details");
  const [dialog, setDialog] = useState(null);
  const [actionError, setError] = useState("");
  const error = actionError || loadError?.message;
  const act = async (fn, msg) => { try { const r = await fn(); if (r?.id) setLead(r); else load(); onChanged(); toast(msg); } catch (e) { setError(e.message); } };
  if (!lead) return <Panel title="Lead" onClose={onClose}>{error ? <div className="form-error">{error}</div> : <p className="muted">Loading…</p>}</Panel>;
  const [tone, label] = CLOCK[lead.reply_clock];
  const closed = ["converted", "dismissed"].includes(lead.status);
  return (
    <Panel title={lead.parent_name || "Lead with no name"} subtitle={`${lead.source} · ${ago(lead.created_at)}`} onClose={onClose}
      tabs={["Details", "Follow-ups"]} tab={tab} setTab={setTab}
      actions={!closed && <>
        <button className="btn btn-ghost btn-sm" onClick={() => act(() => api(`/leads/${id}/replied/`, { method: "POST", body: { note: "Replied" } }), "Marked as replied")}>I replied</button>
        <button className="btn btn-ghost btn-sm" onClick={() => setDialog("trial")}>Book free trial</button>
        <button className="btn btn-primary btn-sm" onClick={() => setDialog("convert")}>Make a family</button>
        <button className="btn btn-danger btn-sm" onClick={() => setDialog("dismiss")}>Dismiss</button>
      </>}>
      {error && <div className="form-error" role="alert">{error}</div>}
      <div className="row"><Pill status={lead.status}>{lead.status_label}</Pill><Pill tone={tone}>Reply: {label}</Pill>{lead.reply_due_at && !lead.first_reply_at && <span className="muted">Reply by {when(lead.reply_due_at)}</span>}</div>
      {lead.needs_cleanup && <div className="card card-tight tone-warn"><strong>Needs cleanup:</strong> {lead.cleanup_reasons.join("; ")}</div>}
      {tab === "Details" && <DL rows={[["Phone", lead.phone], ["Email", lead.email], ["Country", COUNTRIES[lead.country] || lead.country], ["Time zone", lead.time_zone],
        ["Child", lead.child_name ? `${lead.child_name}${lead.child_age ? `, ${lead.child_age}` : ""}` : null], ["Interested in", lead.interest_label],
        ["Level check result", lead.suggested_level], ["Owner", lead.owner_name], ["What they said", lead.message], ["Dismissed because", lead.dismissed_reason]]} />}
      {tab === "Details" && lead.family && <button className="btn btn-ghost" onClick={() => navigate(`/families?open=${lead.family}`)}>Open the family</button>}
      {tab === "Follow-ups" && (lead.follow_ups.length ? <ul className="stack" style={{ paddingLeft: 18 }}>{lead.follow_ups.map((f, i) => <li key={i}><strong>{date(f.at)}</strong> · {f.by}{f.note ? `: ${f.note}` : ""}</li>)}</ul> : <Empty title="No follow-ups yet">Tick “I replied” after each call or message.</Empty>)}
      {dialog === "trial" && <TrialDialog lead={lead} onClose={() => setDialog(null)} onDone={(r) => { setLead(r); setDialog(null); onChanged(); toast("Trial booked"); }} />}
      {dialog === "dismiss" && <Confirm title="Dismiss this lead?" message="It leaves the open list. You can still find it under Dismissed." needReason="Why?" danger confirmLabel="Dismiss lead"
        onClose={() => setDialog(null)} onConfirm={(reason) => api(`/leads/${id}/dismiss/`, { method: "POST", body: { reason } }).then((r) => { setLead(r); onChanged(); toast("Lead dismissed"); })} />}
      {dialog === "convert" && <Confirm title="Make this lead a family?" message={`This creates the ${lead.parent_name || "parent"} family, adds ${lead.child_name || "the child"}, and starts an enrolment at the Trial stage.`}
        confirmLabel="Make a family" onClose={() => setDialog(null)}
        onConfirm={() => api(`/leads/${id}/convert/`, { method: "POST", body: {} }).then((r) => { onChanged(); toast("Family created"); navigate(`/families?open=${r.family}`); })} />}
    </Panel>
  );
}

export default function Leads() {
  const params = new URLSearchParams(window.location.search);
  const [open, setOpen] = useState(useOpenParam());
  const [adding, setAdding] = useState(false);
  const [reload, setReload] = useState(0);
  const initial = { status: params.get("status") || "", clock: params.get("clock") || "", needs_cleanup: params.get("needs_cleanup") || "", open: params.get("status") ? "" : "1" };
  return (
    <div className="page">
      <div className="page-head"><div><h1>Leads</h1><p>Every enquiry gets a reply within one working day (Harare time).</p></div><div className="spacer" />
        <button className="btn btn-primary" onClick={() => setAdding(true)}>Add a lead</button></div>
      <DataTable path="/leads/" reloadKey={reload} initial={initial} onOpen={(r) => setOpen(r.id)} searchLabel="Search names, phones, emails"
        filters={[{ key: "open", label: "Show", options: [["1", "Open leads only"]] }, { key: "status", label: "Status", options: STATUS },
                  { key: "clock", label: "Reply clock", options: [["late", "Late only"]] }, { key: "needs_cleanup", label: "Cleanup", options: [["true", "Needs cleanup"]] }]}
        empty={<Empty title="No leads yet" action={<button className="btn btn-primary btn-sm" onClick={() => setAdding(true)}>Add a lead</button>}>Enquiries from the website arrive here on their own.</Empty>}
        columns={[
          { key: "parent_name", label: "Parent", sort: "parent_name", render: (r) => <><div className="cell-main">{r.parent_name || "No name"} {r.is_demo && <span className="demo-tag">DEMO</span>}</div><div className="cell-sub">{r.phone || r.email}</div></> },
          { key: "child", label: "Child", render: (r) => r.child_name ? `${r.child_name}${r.child_age ? `, ${r.child_age}` : ""}` : "—" },
          { key: "interest_label", label: "Wants" },
          { key: "source", label: "Source" },
          { key: "status", label: "Status", render: (r) => <><Pill status={r.status}>{r.status_label}</Pill>{r.needs_cleanup && <div className="cell-sub">Needs cleanup</div>}</> },
          { key: "clock", label: "Reply", sort: "reply_due_at", render: (r) => <Pill tone={CLOCK[r.reply_clock][0]}>{CLOCK[r.reply_clock][1]}</Pill> },
          { key: "created_at", label: "Came in", sort: "created_at", render: (r) => ago(r.created_at) },
        ]} />
      {open && <LeadPanel id={open} onClose={() => setOpen(null)} onChanged={() => setReload((n) => n + 1)} />}
      {adding && <LeadForm onClose={() => setAdding(false)} onDone={(r) => { setAdding(false); setReload((n) => n + 1); setOpen(r.id); }} />}
    </div>
  );
}
