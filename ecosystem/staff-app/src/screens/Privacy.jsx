import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import { useData } from "../components/hooks";
import { useLookup } from "../components/lookups";
import { Dialog, Empty, Field, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { date, when } from "../format";

function RequestForm({ req, onClose, onDone }) {
  const families = useLookup("families");
  const f = useForm(req || { family: "", requester: "", kind: "see", notes: "" });
  return (
    <Dialog title={req ? "Data request" : "Log a data request"} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !f.values.requester} onClick={() => f.submit(async (v) => onDone(req ? await api(`/privacy/requests/${req.id}/`, { method: "PATCH", body: { status: v.status, notes: v.notes } }) : await api("/privacy/requests/", { method: "POST", body: { ...v, family: v.family || null } })))}>Save</button></>}>
      {!req && <><Field label="Who asked" id="requester" error={f.errors.requester}><input className="input" {...f.bind("requester")} /></Field>
        <Field label="Family, if known" id="family"><select className="input" {...f.bind("family")}><option value="">Not on record</option>{families.map((x) => <option key={x.id} value={x.id}>{x.parent_name}</option>)}</select></Field>
        <Field label="What they asked for" id="kind"><select className="input" {...f.bind("kind")}><option value="see">See my data</option><option value="delete">Delete my data</option><option value="correct">Correct my data</option></select></Field></>}
      {req && <Field label="Status" id="status"><select className="input" {...f.bind("status")}><option value="received">Received</option><option value="in_progress">In progress</option><option value="done">Done</option><option value="refused">Refused (with reason)</option></select></Field>}
      <Field label="Notes" id="notes"><textarea className="input" {...f.bind("notes")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Privacy() {
  const { user } = useAuth();
  const toast = useToast();
  const [edit, setEdit] = useState(null);
  const [reload, setReload] = useState(0);
  const settings = useData("/settings/");
  const access = useData(user.permissions.is_leadership ? "/privacy/requests/sensitive_access/" : null);
  async function exportFamily(id) {
    try {
      const res = await api(`/privacy/requests/export/${id}/`, { raw: true });
      const a = document.createElement("a"); a.href = URL.createObjectURL(await res.blob()); a.download = `family-${id}-data.json`; a.click();
    } catch (e) { toast(e.message); }
  }
  return (
    <div className="page">
      <div className="page-head"><div><h1>Privacy</h1><p>Requests to see, correct or delete data. Reply within one month.</p></div><div className="spacer" /><button className="btn btn-primary" onClick={() => setEdit({})}>Log a request</button></div>
      <DataTable path="/privacy/requests/" reloadKey={reload} onOpen={setEdit} empty={<Empty title="No data requests">When a parent asks to see or delete their data, log it here.</Empty>}
        columns={[{ key: "requester", label: "Who asked", render: (r) => <><div className="cell-main">{r.requester}</div><div className="cell-sub">{r.family_name}</div></> }, { key: "kind_label", label: "Asked for" },
          { key: "due_on", label: "Reply by", render: (r) => date(r.due_on) }, { key: "status", label: "Status", render: (r) => <Pill status={r.status}>{r.status_label}</Pill> },
          user.permissions.is_leadership && { key: "x", label: "", render: (r) => r.family && <button className="btn btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); exportFamily(r.family); }}>Download their data</button> }].filter(Boolean)} />
      <div className="an-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16, marginTop: 24 }}>
        <section className="card"><h2>How long we keep data</h2><p className="muted" style={{ whiteSpace: "pre-wrap" }}>{settings.data?.retention_notes}</p><p className="muted">Change this in Company settings. Draft: needs the owner and a lawyer.</p></section>
        {user.permissions.is_leadership && <section className="card"><h2>Who opened children's support notes</h2>
          {(access.data || []).length === 0 ? <p className="muted">Nobody yet.</p> : <ul>{access.data.slice(0, 12).map((a, i) => <li key={i}>{when(a.at)}: {a.user} opened {a.student}</li>)}</ul>}</section>}
      </div>
      {edit && <RequestForm req={edit.id ? edit : null} onClose={() => setEdit(null)} onDone={() => { setEdit(null); setReload((n) => n + 1); toast("Saved"); }} />}
    </div>
  );
}
