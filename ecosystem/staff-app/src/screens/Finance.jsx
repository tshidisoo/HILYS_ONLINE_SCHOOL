import { useState } from "react";
import { api } from "../api";
import DataTable from "../components/DataTable";
import { ColumnChart } from "../components/Charts";
import { useData } from "../components/hooks";
import { Dialog, ErrorState, Field, Loading, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { date, money } from "../format";
import "./Finance.css";

function EntryForm({ accounts, categories, kind, onClose, onDone }) {
  const f = useForm({ account: accounts[0]?.id || "", kind, amount: "", category: kind === "expense" ? "Internet and data" : "Other", on_date: new Date().toISOString().slice(0, 10), note: "" });
  return (
    <Dialog title={kind === "expense" ? "Record money out" : "Record other money in"} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !Number(f.values.amount)} onClick={() => f.submit(async (v) => onDone(await api("/finance/entries/", { method: "POST", body: v })))}>Save</button></>}>
      <div className="form-grid">
        <Field label="Account" id="account"><select className="input" {...f.bind("account")}>{accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></Field>
        <Field label="Amount" id="amount" error={f.errors.amount}><input className="input" type="number" min="0" step="0.01" {...f.bind("amount")} /></Field>
        <Field label="Category" id="category"><select className="input" {...f.bind("category")}>{categories.map((c) => <option key={c}>{c}</option>)}</select></Field>
        <Field label="Date" id="on_date"><input className="input" type="date" {...f.bind("on_date")} /></Field>
        <Field label="What for" id="note" wide><input className="input" {...f.bind("note")} /></Field>
      </div>
      <p className="muted" style={{ margin: 0 }}>Payments from families are added here automatically when they are recorded on the payments desk.</p>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

function Transfer({ accounts, onClose, onDone }) {
  const f = useForm({ from_account: accounts[0]?.id || "", to_account: accounts[1]?.id || "", amount: "", on_date: new Date().toISOString().slice(0, 10), note: "" });
  return (
    <Dialog title="Move money between accounts" onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !Number(f.values.amount)} onClick={() => f.submit(async (v) => { await api("/finance/accounts/transfer/", { method: "POST", body: v }); onDone(); })}>Move money</button></>}>
      <div className="form-grid">
        <Field label="From" id="from_account"><select className="input" {...f.bind("from_account")}>{accounts.map((a) => <option key={a.id} value={a.id}>{a.name} ({a.currency})</option>)}</select></Field>
        <Field label="To" id="to_account" error={f.errors.to_account}><select className="input" {...f.bind("to_account")}>{accounts.map((a) => <option key={a.id} value={a.id}>{a.name} ({a.currency})</option>)}</select></Field>
        <Field label="Amount" id="amount" error={f.errors.amount}><input className="input" type="number" min="0" step="0.01" {...f.bind("amount")} /></Field>
        <Field label="Date" id="on_date"><input className="input" type="date" {...f.bind("on_date")} /></Field>
      </div>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Finance() {
  const toast = useToast();
  const { data, loading, error, reload } = useData("/finance/overview/");
  const [dialog, setDialog] = useState(null);
  const [bump, setBump] = useState(0);
  const accounts = useData("/finance/accounts/");
  const accs = accounts.data?.results || [];
  const done = (msg) => { setDialog(null); reload(); setBump((n) => n + 1); toast(msg); };
  if (loading && !data) return <div className="page"><Loading /></div>;
  if (error) return <div className="page"><ErrorState error={error} onRetry={reload} /></div>;
  return (
    <div className="page">
      <div className="page-head"><div><h1>Money in and out</h1><p>Cash flow and money owed. Each currency is kept separate.</p></div><div className="spacer" />
        <a className="btn btn-ghost" href="/api/finance/export/" onClick={(e) => { e.preventDefault(); api("/finance/export/", { raw: true }).then((r) => r.blob()).then((b) => { const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "hilys-money.csv"; a.click(); }); }}>Export for the accountant</a>
        <button className="btn btn-ghost" onClick={() => setDialog("transfer")}>Move money</button>
        <button className="btn btn-primary" onClick={() => setDialog("expense")}>Record money out</button></div>
      <section className="acc-grid" aria-label="Account balances">
        {data.accounts.map((a) => <div key={a.id} className="card card-tight"><span className="muted">{a.kind}</span><strong>{a.name}</strong><span className="stat-value">{money(a.balance, a.currency)}</span></div>)}
      </section>
      <div className="fin-grid">
        <section className="card"><h2>Cash flow</h2>{Object.keys(data.cash_flow).length === 0 ? <p className="muted">No money recorded yet.</p> : Object.entries(data.cash_flow).map(([c, rows]) => <ColumnChart key={c} title={`Money in and out by month (${c})`} series={[{ name: "Money in", color: "var(--chart-1)" }, { name: "Money out", color: "var(--chart-2)" }]} format={(v) => money(v, c)} rows={rows.map((r) => ({ label: new Date(r.month + "-15").toLocaleDateString("en-GB", { month: "short", year: "2-digit" }), values: [r.in, r.out] }))} />)}</section>
        <section className="card"><h2>Money owed to HILYS</h2>{Object.keys(data.ageing).length === 0 ? <p className="muted">Nothing is owed.</p> : Object.entries(data.ageing).map(([c, rows]) => (
          <table key={c} className="age"><caption>{c}</caption><tbody>{rows.map((r) => <tr key={r.bucket} className={r.bucket.includes("late") && Number(r.amount) > 0 ? "late" : ""}><th scope="row">{r.bucket}</th><td>{money(r.amount, c)}</td></tr>)}</tbody></table>))}</section>
      </div>
      <h2 style={{ margin: "28px 0 12px" }}>All money in and out</h2>
      <DataTable path="/finance/entries/" reloadKey={bump} initial={{ ordering: "-on_date" }} searchLabel="Search notes"
        filters={[{ key: "kind", label: "Type", options: [["income", "Money in"], ["expense", "Money out"], ["transfer_in", "Transfer in"], ["transfer_out", "Transfer out"]] }, { key: "category", label: "Category", options: data.categories.map((c) => [c, c]) }]}
        columns={[{ key: "on_date", label: "Date", sort: "on_date", render: (r) => date(r.on_date) }, { key: "account_name", label: "Account" }, { key: "kind_label", label: "Type" }, { key: "category", label: "Category" }, { key: "note", label: "Note" },
          { key: "amount", label: "Amount", align: "right", sort: "amount", render: (r) => <span className={r.kind.includes("in") || r.kind === "income" ? "amt-in" : "amt-out"}>{r.kind === "income" || r.kind === "transfer_in" ? "+" : "−"}{money(r.amount, r.currency)}</span> }]} />
      {dialog === "expense" && accs.length > 0 && <EntryForm accounts={accs} categories={data.categories} kind="expense" onClose={() => setDialog(null)} onDone={() => done("Saved")} />}
      {dialog === "transfer" && accs.length > 1 && <Transfer accounts={accs} onClose={() => setDialog(null)} onDone={() => done("Money moved")} />}
    </div>
  );
}
