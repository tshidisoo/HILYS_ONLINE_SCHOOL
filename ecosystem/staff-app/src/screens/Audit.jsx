import DataTable from "../components/DataTable";
import { when } from "../format";

const ACTIONS = ["login", "create", "update", "delete", "restore", "issue", "amend", "cancel", "payment", "reverse", "allocate", "override", "role", "suspend", "password", "stage", "price", "export", "settings", "convert", "dismiss"];

export default function Audit() {
  return (
    <div className="page">
      <div className="page-head"><div><h1>Audit log</h1><p>Who did what, and when. Nobody can change or delete these entries.</p></div></div>
      <DataTable path="/audit/" searchLabel="Search what happened" filters={[{ key: "action", label: "Action", options: ACTIONS.map((a) => [a, a[0].toUpperCase() + a.slice(1)]) }]}
        columns={[{ key: "at", label: "When", render: (r) => when(r.at) }, { key: "actor_name", label: "Who" }, { key: "action", label: "Action" },
          { key: "summary", label: "What happened", render: (r) => <>{r.summary}{r.reason && <div className="cell-sub">Reason: {r.reason}</div>}</> }]} />
    </div>
  );
}
