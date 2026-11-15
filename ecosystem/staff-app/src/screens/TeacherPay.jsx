import { useState } from "react";
import { api } from "../api";
import { useData } from "../components/hooks";
import { Confirm, Dialog, Empty, ErrorState, Field, Loading, Pill, useToast } from "../components/ui";
import { money } from "../format";

export default function TeacherPay() {
  const toast = useToast();
  const [month, setMonth] = useState(() => { const d = new Date(); d.setMonth(d.getMonth() - 1); return d.toISOString().slice(0, 7); });
  const { data, loading, error, reload } = useData(`/teacher-pay/?month=${month}`);
  const accounts = useData("/finance/accounts/");
  const [open, setOpen] = useState(null);
  const [paying, setPaying] = useState(null);
  const [account, setAccount] = useState("");
  const rows = data?.results || [];
  const build = () => api("/teacher-pay/build/", { method: "POST", body: { month } }).then(() => { reload(); toast("Statements worked out from reported lessons"); }).catch((e) => toast(e.message));
  return (
    <div className="page">
      <div className="page-head"><div><h1>Teacher pay</h1><p>Worked out from lessons the teacher has reported. Unreported lessons are not paid until reported.</p></div><div className="spacer" />
        <label htmlFor="month" className="sr-only">Month</label><input id="month" className="input" style={{ width: 170 }} type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
        <button className="btn btn-primary" onClick={build}>Work out {month}</button></div>
      {loading && !data ? <Loading /> : error ? <ErrorState error={error} onRetry={reload} /> : rows.length === 0 ? <Empty title={`No statements for ${month} yet`} action={<button className="btn btn-primary btn-sm" onClick={build}>Work them out</button>}>They are made from each teacher's reported lessons.</Empty> : (
        <div className="stack">{rows.map((s) => (
          <div key={s.id} className="card">
            <div className="row"><h2>{s.teacher_name}</h2><Pill status={s.status}>{s.status_label}</Pill>{s.unreported > 0 && <Pill tone="warn">{s.unreported} {s.unreported === 1 ? "lesson" : "lessons"} not reported</Pill>}<div className="spacer" />
              <strong style={{ fontSize: 20 }}>{money(s.total, s.currency)}</strong></div>
            <p className="muted">{s.lines.length} paid lessons{s.paid_on ? ` · paid on ${s.paid_on}` : ""}</p>
            <div className="row">
              <button className="btn btn-ghost btn-sm" onClick={() => setOpen(s)}>See lessons</button>
              {s.status === "draft" && <button className="btn btn-primary btn-sm" disabled={s.unreported > 0} onClick={() => api(`/teacher-pay/${s.id}/approve/`, { method: "POST" }).then(() => { reload(); toast("Approved"); }).catch((e) => toast(e.message))}>Approve</button>}
              {s.status === "approved" && <button className="btn btn-primary btn-sm" onClick={() => setPaying(s)}>Mark as paid</button>}
            </div>
          </div>))}</div>
      )}
      {open && <Dialog title={`${open.teacher_name} · ${open.month}`} wide onClose={() => setOpen(null)}>
        <table className="doc-lines"><thead><tr><th>Date</th><th>Child</th><th>Lesson</th><th>What happened</th><th className="num">Pay</th></tr></thead>
          <tbody>{open.lines.map((l) => <tr key={l.lesson}><td>{l.date}</td><td>{l.who}</td><td>{l.kind}</td><td>{l.status}</td><td className="num">{money(l.rate, open.currency)}</td></tr>)}</tbody></table>
        <p className="muted">Rates are drafts set per teacher in Team and logins.</p></Dialog>}
      {paying && <Dialog title={`Pay ${paying.teacher_name}`} onClose={() => setPaying(null)} footer={<><button className="btn btn-ghost" onClick={() => setPaying(null)}>Cancel</button>
        <button className="btn btn-primary" disabled={!account} onClick={() => api(`/teacher-pay/${paying.id}/paid/`, { method: "POST", body: { account } }).then(() => { setPaying(null); reload(); toast("Marked as paid"); }).catch((e) => toast(e.message))}>Mark {money(paying.total, paying.currency)} as paid</button></>}>
        <Field label="Paid from" id="account"><select id="account" className="input" value={account} onChange={(e) => setAccount(e.target.value)}><option value="">Choose…</option>
          {(accounts.data?.results || []).filter((a) => a.currency === paying.currency).map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></Field>
        <p className="muted" style={{ margin: 0 }}>This records the money out in the account. Send the money to the teacher yourself.</p></Dialog>}
    </div>
  );
}
