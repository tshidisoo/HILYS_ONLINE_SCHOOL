import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, openPdf } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import { useData } from "../components/hooks";
import { useLookup } from "../components/lookups";
import { Confirm, DL, Dialog, Empty, Field, Panel, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { date, money } from "../format";

const METHODS = [["mukuru", "Mukuru"], ["ecocash", "EcoCash Diaspora"], ["western_union", "Western Union"], ["bank", "Bank transfer"], ["cash", "Cash"]];

function InvoicePicker({ familyId, currency, allocations, setAllocations, preselect }) {
  const { data } = useData(familyId ? `/documents/?family=${familyId}&kind=invoice&currency=${currency}&page_size=50` : null);
  const open = (data?.results || []).filter((d) => ["issued", "part_paid"].includes(d.status));
  if (!familyId) return null;
  if (data && open.length === 0) return <p className="muted" style={{ margin: 0 }}>This family has no unpaid {currency} invoices. The payment is kept as paid ahead.</p>;
  const amountFor = (id) => allocations[id] ?? "";
  return (
    <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
      <legend style={{ fontWeight: 600, marginBottom: 6 }}>Which invoices does it pay?</legend>
      <p className="muted" style={{ margin: "0 0 8px" }}>Leave all empty to pay the oldest invoices first.</p>
      {open.map((d) => (
        <div key={d.id} className="row" style={{ marginBottom: 6 }}>
          <label htmlFor={`a-${d.id}`} style={{ flex: 1 }}>{d.number} · {d.period || date(d.issue_date)} · still to pay {money(d.outstanding, d.currency)}{String(d.id) === String(preselect) ? " (this one)" : ""}</label>
          <input id={`a-${d.id}`} className="input" style={{ width: 120 }} type="number" min="0" step="0.01" value={amountFor(d.id)}
                 onChange={(e) => setAllocations({ ...allocations, [d.id]: e.target.value })} placeholder="0.00" />
          <button type="button" className="link-btn" onClick={() => setAllocations({ ...allocations, [d.id]: d.outstanding })}>All</button>
        </div>
      ))}
    </fieldset>
  );
}

function RecordPayment({ familyId, invoiceId, onClose, onDone }) {
  const families = useLookup("families");
  const today = new Date().toISOString().slice(0, 10);
  const f = useForm({ family: familyId || "", amount: "", currency: "USD", method: "mukuru", reference: "", received_on: today, note: "" });
  const [alloc, setAlloc] = useState({});
  const chosen = Object.entries(alloc).filter(([, v]) => Number(v) > 0).map(([invoice, amount]) => ({ invoice: Number(invoice), amount }));
  const save = () => f.submit(async (v) => onDone(await api("/payments/", { method: "POST", body: { ...v, allocations: chosen.length ? chosen : undefined } })));
  return (
    <Dialog title="Record a payment" wide onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !f.values.family || !Number(f.values.amount)} onClick={save}>{f.busy ? "Saving…" : "Record and make receipt"}</button></>}>
      <div className="form-grid">
        <Field label="Family" id="family" error={f.errors.family}><select className="input" {...f.bind("family")}><option value="">Choose…</option>{families.map((x) => <option key={x.id} value={x.id}>{x.parent_name}</option>)}</select></Field>
        <Field label="How they paid" id="method" error={f.errors.method}><select className="input" {...f.bind("method")}>{METHODS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></Field>
        <Field label="Amount" id="amount" error={f.errors.amount}><input className="input" type="number" min="0" step="0.01" {...f.bind("amount")} /></Field>
        <Field label="Currency" id="currency"><select className="input" {...f.bind("currency")}><option>USD</option><option>GBP</option><option>ZAR</option></select></Field>
        <Field label="Reference" id="reference" hint="The Mukuru, EcoCash or Western Union code the parent sent." error={f.errors.reference}><input className="input" {...f.bind("reference")} /></Field>
        <Field label="Received on" id="received_on" error={f.errors.received_on}><input className="input" type="date" max={today} {...f.bind("received_on")} /></Field>
      </div>
      <InvoicePicker familyId={f.values.family} currency={f.values.currency} allocations={alloc} setAllocations={setAlloc} preselect={invoiceId} />
      <Field label="Note" id="note"><input className="input" {...f.bind("note")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function PaymentPanel({ payment: p, onClose, onChanged }) {
  const toast = useToast();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [dialog, setDialog] = useState(null);
  const [alloc, setAlloc] = useState({});
  const [err, setErr] = useState("");
  const chosen = Object.entries(alloc).filter(([, v]) => Number(v) > 0).map(([invoice, amount]) => ({ invoice: Number(invoice), amount }));
  return (
    <Panel title={money(p.amount, p.currency)} subtitle={`${p.family_name} · ${p.method_label}`} onClose={onClose}
      actions={<>
        {p.receipt_id && <button className="btn btn-ghost btn-sm" onClick={() => openPdf(`/documents/${p.receipt_id}/pdf/`).catch((e) => setErr(e.message))}>Receipt PDF</button>}
        <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/families?open=${p.family}`)}>Family</button>
        {!p.reversed_at && user.permissions.can_record_payments && <button className="btn btn-danger btn-sm" onClick={() => setDialog("reverse")}>Reverse payment</button>}
      </>}>
      {err && <div className="form-error" role="alert">{err}</div>}
      <div className="row">{p.reversed_at ? <Pill status="cancelled">Reversed</Pill> : Number(p.unallocated) > 0 ? <Pill tone="warn">Not fully matched</Pill> : <Pill status="paid">Matched</Pill>}</div>
      <DL rows={[["Received", date(p.received_on)], ["Reference", p.reference], ["Recorded by", p.recorded_by_name], ["Not matched yet", money(p.unallocated, p.currency)],
        ["Note", p.note], p.reversed_at && ["Reversed because", p.reversed_reason]]} />
      <h3>Pays these invoices</h3>
      {p.allocations.length === 0 ? <p className="muted">Not matched to any invoice.</p> : <ul>{p.allocations.map((a) => <li key={a.invoice}>{a.invoice_number}: {money(a.amount, p.currency)}</li>)}</ul>}
      {!p.reversed_at && Number(p.unallocated) > 0 && user.permissions.can_record_payments && <div className="card card-tight stack">
        <InvoicePicker familyId={p.family} currency={p.currency} allocations={alloc} setAllocations={setAlloc} />
        <button className="btn btn-primary btn-sm" style={{ justifySelf: "start" }} disabled={!chosen.length}
          onClick={() => api(`/payments/${p.id}/allocate/`, { method: "POST", body: { allocations: chosen } }).then(() => { onChanged(); toast("Matched"); onClose(); }).catch((e) => setErr(e.message))}>Match to invoices</button>
      </div>}
      {dialog === "reverse" && <Confirm title="Reverse this payment?" message="The invoices it paid go back to unpaid or part paid, and its receipt is cancelled. Use this when money was recorded by mistake or bounced." needReason="Why?" danger confirmLabel="Reverse payment"
        onClose={() => setDialog(null)} onConfirm={(reason) => api(`/payments/${p.id}/reverse/`, { method: "POST", body: { reason } }).then(() => { onChanged(); toast("Payment reversed"); onClose(); })} />}
    </Panel>
  );
}

export default function Payments() {
  const params = new URLSearchParams(window.location.search);
  const { user } = useAuth();
  const [open, setOpen] = useState(null);
  const [recording, setRecording] = useState(params.get("new") ? { family: params.get("family"), invoice: params.get("invoice") } : null);
  const [reload, setReload] = useState(0);
  const toast = useToast();
  const canRecord = user.permissions.can_record_payments;
  return (
    <div className="page">
      <div className="page-head"><div><h1>Payments desk</h1><p>{canRecord ? "Record money received and match it to invoices. A receipt is made each time." : "Only finance and the owner record payments. You can see them here."}</p></div><div className="spacer" />
        {canRecord && <button className="btn btn-primary" onClick={() => setRecording({})}>Record a payment</button>}</div>
      <DataTable path="/payments/" reloadKey={reload} onOpen={setOpen} searchLabel="Search references or families" initial={{ unmatched: params.get("unmatched") || "", ordering: "-received_on" }}
        filters={[{ key: "method", label: "Method", options: METHODS }, { key: "unmatched", label: "Matching", options: [["1", "Not matched to an invoice"]] }]}
        empty={<Empty title="No payments recorded yet">{canRecord ? "Record a payment when a family sends money." : "Finance records payments here."}</Empty>}
        columns={[
          { key: "received_on", label: "Received", sort: "received_on", render: (r) => date(r.received_on) },
          { key: "family_name", label: "Family", render: (r) => <><div className="cell-main">{r.family_name} {r.is_demo && <span className="demo-tag">DEMO</span>}</div><div className="cell-sub">{r.method_label} {r.reference}</div></> },
          { key: "amount", label: "Amount", sort: "amount", align: "right", render: (r) => money(r.amount, r.currency) },
          { key: "allocations", label: "Pays", render: (r) => r.allocations.map((a) => a.invoice_number).join(", ") || "—" },
          { key: "state", label: "", render: (r) => r.reversed_at ? <Pill status="cancelled">Reversed</Pill> : Number(r.unallocated) > 0 ? <Pill tone="warn">Not matched</Pill> : <Pill status="paid">Matched</Pill> },
        ]} />
      {open && <PaymentPanel payment={open} onClose={() => setOpen(null)} onChanged={() => setReload((n) => n + 1)} />}
      {recording && <RecordPayment familyId={recording.family} invoiceId={recording.invoice} onClose={() => setRecording(null)} onDone={() => { setRecording(null); setReload((n) => n + 1); toast("Payment recorded and receipt made"); }} />}
    </div>
  );
}
