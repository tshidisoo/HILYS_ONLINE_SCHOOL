import { BarList, ColumnChart } from "../components/Charts";
import { useData } from "../components/hooks";
import { ErrorState, Loading } from "../components/ui";
import { money } from "../format";
import "./Analytics.css";

const STAGE = { trial: "Trial", waiting: "Waiting to start", active: "Active", paused: "Paused", finished: "Finished", stopped: "Stopped" };
const LESSON = { taught: "Taught", scheduled: "Scheduled", missed: "Missed (used)", cut_short: "Cut short", cancelled: "Cancelled by HILYS", moved: "Moved" };
const STATUS_TEXT = { good: "On target", warn: "Close", bad: "Below target", none: "Not enough data yet" };

export default function Analytics() {
  const { data, loading, error, reload } = useData("/analytics/");
  if (loading && !data) return <div className="page"><Loading /></div>;
  if (error) return <div className="page"><ErrorState error={error} onRetry={reload} /></div>;
  return (
    <div className="page">
      <div className="page-head"><div><h1>Analytics</h1><p>The last six months. Targets are drafts for the owner to set.</p></div></div>
      <section className="kpis" aria-label="Targets">
        {data.kpis.map((k) => (
          <div key={k.label} className={`card card-tight kpi kpi-${k.status}`}>
            <span className="kpi-label">{k.label}</span>
            <span className="kpi-value">{k.actual === null ? "—" : `${k.actual}${k.unit}`}</span>
            <span className="kpi-meta"><span className={`pill tone-${k.status === "none" ? "neutral" : k.status}`}>{STATUS_TEXT[k.status]}</span> target {k.target}{k.unit}</span>
          </div>
        ))}
      </section>
      <div className="an-grid">
        <section className="card">{Object.entries(data.revenue_by_month).length === 0 ? <p className="muted">No payments yet.</p> :
          Object.entries(data.revenue_by_month).map(([c, rows]) => <ColumnChart key={c} title={`Money received by month (${c})`} series={[{ name: "Received", color: "var(--chart-1)" }]}
            format={(v) => money(v, c)} rows={rows.map((r) => ({ label: new Date(r.month + "-15").toLocaleDateString("en-GB", { month: "short" }), values: [r.amount] }))} />)}</section>
        <section className="card"><BarList title="Where leads come from" labelHead="Source" rows={data.leads_by_source.map((r) => ({ label: r.source, value: r.count }))} />
          <p className="muted an-note">{data.conversion.families} of {data.conversion.leads} leads became families.</p></section>
        <section className="card"><BarList title="Children by package (learning now)" labelHead="Package" rows={data.children_by_package.map((r) => ({ label: r.package, value: r.count }))} /></section>
        <section className="card"><BarList title="Enrolments by stage" labelHead="Stage" rows={data.work_by_stage.map((r) => ({ label: STAGE[r.stage] || r.stage, value: r.n }))} /></section>
        <section className="card"><BarList title="Lessons in the last 30 days" labelHead="What happened" rows={data.lessons_last_30_days.map((r) => ({ label: LESSON[r.status] || r.status, value: r.n }))} /></section>
        <section className="card an-stat"><span className="stat-value">{data.returning_families}</span><span className="stat-label">Returning families (three or more documents)</span></section>
      </div>
    </div>
  );
}
