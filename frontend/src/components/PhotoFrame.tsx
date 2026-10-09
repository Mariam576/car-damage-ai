import type { Detection } from "../types";
import { damageColour } from "../format";

interface Props {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  detections?: Detection[];
  highlighted?: number | null;
  onHighlight?: (id: number | null) => void;
  compact?: boolean;
}

interface Tag {
  x: number;
  y: number;
  w: number;
  h: number;
}

const overlaps = (a: Tag, b: Tag) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

/** Place each label above its box, or inside the top, or below it: whichever doesn't hit a label already placed. */
export function placeTags(detections: Detection[], imageW: number, imageH: number, font: number): Map<number, Tag> {
  const pad = font * 0.35;
  const h = font * 1.35;
  const placed = new Map<number, Tag>();
  for (const d of detections) {
    const w = `${d.id} ${d.label} ${d.confidence.toFixed(1)}%`.length * font * 0.52 + pad * 2;
    const x = Math.max(0, Math.min(d.box.x1, imageW - w));
    const candidates = [d.box.y1 - h, d.box.y1, d.box.y2, d.box.y2 - h]
      .filter((y) => y >= 0 && y + h <= imageH)
      .map((y) => ({ x, y, w, h }));
    const free = candidates.find((c) => ![...placed.values()].some((p) => overlaps(c, p)));
    placed.set(d.id, free ?? candidates[0] ?? { x, y: Math.max(0, d.box.y1), w, h });
  }
  return placed;
}

/** The photo with YOLO boxes drawn over it in image-pixel coordinates. */
export function PhotoFrame({ src, alt, width, height, detections = [], highlighted, onHighlight, compact }: Props) {
  const showBoxes = Boolean(width && height && detections.length);
  const w = width ?? 1;
  const h = height ?? 1;
  const font = Math.max(w, h) / (compact ? 38 : 44);
  const tags = showBoxes ? placeTags(detections, w, h, font) : new Map<number, Tag>();
  // Labels are drawn after all boxes; the highest-confidence label (or the hovered one) ends up on top.
  const labelOrder = [...detections].reverse().sort((a, b) => Number(a.id === highlighted) - Number(b.id === highlighted));
  const hover = (id: number | null) => onHighlight?.(id);
  const dimmed = (id: number) => (highlighted != null && highlighted !== id ? " is-dim" : "");

  return (
    <div className={`photo-frame${compact ? " is-compact" : ""}`}>
      <img src={src} alt={alt} />
      {showBoxes && (
        <svg
          className="boxes"
          viewBox={`0 0 ${w} ${h}`}
          preserveAspectRatio="none"
          role="img"
          aria-label={`${detections.length} detected damage area${detections.length === 1 ? "" : "s"}`}
        >
          {detections.map((d) => {
            const colour = damageColour(d.damage_type);
            const box = { x: d.box.x1, y: d.box.y1, width: d.box.x2 - d.box.x1, height: d.box.y2 - d.box.y1 };
            return (
              <g key={d.id} className={`box${dimmed(d.id)}`} onMouseEnter={() => hover(d.id)} onMouseLeave={() => hover(null)}>
                <rect {...box} fill="transparent" stroke="#0E131B" strokeOpacity={0.55} strokeWidth={5} vectorEffect="non-scaling-stroke" />
                <rect
                  {...box}
                  fill={highlighted === d.id ? colour : "transparent"}
                  fillOpacity={0.14}
                  stroke={colour}
                  strokeWidth={2.5}
                  strokeDasharray={d.low_confidence ? "7 5" : undefined}
                  vectorEffect="non-scaling-stroke"
                />
              </g>
            );
          })}
          {labelOrder.map((d) => {
            const t = tags.get(d.id)!;
            return (
              <g key={`tag-${d.id}`} className={`box${dimmed(d.id)}`} onMouseEnter={() => hover(d.id)} onMouseLeave={() => hover(null)}>
                <rect x={t.x} y={t.y} width={t.w} height={t.h} fill={damageColour(d.damage_type)} />
                <text
                  x={t.x + font * 0.35}
                  y={t.y + t.h * 0.74}
                  fontSize={font}
                  fill="#fff"
                  fontFamily="'Barlow Semi Condensed', sans-serif"
                  fontWeight={600}
                >
                  {`${d.id} ${d.label} ${d.confidence.toFixed(1)}%`}
                </text>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}
