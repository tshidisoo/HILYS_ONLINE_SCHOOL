// Money, dates and times formatted for people, not machines. Never added across currencies.
export function money(amount, currency = "USD") {
  if (amount === null || amount === undefined || amount === "") return "—";
  const n = Number(amount);
  return new Intl.NumberFormat("en-GB", { style: "currency", currency, currencyDisplay: "code", minimumFractionDigits: 2 }).format(n);
}
export function date(value) {
  if (!value) return "—";
  const d = new Date(value.length === 10 ? value + "T12:00:00" : value);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}
export function when(value, timeZone = "Africa/Harare") {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-GB", { timeZone, weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
export function timeOnly(value, timeZone = "Africa/Harare") {
  return new Date(value).toLocaleTimeString("en-GB", { timeZone, hour: "2-digit", minute: "2-digit" });
}
export function ago(value) {
  if (!value) return "";
  const mins = Math.round((Date.now() - new Date(value).getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${h} h ago`;
  return `${Math.round(h / 24)} days ago`;
}
export const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
export const COUNTRIES = { GB: "United Kingdom", ZA: "South Africa", AU: "Australia", US: "United States", ZW: "Zimbabwe", CA: "Canada", IE: "Ireland", NZ: "New Zealand", BW: "Botswana" };
export const TIME_ZONES = ["Europe/London", "Europe/Dublin", "Africa/Johannesburg", "Africa/Harare", "Africa/Gaborone",
  "Australia/Perth", "Australia/Sydney", "Australia/Brisbane", "Pacific/Auckland", "America/New_York", "America/Chicago",
  "America/Los_Angeles", "America/Toronto"];
