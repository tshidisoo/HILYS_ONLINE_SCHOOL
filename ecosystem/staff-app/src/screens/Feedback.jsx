import { useState } from "react";
import { api } from "../api";
import DataTable from "../components/DataTable";
import { useLookup } from "../components/lookups";
import { DL, Dialog, Empty, Field, Pill, useToast } from "../components/ui";
import { date } from "../format";

export default function Feedback() {
  const toast = useToast();
  const families = useLookup("families");
  const [making, setMaking] = useState(false);
  const [family, setFamily] = useState("");
  const [reason, setReason] = useState("End of Book 1");
  const [link, setLink] = useState("");
  const [open, setOpen] = useState(null);
  const [reload, setReload] = useState(0);
  return (
    <div className="page">
      <div className="page-head"><div><h1>Feedback</h1><p>Survey answers from parents. Only the owner sees them.</p></div><div className="spacer" /><button className="btn btn-primary" onClick={() => setMaking(true)}>Make a survey link</button></div>
      <DataTable path="/feedback/" reloadKey={reload} onOpen={setOpen} empty={<Empty title="No feedback yet">Make a survey link and send it on WhatsApp at the end of a book or term.</Empty>}
        columns={[{ key: "family_name", label: "Family" }, { key: "reason", label: "When" }, { key: "sent_at", label: "Sent", render: (r) => date(r.sent_at) },
          { key: "rating", label: "Rating", render: (r) => r.answered_at ? `${r.rating} of 5` : <Pill tone="neutral">Not answered</Pill> },
          { key: "would_recommend", label: "Would recommend", render: (r) => r.answered_at ? (r.would_recommend ? "Yes" : "Not yet") : "—" }]} />
      {open && <Dialog title={`${open.family_name}: ${open.reason}`} onClose={() => setOpen(null)}>
        {open.answered_at ? <DL rows={[["Rating", `${open.rating} of 5`], ["Would recommend", open.would_recommend ? "Yes" : "Not yet"], ["Enjoyed most", open.best], ["Could do better", open.improve], ["May quote on the website", open.may_quote ? "Yes" : "No"]]} />
          : <><p style={{ margin: 0 }}>Not answered yet. The link to send:</p><code style={{ overflowWrap: "anywhere" }}>{open.link}</code></>}
      </Dialog>}
      {making && <Dialog title="Make a survey link" onClose={() => { setMaking(false); setLink(""); }} footer={!link && <><button className="btn btn-ghost" onClick={() => setMaking(false)}>Cancel</button>
        <button className="btn btn-primary" disabled={!family} onClick={() => api("/feedback/", { method: "POST", body: { family, reason } }).then((r) => { setLink(r.link); setReload((n) => n + 1); }).catch((e) => toast(e.message))}>Make link</button></>}>
        {link ? <><p style={{ margin: 0 }}>Send this link to the parent on WhatsApp:</p><code style={{ overflowWrap: "anywhere" }}>{link}</code>
          <button className="btn btn-ghost btn-sm" onClick={() => navigator.clipboard?.writeText(link).then(() => toast("Copied"))}>Copy link</button></> : <>
          <Field label="Family" id="fb-family"><select id="fb-family" className="input" value={family} onChange={(e) => setFamily(e.target.value)}><option value="">Choose…</option>{families.map((x) => <option key={x.id} value={x.id}>{x.parent_name}</option>)}</select></Field>
          <Field label="When" id="fb-reason"><input id="fb-reason" className="input" value={reason} onChange={(e) => setReason(e.target.value)} /></Field></>}
      </Dialog>}
    </div>
  );
}
