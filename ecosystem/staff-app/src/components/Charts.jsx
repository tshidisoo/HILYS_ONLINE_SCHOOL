import { useState } from "react";
import "./Charts.css";

function niceMax(v) {
  if (v <= 0) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((m) => m >= v);
}

function Legend({ series }) {
  if (series.length < 2) return null;
  return <div className="chart-legend">{series.map((s) => <span key={s.name}><i style={{ background: s.color }} />{s.name}</span>)}</div>;
}

function TableView({ rows, series, format, labelHead }) {
  return (
    <table className="chart-table"><thead><tr><th scope="col">{labelHead}</th>{series.map((s) => <th key={s.name} scope="col" className="num">{s.name}</th>)}</tr></thead>
      <tbody>{rows.map((r) => <tr key={r.label}><th scope="row">{r.label}</th>{r.values.map((v, i) => <td key={i} className="num">{format(v)}</td>)}</tr>)}</tbody></table>
  );
}

/* Columns over a shared baseline. One axis, thin marks, a legend for two or more series, and a table view. */
export function ColumnChart({ title, rows, series, format = (v) => v, labelHead = "Month", height = 180 }) {
  const [table, setTable] = useState(false);
  const [tip, setTip] = useState(null);
  const max = niceMax(Math.max(0, ...rows.flatMap((r) => r.values.map(Number))));
  const ticks = [0, max / 2, max];
  return (
    <figure className="chart">
      <div className="chart-head"><figcaption>{title}</figcaption><button className="link-btn" onClick={() => setTable(!table)}>{table ? "Show chart" : "Show as table"}</button></div>
      <Legend series={series} />
      {table ? <TableView rows={rows} series={series} format={format} labelHead={labelHead} /> : (
        <div className="col-chart" style={{ height }}>
          <div className="col-axis" aria-hidden="true">{ticks.slice().reverse().map((t) => <span key={t}>{format(t)}</span>)}</div>
          <div className="col-plot">
            {ticks.map((t) => <span key={t} className="col-grid" style={{ bottom: `${(100 * t) / max}%` }} />)}
            {rows.map((r) => (
              <div key={r.label} className="col-group">
                <div className="col-bars">
                  {r.values.map((v, i) => (
                    <button key={i} className="col-bar" style={{ height: `${Math.max(0.5, (100 * Number(v)) / max)}%`, background: series[i].color }}
                      aria-label={`${r.label}, ${series[i].name}: ${format(v)}`}
                      onPointerEnter={() => setTip({ r, i })} onPointerLeave={() => setTip(null)} onFocus={() => setTip({ r, i })} onBlur={() => setTip(null)} />
                  ))}
                </div>
                <span className="col-label">{r.label}</span>
                {tip?.r === r && <div className="chart-tip" role="status"><strong>{format(r.values[tip.i])}</strong><span>{series[tip.i].name} · {r.label}</span></div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </figure>
  );
}

/* Horizontal bars for one measure across categories, value at the tip. */
export function BarList({ title, rows, format = (v) => v, color = "var(--chart-1)", labelHead = "" }) {
  const [table, setTable] = useState(false);
  const max = Math.max(1, ...rows.map((r) => Number(r.value)));
  return (
    <figure className="chart">
      <div className="chart-head"><figcaption>{title}</figcaption><button className="link-btn" onClick={() => setTable(!table)}>{table ? "Show chart" : "Show as table"}</button></div>
      {rows.length === 0 ? <p className="muted">Nothing to show yet.</p> : table
        ? <TableView rows={rows.map((r) => ({ label: r.label, values: [r.value] }))} series={[{ name: "Count" }]} format={format} labelHead={labelHead} />
        : <ul className="bar-list">{rows.map((r) => (
          <li key={r.label} title={`${r.label}: ${format(r.value)}`}><span className="bar-name">{r.label}</span>
            <span className="bar-track"><span className="bar-fill" style={{ width: `${(100 * Number(r.value)) / max}%`, background: color }} /></span>
            <span className="bar-value">{format(r.value)}</span></li>))}</ul>}
    </figure>
  );
}
