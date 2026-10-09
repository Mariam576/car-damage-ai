const whole = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 });
const pence = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 2 });

/** "£120", "£29.95", "£962.50" */
export function money(value: number): string {
  const rounded = Math.round(value * 100) / 100;
  return Number.isInteger(rounded) ? whole.format(rounded) : pence.format(rounded);
}

export function range(min: number, max: number, open = false): string {
  if (min === max && !open) return money(min);
  return `${money(min)}–${money(max)}${open ? "+" : ""}`;
}

const day = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });
const stamp = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function date(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00Z` : iso);
  return Number.isNaN(d.getTime()) ? iso : day.format(d);
}

export function dateTime(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : stamp.format(d);
}

export function percent(value: number | null | undefined, digits = 2): string {
  return value == null ? "–" : `${value.toFixed(digits)}%`;
}

/** "Dentscout, updated 30 Aug 2026" */
export function sourceDate(source: { publisher: string; published: string | null; updated: string | null }): string {
  if (source.updated) return `${source.publisher}, updated ${date(source.updated)}`;
  if (source.published) return `${source.publisher}, ${date(source.published)}`;
  return source.publisher;
}

/** "1 dent", "2 panels", "3 tyres" */
export function units(count: number, unit: string): string {
  if (count === 1) return `1 ${unit}`;
  const plural = unit.endsWith("s") ? unit : `${unit}s`;
  return `${count} ${plural}`;
}

/** Colour per damage class, used for boxes, swatches and legends. */
export const DAMAGE_COLOURS: Record<string, string> = {
  dent: "#3B7BF0",
  scratch: "#E2477F",
  crack: "#F08A00",
  "glass shatter": "#0FA3A3",
  "lamp broken": "#9A63F0",
  "tire flat": "#47A447",
};

export function damageColour(type: string): string {
  return DAMAGE_COLOURS[type] ?? "#C8CDD3";
}
