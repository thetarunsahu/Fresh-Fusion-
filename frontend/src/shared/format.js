export const fmt = (value, decimals = 1) =>
  value == null ? "—" : Number(value).toFixed(decimals);
export const dateValue = (value) =>
  value
    ? new Date(/(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value}Z`)
    : null;
export const dateTime = (value) =>
  dateValue(value)?.toLocaleString() || "Not recorded";
export const isRecent = (value, seconds, now = Date.now()) => {
  const age = now - (dateValue(value)?.getTime() ?? 0);
  return Boolean(value) && age >= -5000 && age <= seconds * 1000;
};
export const titleCase = (value) =>
  (value || "Not available").replaceAll("_", " ").replaceAll("-", " ");
