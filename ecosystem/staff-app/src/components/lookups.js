import { useEffect, useState } from "react";
import { api } from "../api";

const cache = {};
// Small option lists used by forms (teachers, families, packages). Fetched once per session.
export function useLookup(name) {
  const paths = {
    teachers: "/users/?role=teacher&page_size=200",
    staff: "/users/?page_size=200",
    families: "/families/?page_size=200&ordering=parent_name",
    packages: "/catalogue/?is_active=true&page_size=200",
    books: "/books/",
  };
  const [rows, setRows] = useState(cache[name] || []);
  useEffect(() => {
    if (cache[name]) return;
    api(paths[name]).then((d) => { cache[name] = d.results || d; setRows(cache[name]); }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name]);
  return rows;
}
export function clearLookup(name) { delete cache[name]; }
