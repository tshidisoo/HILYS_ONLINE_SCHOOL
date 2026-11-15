import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import { Dialog, Empty, Field, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";

function ContentForm({ item, onClose, onDone }) {
  const { user } = useAuth();
  const f = useForm(item || { kind: "announcement", title: "", body: "", author: "", is_published: false, sort_order: 0 });
  return (
    <Dialog title={item ? "Edit website content" : "Add website content"} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !f.values.title} onClick={() => f.submit(async (v) => onDone(item ? await api(`/site-content/${item.id}/`, { method: "PATCH", body: v }) : await api("/site-content/", { method: "POST", body: v })))}>Save</button></>}>
      <Field label="Type" id="kind"><select className="input" {...f.bind("kind")}><option value="announcement">Announcement</option><option value="testimonial">Parent review</option><option value="faq">Question and answer</option></select></Field>
      <Field label={f.values.kind === "faq" ? "Question" : "Title"} id="title" error={f.errors.title}><input className="input" {...f.bind("title")} /></Field>
      <Field label={f.values.kind === "faq" ? "Answer" : "Text"} id="body"><textarea className="input" {...f.bind("body")} /></Field>
      {f.values.kind === "testimonial" && <Field label="Who said it" id="author" hint="First name and city only, and only with the parent's permission."><input className="input" {...f.bind("author")} /></Field>}
      <label className="check"><input type="checkbox" checked={!!f.values.is_published} onChange={f.set("is_published")} disabled={!user.permissions.is_leadership} /> Show on the website {user.permissions.is_leadership ? "" : "(the owner publishes)"}</label>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Website() {
  const toast = useToast();
  const [edit, setEdit] = useState(null);
  const [reload, setReload] = useState(0);
  return (
    <div className="page">
      <div className="page-head"><div><h1>Website content</h1><p>Announcements, parent reviews and questions shown on the website. Website enquiries arrive as leads.</p></div><div className="spacer" /><button className="btn btn-primary" onClick={() => setEdit({})}>Add content</button></div>
      <DataTable path="/site-content/" reloadKey={reload} onOpen={setEdit} filters={[{ key: "kind", label: "Type", options: [["announcement", "Announcement"], ["testimonial", "Parent review"], ["faq", "Question and answer"]] }]}
        empty={<Empty title="No website content yet" action={<button className="btn btn-primary btn-sm" onClick={() => setEdit({})}>Add content</button>} />}
        columns={[{ key: "title", label: "Title", render: (r) => <span className="cell-main">{r.title}</span> }, { key: "kind_label", label: "Type" }, { key: "author", label: "Who said it" },
          { key: "is_published", label: "", render: (r) => r.is_published ? <Pill tone="good">On the website</Pill> : <Pill tone="neutral">Not published</Pill> }]} />
      {edit && <ContentForm item={edit.id ? edit : null} onClose={() => setEdit(null)} onDone={() => { setEdit(null); setReload((n) => n + 1); toast("Saved"); }} />}
    </div>
  );
}
