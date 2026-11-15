import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(!!getToken());
  useEffect(() => {
    if (!getToken()) return;
    api("/auth/me/").then(setUser).catch(() => setToken(null)).finally(() => setChecking(false));
  }, []);
  useEffect(() => {
    const out = () => setUser(null);
    window.addEventListener("hilys-signed-out", out);
    return () => window.removeEventListener("hilys-signed-out", out);
  }, []);
  const signIn = useCallback(async (username, password) => {
    const r = await api("/auth/login/", { method: "POST", body: { username, password, app: "teacher" } });
    setToken(r.token);
    setUser(r.user);
  }, []);
  const signOut = useCallback(async () => {
    try { await api("/auth/logout/", { method: "POST" }); } catch { /* already gone */ }
    setToken(null);
    setUser(null);
  }, []);
  return <AuthCtx.Provider value={{ user, checking, signIn, signOut }}>{children}</AuthCtx.Provider>;
}
export const useAuth = () => useContext(AuthCtx);
