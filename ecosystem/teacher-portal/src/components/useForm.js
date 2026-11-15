import { useState } from "react";

// Keeps the person's input, shows server errors under the right field, and a message for the rest.
export function useForm(initial) {
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setValues((v) => ({ ...v, [k]: e?.target ? (e.target.type === "checkbox" ? e.target.checked : e.target.value) : e }));
  async function submit(fn) {
    setBusy(true); setErrors({}); setFormError("");
    try { return await fn(values); }
    catch (e) {
      setErrors(e.fields || {});
      setFormError(Object.keys(e.fields || {}).length ? "Please fix the highlighted fields." : e.message);
      return null;
    } finally { setBusy(false); }
  }
  const bind = (k) => ({ id: k, value: values[k] ?? "", onChange: set(k), "aria-invalid": errors[k] ? "true" : undefined,
                          "aria-describedby": errors[k] ? `${k}-error` : undefined });
  return { values, setValues, set, errors, formError, busy, submit, bind };
}
