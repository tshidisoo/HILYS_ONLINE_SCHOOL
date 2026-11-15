import { useData } from "../components/hooks";
import { Empty, ErrorState, Loading, Pill } from "../components/ui";
import { date, money } from "../format";

export default function Pay() {
  const { data, loading, error, reload } = useData("/teacher/pay/");
  if (loading && !data) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  return (
    <div>
      <h1>My pay</h1>
      <p className="muted">Worked out by HILYS from the lessons you report. A lesson is paid once it is reported.</p>
      {data.length === 0 && <Empty title="No pay statements yet">They appear here once HILYS works out the month.</Empty>}
      {data.map((s) => (
        <article key={s.month} className="t-lesson">
          <div className="row"><strong style={{ fontSize: 17 }}>{new Date(s.month + "-15").toLocaleDateString("en-GB", { month: "long", year: "numeric" })}</strong><div className="spacer" />
            <Pill status={s.status.toLowerCase()}>{s.status}</Pill></div>
          <span className="t-time">{money(s.total, s.currency)}</span>
          <span className="t-sub">{s.lessons} paid lessons{s.paid_on ? ` · paid ${date(s.paid_on)}` : ""}</span>
          {s.unreported > 0 && <Pill tone="warn">{s.unreported} {s.unreported === 1 ? "lesson" : "lessons"} not reported yet</Pill>}
        </article>
      ))}
    </div>
  );
}
