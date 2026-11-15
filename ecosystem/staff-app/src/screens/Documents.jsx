import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, openPdf } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import { useOpenParam, useRecord } from "../components/hooks";
import { useLookup } from "../components/lookups";
import { Confirm, DL, Dialog, Empty, ErrorState, Field, Loading, Panel, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { date, money } from "../format";
import "./Documents.css";

const KINDS = [["invoice", "Invoice"], ["quotation", "Quotation"], ["receipt", "Receipt"], ["credit_note", "Credit note"], ["payment_plan", "Payment plan"], ["statement", "Statement"], ["agreement", "Enrolment agreement"]];
const STATUS = [["draft", "Draft"], ["issued", "Issued"], ["part_paid", "Part paid"], ["paid", "Paid"], ["accepted", "Accepted"], ["cancelled", "Cancelled"]];

function LinesEditor({ lines, setLines, currency }) {
  const items = useLookup("packages");
  const update = (i, k, v) => setLines(lines.map((l, j) => (j === i ? { ...l, [k]: v } : l)));
  const pick = (i, id) => { const it = items.find((x) => String(x.id) === id); if (it) setLines(lines.map((l, j) => (j === i ? { ...l, item: it.id, description: it.name, unit_price: it.price } : l))); };
  const total = lines.reduce((s, l) => s + Number(l.quantity || 0) * Number(l.unit_price || 0), 0);
  return (
    <div className="lines">
      <div className="line line-head" aria-hidden="true"><span>From the price book</span><span>Description</span><span>Qty</span><span>Price</span><span /></div>
      {lines.map((l, i) => (
        <div key={i} className="line">
          <select aria-label="From the price book" className="input" value={l.item || ""} onChange={(e) => pick(i, e.target.value)}><option value="">Choose…</option>{items.map((it) => <option key={it.id} value={it.id}>{it.name}</option>)}</select>
          <input aria-label="Description" className="input" value={l.description} onChange={(e) => update(i, "description", e.target.value)} />
          <input aria-label="Quantity" className="input" type="number" min="0" step="0.5" value={l.quantity} onChange={(e) => update(i, "quantity", e.target.value)} />
          <input aria-label="Price" className="input" type="number" min="0" step="0.01" value={l.unit_price} onChange={(e) => update(i, "unit_price", e.target.value)} />
          <button type="button" className="icon-btn" aria-label="Remove line" onClick={() => setLines(lines.filter((_, j) => j !== i))}>×</button>
        </div>
      ))}
      <div className="row"><button type="button" className="btn btn-ghost btn-sm" onClick={() => setLines([...lines, { item: "", description: "", quantity: 1, unit_price: "" }])}>Add a line</button><div className="spacer" /><strong>Total {money(total, currency)}</strong></div>
    </div>
  );
}

function NewDocument({ kind, familyId, onClose, onDone }) {
  const families = useLookup("families");
  const f = useForm({ kind, family: familyId || "", period: new Date().toISOString().slice(0, 7), currency: "USD", notes: "" });
  const [lines, setLines] = useState([{ item: "", description: "", quantity: 1, unit_price: "" }]);
  const hasLines = ["invoice", "quotation"].includes(f.values.kind);
  const save = () => f.submit(async (v) => onDone(await api("/documents/", { method: "POST", body: { ...v, lines: hasLines ? lines.filter((l) => l.description && l.unit_price !== "") : [] } })));
  return (
    <Dialog title="New document" wide onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy || !f.values.family} onClick={save}>Save as draft</button></>}>
      <div className="form-grid">
        <Field label="Type" id="kind"><select className="input" {...f.bind("kind")}>{KINDS.filter(([k]) => ["invoice", "quotation", "agreement"].includes(k)).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></Field>
        <Field label="Family" id="family" error={f.errors.family}><select className="input" {...f.bind("family")}><option value="">Choose…</option>{families.map((x) => <option key={x.id} value={x.id}>{x.parent_name}</option>)}</select></Field>
        {f.values.kind === "invoice" && <Field label="For the month" id="period" hint="Packages are paid at the start of each month."><input className="input" type="month" {...f.bind("period")} /></Field>}
        <Field label="Currency" id="currency"><select className="input" {...f.bind("currency")}><option>USD</option><option>GBP</option><option>ZAR</option></select></Field>
      </div>
      {hasLines && <LinesEditor lines={lines} setLines={setLines} currency={f.values.currency} />}
      {f.values.kind === "agreement" && <p className="muted" style={{ margin: 0 }}>The agreement uses HILYS's standard terms. They are a draft until the owner approves them and a lawyer has checked them.</p>}
      <Field label="Note on the document" id="notes"><textarea className="input" {...f.bind("notes")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function AmountDialog({ title, label, onClose, onSubmit, withReason, parts }) {
  const f = useForm({ amount: "", reason: "", parts: 3 });
  return (
    <Dialog title={title} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={f.busy} onClick={() => f.submit(onSubmit)}>Save as draft</button></>}>
      {parts ? <Field label="How many instalments?" id="parts" hint="Due a month apart, from today."><select className="input" {...f.bind("parts")}>{[2, 3, 4, 5, 6].map((n) => <option key={n}>{n}</option>)}</select></Field>
        : <Field label={label} id="amount" error={f.errors.amount}><input className="input" type="number" min="0" step="0.01" {...f.bind("amount")} /></Field>}
      {withReason && <Field label="Why?" id="reason" hint="Printed on the credit note."><textarea className="input" {...f.bind("reason")} /></Field>}
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function DocumentPanel({ id, onClose, onChanged, onOpenOther }) {
  const toast = useToast();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: d, setData, reload, error } = useRecord(`/documents/${id}/`);
  const [dialog, setDialog] = useState(null);
  const [lines, setLines] = useState(null);
  const [actionError, setActionError] = useState("");
  if (error) return <Panel title="Document" onClose={onClose}><ErrorState error={error} onRetry={reload} /></Panel>;
  if (!d) return <Panel title="Document" onClose={onClose}><Loading /></Panel>;
  const run = async (fn, msg, openNew) => {
    setActionError("");
    try { const r = await fn(); onChanged(); toast(msg); if (openNew && r?.id && r.id !== d.id) onOpenOther(r.id); else if (r?.id) setData(r); else reload(); }
    catch (e) { setActionError(e.message); }
  };
  const draft = d.status === "draft";
  const editLines = lines ?? d.lines.map((l) => ({ ...l, item: l.item || "" }));
  return (
    <Panel title={`${d.kind_label} ${d.number || "(draft)"}`} subtitle={d.family_name} onClose={onClose}
      actions={<>
        {d.number && <button className="btn btn-ghost btn-sm" onClick={() => openPdf(`/documents/${d.id}/pdf/`).catch((e) => setActionError(e.message))}>Open PDF</button>}
        {!d.number && d.kind !== "receipt" && <button className="btn btn-ghost btn-sm" onClick={() => openPdf(`/documents/${d.id}/pdf/`).catch((e) => setActionError(e.message))}>Preview</button>}
        {draft && <button className="btn btn-primary btn-sm" onClick={() => setDialog("issue")}>Issue</button>}
        {d.kind === "quotation" && ["issued", "accepted"].includes(d.status) && <button className="btn btn-primary btn-sm" onClick={() => run(() => api(`/documents/${d.id}/to_invoice/`, { method: "POST" }), "Draft invoice made", true)}>Turn into invoice</button>}
        {d.kind === "invoice" && ["issued", "part_paid"].includes(d.status) && user.permissions.can_record_payments && <button className="btn btn-primary btn-sm" onClick={() => navigate(`/payments?new=1&family=${d.family}&invoice=${d.id}`)}>Record payment</button>}
        {d.kind === "invoice" && ["issued", "part_paid", "paid"].includes(d.status) && <button className="btn btn-ghost btn-sm" onClick={() => setDialog("credit")}>Credit note</button>}
        {d.kind === "invoice" && ["issued", "part_paid"].includes(d.status) && <button className="btn btn-ghost btn-sm" onClick={() => setDialog("plan")}>Payment plan</button>}
        {d.status !== "cancelled" && d.kind !== "receipt" && (draft || user.permissions.can_override_rules) && <button className="btn btn-danger btn-sm" onClick={() => setDialog("cancel")}>Cancel</button>}
      </>}>
      {actionError && <div className="form-error" role="alert">{actionError}</div>}
      <div className="row"><Pill status={d.is_overdue ? "overdue" : d.status}>{d.is_overdue ? "Overdue" : d.status_label}</Pill>{d.is_demo && <span className="demo-tag">DEMO</span>}</div>
      <DL rows={[["Family", d.family_name], ["Date", date(d.issue_date)], d.kind === "invoice" && ["Due", date(d.due_date)], d.kind === "quotation" && ["Valid until", date(d.due_date)],
        d.period && ["For the month", d.period], d.related_number && ["Linked to", d.related_number], ["Total", money(d.total, d.currency)],
        d.paid !== null && ["Paid", money(d.paid, d.currency)], d.outstanding !== null && ["Still to pay", money(d.outstanding, d.currency)],
        d.number && ["Check code", d.verify_code], d.amended_reason && ["Amended", d.amended_reason], d.notes && ["Note", d.notes]]} />
      {d.installments.length > 0 && <><h3>Instalments</h3><ul>{d.installments.map((i, n) => <li key={n}>{date(i.due_date)}: {money(i.amount, d.currency)}</li>)}</ul></>}
      {["invoice", "quotation", "credit_note"].includes(d.kind) && (draft ? <>
        <h3>Lines</h3><LinesEditor lines={editLines} setLines={setLines} currency={d.currency} />
        {lines && <button className="btn btn-primary btn-sm" onClick={() => run(() => api(`/documents/${d.id}/`, { method: "PATCH", body: { lines: lines.filter((l) => l.description) } }).then((r) => { setLines(null); return r; }), "Lines saved")}>Save lines</button>}
      </> : <table className="doc-lines"><thead><tr><th>Description</th><th className="num">Qty</th><th className="num">Price</th><th className="num">Amount</th></tr></thead>
        <tbody>{d.lines.map((l) => <tr key={l.id}><td>{l.description}{l.student_name && <div className="cell-sub">{l.student_name}</div>}</td><td className="num">{Number(l.quantity)}</td><td className="num">{money(l.unit_price, d.currency)}</td><td className="num">{money(l.amount, d.currency)}</td></tr>)}</tbody></table>)}
      {!draft && d.kind !== "receipt" && <p className="muted">Issued documents are locked. Use a credit note to reduce what is owed, or ask the owner to amend it.</p>}

      {dialog === "issue" && <Confirm title={`Issue this ${d.kind_label.toLowerCase()}?`} message="It gets its number and is locked. The family can see it in their app." confirmLabel="Issue" onClose={() => setDialog(null)}
        onConfirm={() => api(`/documents/${d.id}/issue/`, { method: "POST" }).then((r) => { setData(r); onChanged(); toast(`Issued ${r.number}`); })} />}
      {dialog === "cancel" && <Confirm title="Cancel this document?" message={draft ? "The draft is cancelled. Nothing was sent to the family." : "It stays on record marked Cancelled, and the check page says it is no longer valid."} needReason={draft ? undefined : "Why?"} danger confirmLabel="Cancel document"
        onClose={() => setDialog(null)} onConfirm={(reason) => api(`/documents/${d.id}/cancel/`, { method: "POST", body: { reason } }).then((r) => { setData(r); onChanged(); toast("Cancelled"); })} />}
      {dialog === "credit" && <AmountDialog title="Credit note" label={`Amount to credit (${d.currency})`} withReason onClose={() => setDialog(null)}
        onSubmit={(v) => api(`/documents/${d.id}/credit/`, { method: "POST", body: { amount: v.amount, reason: v.reason } }).then((r) => { setDialog(null); onChanged(); onOpenOther(r.id); })} />}
      {dialog === "plan" && <AmountDialog title="Payment plan" parts onClose={() => setDialog(null)}
        onSubmit={(v) => api(`/documents/${d.id}/plan/`, { method: "POST", body: { parts: v.parts } }).then((r) => { setDialog(null); onChanged(); onOpenOther(r.id); })} />}
    </Panel>
  );
}

function MonthlyInvoices({ onClose, onDone }) {
  const next = new Date(); next.setMonth(next.getMonth() + 1);
  const f = useForm({ period: next.toISOString().slice(0, 7) });
  return (
    <Dialog title="Draft next month's invoices" onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy} onClick={() => f.submit(async (v) => onDone(await api("/documents/monthly_invoices/", { method: "POST", body: v })))}>Draft invoices</button></>}>
      <p style={{ margin: 0 }}>One draft invoice per family with an active enrolment, from their packages. Families who already have an invoice for the month are skipped. Check the drafts, then issue them.</p>
      <Field label="Month" id="period"><input className="input" type="month" {...f.bind("period")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Documents() {
  const params = new URLSearchParams(window.location.search);
  const [open, setOpen] = useState(useOpenParam());
  const [creating, setCreating] = useState(params.get("new") ? { kind: params.get("new"), family: params.get("family") } : null);
  const [monthly, setMonthly] = useState(false);
  const [reload, setReload] = useState(0);
  const toast = useToast();
  const bump = () => setReload((n) => n + 1);
  return (
    <div className="page">
      <div className="page-head"><div><h1>Documents</h1><p>Quotations, invoices, receipts, credit notes, payment plans, statements and agreements.</p></div><div className="spacer" />
        <button className="btn btn-ghost" onClick={() => setMonthly(true)}>Draft monthly invoices</button>
        <button className="btn btn-primary" onClick={() => setCreating({ kind: "invoice" })}>New document</button></div>
      <DataTable path="/documents/" reloadKey={reload} onOpen={(r) => setOpen(r.id)} searchLabel="Search numbers or families"
        initial={{ kind: params.get("kind") || "", status: params.get("status") || "", overdue: params.get("overdue") || "", ordering: "-created_at" }}
        filters={[{ key: "kind", label: "Type", options: KINDS }, { key: "status", label: "Status", options: STATUS }, { key: "overdue", label: "Overdue", options: [["1", "Overdue only"]] }]}
        empty={<Empty title="No documents yet" action={<button className="btn btn-primary btn-sm" onClick={() => setCreating({ kind: "invoice" })}>New document</button>}>Receipts are made for you when a payment is recorded.</Empty>}
        columns={[
          { key: "number", label: "Document", render: (r) => <><div className="cell-main">{r.kind_label} {r.number || "(draft)"} {r.is_demo && <span className="demo-tag">DEMO</span>}</div><div className="cell-sub">{r.period}</div></> },
          { key: "family_name", label: "Family" },
          { key: "issue_date", label: "Date", sort: "issue_date", render: (r) => date(r.issue_date) },
          { key: "total", label: "Total", sort: "total", align: "right", render: (r) => money(r.total, r.currency) },
          { key: "outstanding", label: "Still to pay", align: "right", render: (r) => r.outstanding !== null ? money(r.outstanding, r.currency) : "—" },
          { key: "status", label: "Status", render: (r) => <Pill status={r.is_overdue ? "overdue" : r.status}>{r.is_overdue ? "Overdue" : r.status_label}</Pill> },
        ]} />
      {open && <DocumentPanel key={open} id={open} onClose={() => setOpen(null)} onChanged={bump} onOpenOther={setOpen} />}
      {creating && <NewDocument kind={creating.kind} familyId={creating.family} onClose={() => setCreating(null)} onDone={(r) => { setCreating(null); bump(); setOpen(r.id); }} />}
      {monthly && <MonthlyInvoices onClose={() => setMonthly(false)} onDone={(r) => { setMonthly(false); bump(); toast(`${r.created} draft invoices made`); }} />}
    </div>
  );
}
