import { useEffect } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { useData } from "../components/hooks";
import { ErrorState, Field, Loading, useToast } from "../components/ui";
import { useForm } from "../components/useForm";

export default function Settings() {
  const { user } = useAuth();
  const toast = useToast();
  const { data, loading, error, reload } = useData("/settings/");
  const f = useForm({});
  useEffect(() => { if (data) f.setValues(data); }, [data]); // eslint-disable-line react-hooks/exhaustive-deps
  const pw = useForm({ current_password: "", new_password: "" });
  if (loading && !data) return <div className="page"><Loading /></div>;
  if (error) return <div className="page"><ErrorState error={error} onRetry={reload} /></div>;
  const ro = !user.permissions.is_leadership;
  const prefixes = ["invoice", "quotation", "receipt", "credit_note", "payment_plan", "statement", "agreement", "certificate"];
  return (
    <div className="page">
      <div className="page-head"><div><h1>Company settings</h1><p>{ro ? "Only the owner can change these." : "Used on documents, the website and reminders."}</p></div></div>
      <div className="stack" style={{ maxWidth: 860 }}>
        <section className="card stack"><h2>Company</h2><div className="form-grid">
          <Field label="Name" id="name"><input className="input" {...f.bind("name")} disabled={ro} /></Field>
          <Field label="Short name" id="short_name"><input className="input" {...f.bind("short_name")} disabled={ro} /></Field>
          <Field label="Email on documents" id="email"><input className="input" type="email" {...f.bind("email")} disabled={ro} /></Field>
          <Field label="WhatsApp on documents" id="whatsapp"><input className="input" {...f.bind("whatsapp")} disabled={ro} /></Field>
          <Field label="Website" id="website"><input className="input" {...f.bind("website")} disabled={ro} /></Field>
          <Field label="Motto" id="motto"><input className="input" {...f.bind("motto")} disabled={ro} /></Field>
          <Field label="How to pay (printed on invoices)" id="payment_details" wide><textarea className="input" {...f.bind("payment_details")} disabled={ro} /></Field></div>
          <p className="muted" style={{ margin: 0 }}>HILYS has no physical address, so documents show email, WhatsApp and the website only.</p></section>
        <section className="card stack"><h2>Documents and reminders</h2><div className="form-grid">
          {prefixes.map((p) => <Field key={p} label={`${p.replace("_", " ")} number prefix`} id={`${p}_prefix`}><input className="input" {...f.bind(`${p}_prefix`)} disabled={ro} /></Field>)}
          <Field label="Days to pay an invoice" id="invoice_due_days"><input className="input" type="number" min="0" {...f.bind("invoice_due_days")} disabled={ro} /></Field>
          <Field label="Days a quotation is valid" id="quotation_valid_days"><input className="input" type="number" min="0" {...f.bind("quotation_valid_days")} disabled={ro} /></Field></div></section>
        <section className="card stack"><h2>Privacy</h2><Field label="How long we keep data" id="retention_notes" hint="A draft until the owner and a lawyer approve it."><textarea className="input" rows={6} {...f.bind("retention_notes")} disabled={ro} /></Field></section>
        {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
        {!ro && <button className="btn btn-primary" style={{ justifySelf: "start" }} disabled={f.busy} onClick={() => f.submit(async (v) => { const r = await api("/settings/", { method: "PATCH", body: v }); f.setValues(r); toast("Settings saved"); })}>Save settings</button>}
        <section className="card stack"><h2>My password</h2><div className="form-grid">
          <Field label="Current password" id="current_password" error={pw.errors.current_password}><input className="input" type="password" autoComplete="current-password" {...pw.bind("current_password")} /></Field>
          <Field label="New password" id="new_password" hint="At least 10 characters." error={pw.errors.new_password}><input className="input" type="password" autoComplete="new-password" {...pw.bind("new_password")} /></Field></div>
          <button className="btn btn-ghost" style={{ justifySelf: "start" }} disabled={pw.busy || !pw.values.new_password} onClick={() => pw.submit(async (v) => { const r = await api("/auth/password/", { method: "POST", body: v }); localStorage.setItem("hilys-staff-token", r.token); pw.setValues({ current_password: "", new_password: "" }); toast("Password changed"); })}>Change password</button></section>
      </div>
    </div>
  );
}
