import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import { clearLookup } from "../components/lookups";
import { Dialog, Field, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { money } from "../format";

function ItemForm({ item, onClose, onDone }) {
  const f = useForm(item || { name: "", description: "", kind: "package", lesson_type: "one_to_one", lessons_per_week: 1, price: "", currency: "USD", unit: "per month", is_active: true, on_website: true, is_draft_price: true });
  return (
    <Dialog title={item ? `Edit ${item.name}` : "Add to the price book"} wide onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !f.values.name} onClick={() => f.submit(async (v) => { const r = item ? await api(`/catalogue/${item.id}/`, { method: "PATCH", body: v }) : await api("/catalogue/", { method: "POST", body: v }); clearLookup("packages"); onDone(r); })}>Save</button></>}>
      <div className="form-grid">
        <Field label="Name" id="name" error={f.errors.name}><input className="input" {...f.bind("name")} /></Field>
        <Field label="Type" id="kind"><select className="input" {...f.bind("kind")}><option value="package">Monthly lesson package</option><option value="lesson">Single lesson</option><option value="course">Video course</option><option value="trial">Trial lesson</option><option value="other">Other</option></select></Field>
        <Field label="Lesson type" id="lesson_type"><select className="input" {...f.bind("lesson_type")}><option value="one_to_one">One-to-one</option><option value="group">Group (up to 3)</option><option value="">Not a lesson</option></select></Field>
        <Field label="Lessons a week" id="lessons_per_week" hint="A month counts as 4 lessons per weekly slot."><input className="input" type="number" min="0" {...f.bind("lessons_per_week")} /></Field>
        <Field label="Price" id="price" error={f.errors.price}><input className="input" type="number" min="0" step="0.01" {...f.bind("price")} /></Field>
        <Field label="Currency" id="currency"><select className="input" {...f.bind("currency")}><option>USD</option><option>GBP</option><option>ZAR</option></select></Field>
        <Field label="Unit" id="unit"><input className="input" {...f.bind("unit")} /></Field>
        <Field label="Description" id="description" wide><textarea className="input" {...f.bind("description")} /></Field>
        <label className="check"><input type="checkbox" checked={!!f.values.is_active} onChange={f.set("is_active")} /> Can be sold</label>
        <label className="check"><input type="checkbox" checked={!!f.values.on_website} onChange={f.set("on_website")} /> Shown on the website</label>
        <label className="check wide"><input type="checkbox" checked={!!f.values.is_draft_price} onChange={f.set("is_draft_price")} /> Draft price: not yet approved by the owner</label>
      </div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function PriceBook() {
  const { user } = useAuth();
  const toast = useToast();
  const [edit, setEdit] = useState(null);
  const [reload, setReload] = useState(0);
  return (
    <div className="page">
      <div className="page-head"><div><h1>Price book</h1><p>The only place prices are typed. Invoices and quotations pick from here.</p></div><div className="spacer" />
        <button className="btn btn-primary" onClick={() => setEdit({})}>Add an item</button></div>
      <DataTable path="/catalogue/" reloadKey={reload} onOpen={setEdit} initial={{ ordering: "sort_order" }}
        filters={[{ key: "kind", label: "Type", options: [["package", "Monthly package"], ["lesson", "Single lesson"], ["course", "Video course"], ["trial", "Trial"]] }, { key: "is_active", label: "Status", options: [["true", "Can be sold"], ["false", "Retired"]] }]}
        columns={[{ key: "name", label: "Item", sort: "name", render: (r) => <><div className="cell-main">{r.name}</div><div className="cell-sub">{r.kind_label}{r.lesson_type_label && r.lesson_type ? ` · ${r.lesson_type_label}` : ""}</div></> },
          { key: "price", label: "Price", sort: "price", align: "right", render: (r) => `${money(r.price, r.currency)} ${r.unit}` },
          { key: "flags", label: "", render: (r) => <>{r.is_draft_price && <Pill tone="warn">Draft price</Pill>}{!r.is_active && <Pill tone="neutral">Retired</Pill>}{r.on_website && <Pill tone="info">On website</Pill>}</> }]} />
      {edit && <ItemForm item={edit.id ? edit : null} onClose={() => setEdit(null)} onDone={() => { setEdit(null); setReload((n) => n + 1); toast("Saved"); }} />}
      {!user.permissions.is_leadership && <p className="muted" style={{ marginTop: 12 }}>Price changes are recorded in the audit log.</p>}
    </div>
  );
}
