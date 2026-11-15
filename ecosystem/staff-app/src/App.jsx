import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth";
import ErrorBoundary from "./components/ErrorBoundary";
import Layout from "./components/Layout";
import { Loading } from "./components/ui";
import Analytics from "./screens/Analytics";
import Audit from "./screens/Audit";
import Curriculum from "./screens/Curriculum";
import Documents from "./screens/Documents";
import Enrolments from "./screens/Enrolments";
import Families from "./screens/Families";
import Feedback from "./screens/Feedback";
import Finance from "./screens/Finance";
import Home from "./screens/Home";
import Leads from "./screens/Leads";
import Lessons from "./screens/Lessons";
import Login from "./screens/Login";
import Payments from "./screens/Payments";
import Pipeline from "./screens/Pipeline";
import PriceBook from "./screens/PriceBook";
import Privacy from "./screens/Privacy";
import Settings from "./screens/Settings";
import Tasks from "./screens/Tasks";
import TeacherPay from "./screens/TeacherPay";
import Team from "./screens/Team";
import Website from "./screens/Website";

export const MENU = [
  { area: "Today", items: [{ to: "/", label: "Home" }, { to: "/tasks", label: "Tasks" }] },
  { area: "Leads and sales", items: [{ to: "/leads", label: "Leads" }, { to: "/pipeline", label: "Pipeline" }] },
  { area: "Families", items: [{ to: "/families", label: "Families" }, { to: "/enrolments", label: "Enrolments" }] },
  { area: "Teaching", items: [{ to: "/lessons", label: "Timetable" }, { to: "/curriculum", label: "Book 1 and certificates" }] },
  { area: "Money", items: [
    { to: "/documents", label: "Documents" }, { to: "/payments", label: "Payments desk" },
    { to: "/finance", label: "Money in and out", perm: "can_record_payments" }, { to: "/teacher-pay", label: "Teacher pay", perm: "can_record_payments" },
    { to: "/price-book", label: "Price book" }] },
  { area: "Insight", items: [{ to: "/analytics", label: "Analytics" }, { to: "/feedback", label: "Feedback", perm: "is_leadership" }] },
  { area: "Settings", items: [
    { to: "/team", label: "Team and logins" }, { to: "/website", label: "Website content" }, { to: "/privacy", label: "Privacy" },
    { to: "/audit", label: "Audit log", perm: "is_leadership" }, { to: "/settings", label: "Company settings" }] },
];

export default function App() {
  const { user, checking } = useAuth();
  const location = useLocation();
  if (checking) return <Loading label="Opening HILYS…" />;
  if (!user) return <Login />;
  const can = (p) => !p || user.permissions?.[p];
  const guard = (perm, el) => (can(perm) ? el : <Navigate to="/" replace />);
  return (
    <Layout>
      <ErrorBoundary resetKey={location.pathname}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/leads" element={<Leads />} />
        <Route path="/pipeline" element={<Pipeline />} />
        <Route path="/families" element={<Families />} />
        <Route path="/enrolments" element={<Enrolments />} />
        <Route path="/lessons" element={<Lessons />} />
        <Route path="/curriculum" element={<Curriculum />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/payments" element={<Payments />} />
        <Route path="/finance" element={guard("can_record_payments", <Finance />)} />
        <Route path="/teacher-pay" element={guard("can_record_payments", <TeacherPay />)} />
        <Route path="/price-book" element={<PriceBook />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/feedback" element={guard("is_leadership", <Feedback />)} />
        <Route path="/team" element={<Team />} />
        <Route path="/website" element={<Website />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/audit" element={guard("is_leadership", <Audit />)} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </ErrorBoundary>
    </Layout>
  );
}
