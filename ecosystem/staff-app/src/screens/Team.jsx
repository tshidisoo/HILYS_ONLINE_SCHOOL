import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import { clearLookup } from "../components/lookups";
import { Confirm, Dialog, Field, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { ago } from "../format";

const ROLES = [["owner", "Owner"], ["coordinator", "Coordinator"], ["finance", "Finance"], ["teacher", "Teacher"], ["parent", "Parent"]];

function UserForm({ u, onClose, onDone }) {
  const f = useForm(u ? { ...u, teacher_profile: u.teacher_profile || { pay_one_to_one: "6", pay_group: "8", pay_currency: "USD", zoom_link: "", bio: "", takes_new_students: true } }
    : { username: "", first_name: "", last_name: "", email: "", phone: "", role: "coordinator", time_zone: "Africa/Harare", teacher_profile: { pay_one_to_one: "6", pay_group: "8", pay_currency: "USD", zoom_link: "", bio: "", takes_new_students: true } });
  const tp = f.values.teacher_profile;
  const setTp = (k) => (e) => f.setValues((v) => ({ ...v, teacher_profile: { ...v.teacher_profile, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value } }));
  const save = () => f.submit(async (v) => {
    const body = { ...v }; delete body.permissions; delete body.last_login; if (body.role !== "teacher") delete body.teacher_profile;
    const r = u ? await api(`/users/${u.id}/`, { method: "PATCH", body }) : await api("/users/", { method: "POST", body });
    clearLookup("teachers"); clearLookup("staff"); onDone(r);
  });
  return (
    <Dialog title={u ? `Edit ${u.display_name}` : "Add a person"} wide onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || !f.values.username} onClick={save}>Save</button></>}>
      <div className="form-grid">
        <Field label="Username" id="username" error={f.errors.username}><input className="input" {...f.bind("username")} disabled={!!u} /></Field>
        <Field label="Role" id="role"><select className="input" {...f.bind("role")}>{ROLES.filter(([k]) => k !== "parent").map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></Field>
        <Field label="First name" id="first_name"><input className="input" {...f.bind("first_name")} /></Field>
        <Field label="Last name" id="last_name"><input className="input" {...f.bind("last_name")} /></Field>
        <Field label="Email" id="email" error={f.errors.email}><input className="input" type="email" {...f.bind("email")} /></Field>
        <Field label="Phone" id="phone"><input className="input" {...f.bind("phone")} /></Field>
      </div>
      {f.values.role === "teacher" && <fieldset className="card card-tight" style={{ border: "1px solid var(--line)" }}><legend style={{ fontWeight: 700 }}>Teacher details</legend><div className="form-grid">
        <Field label="Pay per one-to-one lesson" id="p1" hint="Draft rate."><input id="p1" className="input" type="number" step="0.01" value={tp.pay_one_to_one} onChange={setTp("pay_one_to_one")} /></Field>
        <Field label="Pay per group lesson" id="p2"><input id="p2" className="input" type="number" step="0.01" value={tp.pay_group} onChange={setTp("pay_group")} /></Field>
        <Field label="Zoom link" id="zoom" wide><input id="zoom" className="input" value={tp.zoom_link} onChange={setTp("zoom_link")} /></Field>
        <label className="check wide"><input type="checkbox" checked={tp.takes_new_students} onChange={setTp("takes_new_students")} /> Takes new students</label></div></fieldset>}
      {!u && <p className="muted" style={{ margin: 0 }}>After saving, set a password from the list so the person can sign in.</p>}
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Team() {
  const { user } = useAuth();
  const toast = useToast();
  const [edit, setEdit] = useState(null);
  const [pw, setPw] = useState(null);
  const [password, setPassword] = useState("");
  const [suspend, setSuspend] = useState(null);
  const [reload, setReload] = useState(0);
  const lead = user.permissions.is_leadership;
  return (
    <div className="page">
      <div className="page-head"><div><h1>Team and logins</h1><p>{lead ? "Add people, change roles, suspend logins and reset passwords." : "Only the owner can change logins."}</p></div><div className="spacer" />
        {lead && <button className="btn btn-primary" onClick={() => setEdit({})}>Add a person</button>}</div>
      <DataTable path="/users/" reloadKey={reload} onOpen={lead ? setEdit : undefined} filters={[{ key: "role", label: "Role", options: ROLES }, { key: "is_suspended", label: "Status", options: [["true", "Suspended"], ["false", "Active"]] }]}
        columns={[{ key: "display_name", label: "Name", render: (r) => <><div className="cell-main">{r.display_name}</div><div className="cell-sub">{r.username}</div></> }, { key: "role_label", label: "Role" },
          { key: "last_login", label: "Last signed in", sort: "last_login", render: (r) => r.last_login ? ago(r.last_login) : "Never" },
          { key: "state", label: "", render: (r) => r.is_suspended ? <Pill tone="bad">Suspended</Pill> : <Pill tone="good">Active</Pill> },
          lead && { key: "act", label: "", render: (r) => <div className="row" onClick={(e) => e.stopPropagation()}>
            <button className="btn btn-ghost btn-sm" onClick={() => { setPw(r); setPassword(""); }}>Set password</button>
            {r.id !== user.id && <button className="btn btn-ghost btn-sm" onClick={() => setSuspend(r)}>{r.is_suspended ? "Restore" : "Suspend"}</button>}</div> }].filter(Boolean)} />
      {edit && <UserForm u={edit.id ? edit : null} onClose={() => setEdit(null)} onDone={() => { setEdit(null); setReload((n) => n + 1); toast("Saved"); }} />}
      {pw && <Dialog title={`Set a password for ${pw.display_name}`} onClose={() => setPw(null)} footer={<><button className="btn btn-ghost" onClick={() => setPw(null)}>Cancel</button>
        <button className="btn btn-primary" disabled={password.length < 10} onClick={() => api(`/users/${pw.id}/set_password/`, { method: "POST", body: { password } }).then(() => { setPw(null); toast("Password set. They are signed out everywhere."); }).catch((e) => toast(e.message))}>Set password</button></>}>
        <Field label="New password" id="new-pw" hint="At least 10 characters. Send it privately."><input id="new-pw" className="input" type="text" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} /></Field></Dialog>}
      {suspend && <Confirm title={suspend.is_suspended ? `Restore ${suspend.display_name}?` : `Suspend ${suspend.display_name}?`} danger={!suspend.is_suspended}
        message={suspend.is_suspended ? "They can sign in again." : "They are signed out at once and cannot sign in. Their records and history stay."}
        confirmLabel={suspend.is_suspended ? "Restore" : "Suspend"} onClose={() => setSuspend(null)}
        onConfirm={() => api(`/users/${suspend.id}/suspend/`, { method: "POST" }).then(() => { setReload((n) => n + 1); toast("Done"); })} />}
    </div>
  );
}
