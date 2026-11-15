import { useEffect, useMemo, useState } from "react";
import { qs } from "../api";
import { useData } from "./hooks";
import { Empty, ErrorState, Loading } from "./ui";
import "./DataTable.css";

/*
  A list screen's table: search, filters, sortable columns, pagination, and loading, empty and error states.
  columns: [{ key, label, render(row), sort: "field" }]
  filters: [{ key, label, options: [[value, label]] }]
*/
export default function DataTable({ path, columns, filters = [], initial = {}, onOpen, empty, searchLabel = "Search",
                                    reloadKey = 0, rowKey = (r) => r.id, pageSize = 25 }) {
  const [search, setSearch] = useState("");
  const [term, setTerm] = useState("");
  const [values, setValues] = useState(() => ({ ...initial }));
  const [ordering, setOrdering] = useState(initial.ordering || "");
  const [page, setPage] = useState(1);

  useEffect(() => { const t = setTimeout(() => { setTerm(search); setPage(1); }, 300); return () => clearTimeout(t); }, [search]);

  const url = useMemo(() => `${path}${path.includes("?") ? "&" : "?"}${qs({ ...values, search: term, ordering, page, page_size: pageSize }).slice(1)}`,
    [path, values, term, ordering, page, pageSize]);
  const { data, loading, error, reload } = useData(url, [reloadKey]);
  const rows = Array.isArray(data) ? data : data?.results || [];
  const count = Array.isArray(data) ? rows.length : data?.count || 0;
  const pages = Math.max(1, Math.ceil(count / pageSize));
  const filtered = term || Object.entries(values).some(([k, v]) => v && initial[k] !== v);

  function sortBy(col) {
    if (!col.sort) return;
    setOrdering(ordering === col.sort ? `-${col.sort}` : col.sort);
    setPage(1);
  }

  return (
    <div className="dt">
      <div className="dt-tools">
        <div className="dt-search">
          <label htmlFor="dt-search" className="sr-only">{searchLabel}</label>
          <input id="dt-search" className="input" type="search" placeholder={`${searchLabel}…`} value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {filters.map((f) => (
          <div key={f.key} className="dt-filter">
            <label htmlFor={`f-${f.key}`} className="sr-only">{f.label}</label>
            <select id={`f-${f.key}`} className="input" value={values[f.key] ?? ""} onChange={(e) => { setValues({ ...values, [f.key]: e.target.value }); setPage(1); }}>
              <option value="">{f.label}: all</option>
              {f.options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
        ))}
        {filtered && <button className="link-btn" onClick={() => { setSearch(""); setValues({ ...initial }); setPage(1); }}>Clear filters</button>}
      </div>

      {error ? <ErrorState error={error} onRetry={reload} /> : (
        <div className="dt-wrap" aria-busy={loading}>
          <table className="dt-table">
            <thead>
              <tr>{columns.map((c) => (
                <th key={c.key} scope="col" className={c.align === "right" ? "num" : ""}
                    aria-sort={c.sort && ordering.replace("-", "") === c.sort ? (ordering.startsWith("-") ? "descending" : "ascending") : undefined}>
                  {c.sort ? <button className="dt-sort" onClick={() => sortBy(c)}>{c.label}<span aria-hidden="true">{ordering === c.sort ? " ↑" : ordering === `-${c.sort}` ? " ↓" : ""}</span></button> : c.label}
                </th>))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={rowKey(r)} className={onOpen ? "clickable" : ""} onClick={onOpen ? () => onOpen(r) : undefined}
                    tabIndex={onOpen ? 0 : undefined} onKeyDown={onOpen ? (e) => { if (e.key === "Enter") onOpen(r); } : undefined}>
                  {columns.map((c) => <td key={c.key} data-label={c.label} className={c.align === "right" ? "num" : ""}>{c.render ? c.render(r) : r[c.key] ?? "—"}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
          {loading && !rows.length && <Loading />}
          {!loading && !rows.length && (filtered
            ? <Empty title="Nothing matches">Try a different search or clear the filters.</Empty>
            : (empty || <Empty title="Nothing here yet" />))}
        </div>
      )}

      {pages > 1 && (
        <nav className="dt-pages" aria-label="Pages">
          <button className="btn btn-ghost btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span className="muted">Page {page} of {pages} · {count} in all</span>
          <button className="btn btn-ghost btn-sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
        </nav>
      )}
    </div>
  );
}
