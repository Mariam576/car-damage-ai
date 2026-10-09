interface Props {
  min: number;
  max: number;
  open?: boolean;
  scaleMax: number;
  colour?: string;
}

/** A price range drawn on a shared £0–scaleMax axis, so options can be compared by eye. */
export function RangeBar({ min, max, open, scaleMax, colour = "var(--ink)" }: Props) {
  const scale = Math.max(scaleMax, 1);
  const left = (min / scale) * 100;
  const width = Math.max(((max - min) / scale) * 100, 1.2);
  const mid = (((min + max) / 2) / scale) * 100;
  return (
    <div className="range-bar" aria-hidden="true">
      <div
        className={`range-fill${open ? " is-open" : ""}`}
        style={{ left: `${left}%`, width: `${width}%`, background: colour }}
      />
      <div className="range-mid" style={{ left: `${mid}%` }} />
    </div>
  );
}

/** Upper end of the axis for a group of ranges: the largest maximum plus headroom for "+" ranges. */
export function scaleFor(ranges: { max_gbp: number; max_open: boolean }[]): number {
  const top = Math.max(0, ...ranges.map((r) => r.max_gbp * (r.max_open ? 1.15 : 1)));
  return top * 1.04;
}
