import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import { useLookup } from "../components/lookups";
import { Dialog, Empty, Field, Pill, useToast } from "../components/ui";
import { useForm } from "../components/useForm";
import { date } from "../format";

function TaskForm({ task, onClose, onDone }) {
  const staff = useLookup("staff").filter((u) => ["owner", "coordinator", "finance"].includes(u.role));
  const { user } = useAuth();
  const f = useForm(task || { title: "", notes: "", assignee: user.id, due_on: new Date().toISOString().slice(0, 10), status: "open" });
  return (
    <Dialog title={task ? "Edit task" : "New task"} onClose={onClose} footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" disabled={f.busy || !f.values.title} onClick={() => f.submit(async (v) => onDone(task ? await api(`/tasks/${task.id}/`, { method: "PATCH", body: v }) : await api("/tasks/", { method: "POST", body: v })))}>Save</button></>}>
      <Field label="What needs doing?" id="title" error={f.errors.title}><input className="input" {...f.bind("title")} /></Field>
      <div className="form-grid">
        <Field label="Who" id="assignee"><select className="input" {...f.bind("assignee")}>{staff.map((u) => <option key={u.id} value={u.id}>{u.display_name}</option>)}</select></Field>
        <Field label="Due" id="due_on"><input className="input" type="date" {...f.bind("due_on")} /></Field>
        {task && <Field label="Status" id="status"><select className="input" {...f.bind("status")}><option value="open">To do</option><option value="doing">Doing</option><option value="done">Done</option></select></Field>}
      </div>
      <Field label="Notes" id="notes"><textarea className="input" {...f.bind("notes")} /></Field>
      {f.formError && <div className="form-error" role="alert">{f.formError}</div>}
    </Dialog>
  );
}

export default function Tasks() {
  const toast = useToast();
  const [edit, setEdit] = useState(null);
  const [reload, setReload] = useState(0);
  const today = new Date().toISOString().slice(0, 10);
  const mine = new URLSearchParams(window.location.search).get("mine") || "";
  const done = (r) => api(`/tasks/${r.id}/`, { method: "PATCH", body: { status: "done" } }).then(() => { setReload((n) => n + 1); toast("Done"); });
  return (
    <div className="page">
      <div className="page-head"><div><h1>Tasks</h1><p>Small jobs with an owner and a date.</p></div><div className="spacer" /><button className="btn btn-primary" onClick={() => setEdit({})}>New task</button></div>
      <DataTable path="/tasks/" reloadKey={reload} onOpen={setEdit} initial={{ mine, status: "", ordering: "due_on" }}
        filters={[{ key: "mine", label: "Whose", options: [["1", "Mine only"]] }, { key: "status", label: "Status", options: [["open", "To do"], ["doing", "Doing"], ["done", "Done"]] }]}
        empty={<Empty title="No tasks" action={<button className="btn btn-primary btn-sm" onClick={() => setEdit({})}>New task</button>} />}
        columns={[{ key: "title", label: "Task", render: (r) => <span className={r.status === "done" ? "muted" : "cell-main"}>{r.title}</span> }, { key: "assignee_name", label: "Who" },
          { key: "due_on", label: "Due", sort: "due_on", render: (r) => <span style={{ color: r.status !== "done" && r.due_on && r.due_on < today ? "var(--bad)" : undefined, fontWeight: r.due_on < today ? 700 : 400 }}>{date(r.due_on)}{r.status !== "done" && r.due_on < today ? " (late)" : ""}</span> },
          { key: "status", label: "Status", render: (r) => <Pill status={r.status}>{r.status_label}</Pill> },
          { key: "act", label: "", render: (r) => r.status !== "done" && <button className="btn btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); done(r); }}>Mark done</button> }]} />
      {edit && <TaskForm task={edit.id ? edit : null} onClose={() => setEdit(null)} onDone={() => { setEdit(null); setReload((n) => n + 1); toast("Saved"); }} />}
    </div>
  );
}
