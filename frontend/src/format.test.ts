import { describe, expect, it } from "vitest";
import { date, money, range, sourceDate, units } from "./format";
import { scaleFor } from "./components/RangeBar";
import { missingChoices } from "./components/Estimate";
import type { Analysis } from "./types";

describe("format", () => {
  it("formats pounds without trailing pence", () => {
    expect(money(120)).toBe("£120");
    expect(money(29.95)).toBe("£29.95");
    expect(money(1400)).toBe("£1,400");
    expect(money(962.5)).toBe("£962.50");
  });
  it("formats ranges, including open-ended ones", () => {
    expect(range(60, 180)).toBe("£60–£180");
    expect(range(600, 1000, true)).toBe("£600–£1,000+");
    expect(range(0, 0)).toBe("£0");
  });
  it("formats dates and sources", () => {
    expect(date("2026-08-30")).toBe("30 Aug 2026");
    expect(sourceDate({ publisher: "Dentscout", published: "2025-04-01", updated: "2026-08-30" })).toBe(
      "Dentscout, updated 30 Aug 2026",
    );
    expect(sourceDate({ publisher: "Drive", published: "2026-07-16", updated: null })).toBe("Drive, 16 Jul 2026");
  });
  it("pluralises units", () => {
    expect(units(1, "dent")).toBe("1 dent");
    expect(units(3, "tyre")).toBe("3 tyres");
  });
  it("leaves headroom on the scale for open ranges", () => {
    expect(scaleFor([{ max_gbp: 100, max_open: false }])).toBeCloseTo(104);
    expect(scaleFor([{ max_gbp: 100, max_open: true }])).toBeCloseTo(119.6);
  });
});

describe("missingChoices", () => {
  const analysis = {
    summary: {
      by_type: [
        { damage_type: "dent", label: "Dent", count: 1, max_confidence: 64.61, safety_related: false },
        { damage_type: "odd", label: "Odd", count: 1, max_confidence: 50, safety_related: false },
      ],
    },
    repair_options: { dent: [{ id: 5 }], odd: [] },
  } as unknown as Analysis;

  it("asks only for damage types that have prices", () => {
    expect(missingChoices(analysis, {})).toEqual(["Dent"]);
    expect(
      missingChoices(analysis, { dent: { damage_type: "dent", method_id: 5, quantity: 1, excluded: false } }),
    ).toEqual([]);
    expect(
      missingChoices(analysis, { dent: { damage_type: "dent", method_id: null, quantity: 1, excluded: true } }),
    ).toEqual([]);
  });
});

import { placeTags } from "./components/PhotoFrame";
import type { Detection } from "./types";

describe("placeTags", () => {
  const det = (id: number, x1: number, y1: number, x2: number, y2: number) =>
    ({ id, label: "Scratch", confidence: 50, box: { x1, y1, x2, y2 } }) as Detection;

  it("keeps labels inside the image and apart when boxes are close", () => {
    const tags = placeTags([det(1, 100, 100, 300, 200), det(2, 110, 110, 300, 220)], 800, 600, 20);
    const a = tags.get(1)!;
    const b = tags.get(2)!;
    const apart = a.y + a.h <= b.y || b.y + b.h <= a.y || a.x + a.w <= b.x || b.x + b.w <= a.x;
    expect(apart).toBe(true);
    for (const t of [a, b]) {
      expect(t.x).toBeGreaterThanOrEqual(0);
      expect(t.x + t.w).toBeLessThanOrEqual(800);
      expect(t.y).toBeGreaterThanOrEqual(0);
    }
  });

  it("puts the label inside the box when the box touches the top edge", () => {
    expect(placeTags([det(1, 10, 0, 200, 100)], 800, 600, 20).get(1)!.y).toBe(0);
  });
});
