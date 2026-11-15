import { api } from "../api";
import { useData } from "./hooks";
import { Dialog, Empty, ErrorState, Loading, useToast } from "./ui";
import { date } from "../format";

// The bin for one record type. Leadership can restore what was deleted by mistake.
export default function Bin({ base, label, onClose, onRestored }) {
  const toast = useToast();
  const { data, loading, error, reload } = useData(`${base}bin/`);
  async function restore(row) {
    try { await api(`${base}${row.id}/restore/`, { method: "POST" }); toast("Restored"); reload(); onRestored?.(); }
    catch (e) { toast(e.message); }
  }
  return (
    <Dialog title="Deleted records" onClose={onClose}>
      {loading && <Loading />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && data.length === 0 && <Empty title="The bin is empty">Deleted records wait here until someone restores them.</Empty>}
      {data && data.map((r) => (
        <div key={r.id} className="row" style={{ borderBottom: "1px solid var(--line)", paddingBottom: 8 }}>
          <span><strong>{label(r)}</strong><br /><span className="muted">Created {date(r.created_at)}</span></span>
          <div className="spacer" /><button className="btn btn-ghost btn-sm" onClick={() => restore(r)}>Restore</button>
        </div>
      ))}
    </Dialog>
  );
}
