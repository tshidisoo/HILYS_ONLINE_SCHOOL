import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";

// Loads a path; gives data, loading, error and a reload function. Stale answers are ignored.
export function useData(path, deps = []) {
  const [state, setState] = useState({ data: null, loading: !!path, error: null });
  const seq = useRef(0);
  const load = useCallback(async () => {
    if (!path) return;
    const mine = ++seq.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await api(path);
      if (mine === seq.current) setState({ data, loading: false, error: null });
    } catch (error) {
      if (mine === seq.current) setState({ data: null, loading: false, error });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...deps]);
  useEffect(() => { load(); }, [load]);
  return { ...state, reload: load };
}

export function useOpenParam() {
  const params = new URLSearchParams(window.location.search);
  return params.get("open");
}

// One record for a detail panel: data, setData (after an action), reload and error.
export function useRecord(path) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const reload = useCallback(() => api(path).then((d) => { setData(d); setError(null); }).catch(setError), [path]);
  useEffect(() => { reload(); }, [reload]);
  return { data, setData, reload, error };
}
