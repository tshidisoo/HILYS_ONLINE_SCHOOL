import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import { MENU } from "../App";
import { useAuth } from "../auth";
import { ago } from "../format";
import "./Layout.css";

function Bell() {
  const [data, setData] = useState({ unread: 0, items: [] });
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const load = () => api("/notifications/").then(setData).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, []);
  async function toggle() {
    setOpen(!open);
    if (!open && data.unread) { await api("/notifications/read/", { method: "POST" }).catch(() => {}); setData({ ...data, unread: 0 }); }
  }
  return (
    <div className="bell">
      <button className="icon-btn bell-btn" onClick={toggle} aria-expanded={open} aria-label={`Notifications${data.unread ? `, ${data.unread} new` : ""}`}>
        <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22Zm7-6V11a7 7 0 0 0-5.5-6.84V3a1.5 1.5 0 0 0-3 0v1.16A7 7 0 0 0 5 11v5l-2 2v1h18v-1Z"/></svg>
        {data.unread > 0 && <span className="bell-count">{data.unread}</span>}
      </button>
      {open && (
        <div className="bell-menu" role="menu">
          <h3>Notifications</h3>
          {data.items.length === 0 && <p className="muted">Nothing new. Reminders about late leads and overdue invoices appear here.</p>}
          {data.items.map((n) => (
            <button key={n.id} role="menuitem" className={`bell-item${n.read ? "" : " unread"}`} onClick={() => { setOpen(false); if (n.link) navigate(n.link); }}>
              <strong>{n.title}</strong><span>{n.body}</span><span className="muted">{ago(n.created_at)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Layout({ children }) {
  const { user, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setMenuOpen(false), [location.pathname]);
  const can = (p) => !p || user.permissions?.[p];
  return (
    <div className="shell">
      <a className="skip" href="#main">Skip to the main content</a>
      <header className="topbar">
        <button className="icon-btn menu-btn" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen} aria-controls="sidenav" aria-label="Menu">☰</button>
        <NavLink to="/" className="brand"><img src="/logo.jpg" alt="" width="32" height="32" /><span>HILYS</span><small>Staff</small></NavLink>
        <div className="spacer" />
        <Bell />
        <div className="who"><strong>{user.display_name}</strong><span>{user.role_label}</span></div>
        <button className="btn btn-ghost btn-sm" onClick={signOut}>Sign out</button>
      </header>
      <nav id="sidenav" className={`sidenav${menuOpen ? " open" : ""}`} aria-label="Main">
        {MENU.map((g) => {
          const items = g.items.filter((i) => can(i.perm));
          if (!items.length) return null;
          return (
            <div key={g.area} className="nav-group">
              <span className="nav-area">{g.area}</span>
              {items.map((i) => <NavLink key={i.to} to={i.to} end={i.to === "/"} className="nav-link">{i.label}</NavLink>)}
            </div>
          );
        })}
      </nav>
      <main id="main" className="main" tabIndex={-1}>{children}</main>
    </div>
  );
}
