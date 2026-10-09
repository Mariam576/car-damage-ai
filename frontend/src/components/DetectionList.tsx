import type { Detection } from "../types";
import { damageColour, percent } from "../format";

interface Props {
  detections: Detection[];
  highlighted: number | null;
  onHighlight: (id: number | null) => void;
}

export function DetectionList({ detections, highlighted, onHighlight }: Props) {
  return (
    <ol className="detections">
      {detections.map((d) => (
        <li
          key={d.id}
          className={highlighted === d.id ? "is-on" : undefined}
          onMouseEnter={() => onHighlight(d.id)}
          onMouseLeave={() => onHighlight(null)}
          onFocus={() => onHighlight(d.id)}
          onBlur={() => onHighlight(null)}
          tabIndex={0}
        >
          <span className="swatch" style={{ background: damageColour(d.damage_type) }} aria-hidden="true">
            {d.id}
          </span>
          <span className="det-name">{d.label}</span>
          <span className="det-conf">
            <strong>{percent(d.confidence)}</strong> confidence
          </span>
          <span className="det-cover">covers {percent(d.coverage_pct, 1)} of photo</span>
          {d.low_confidence && <span className="tag tag-warn">Low confidence: check by eye</span>}
        </li>
      ))}
    </ol>
  );
}
