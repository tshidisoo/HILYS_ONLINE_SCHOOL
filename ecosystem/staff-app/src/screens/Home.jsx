import { Link } from "react-router-dom";
import { useData } from "../components/hooks";
import { ErrorState, Loading, Pill } from "../components/ui";
import { date, when } from "../format";
import "./Home.css";

export default function Home() {
  const { data, loading, error, reload } = useData("/home/");
  if (loading && !data) return <div className="page"><Loading /></div>;
  if (error) return <div className="page"><ErrorState error={error} onRetry={reload} /></div>;
  const todo = data.cards.filter((c) => c.count > 0);
  const clear = data.cards.filter((c) => c.count === 0);
  return (
    <div className="page home">
      <div className="page-head"><div><h1>{data.greeting}</h1><p>{date(data.date)} · Harare time</p></div></div>
      <section className="home-numbers" aria-label="Key numbers">
        {data.numbers.map((n) => <div key={n.label} className="card card-tight"><span className="stat-value">{n.value}</span><span className="stat-label">{n.label}</span></div>)}
      </section>
      <div className="home-grid">
        <section aria-labelledby="todo-h">
          <h2 id="todo-h">What needs you today</h2>
          {todo.length === 0 && <div className="card">Nothing is waiting. Ngiyabonga for keeping on top of things.</div>}
          <div className="home-cards">
            {todo.map((c) => (
              <Link key={c.key} to={c.link} className={`home-card tone-edge-${c.tone}`}>
                <span className="home-count">{c.count}</span><span>{c.title}</span><span className="home-go" aria-hidden="true">→</span>
              </Link>
            ))}
          </div>
          {clear.length > 0 && <p className="muted home-clear">All clear: {clear.map((c) => c.title.toLowerCase()).join("; ")}.</p>}
        </section>
        <section aria-labelledby="today-h">
          <h2 id="today-h">Lessons today</h2>
          <div className="card card-tight home-today">
            {data.today.length === 0 && <p className="muted">No lessons today.</p>}
            {data.today.map((l) => (
              <Link key={l.id} to={`/lessons?open=${l.id}`} className="today-row">
                <span className="today-time">{when(l.starts_at).split(", ").pop()}</span>
                <span><strong>{l.who}</strong><br /><span className="muted">{l.teacher_name} · {l.kind_label}</span></span>
                <Pill status={l.status}>{l.status_label}</Pill>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
