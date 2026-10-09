import type { Analysis, Selection } from "../types";
import { damageColour, percent, range, sourceDate, units } from "../format";
import { RangeBar, scaleFor } from "./RangeBar";

interface Props {
  analysis: Analysis;
  selections: Record<string, Selection>;
  onChange: (damageType: string, next: Selection) => void;
}

const UNIT_HEADINGS: Record<string, string> = {
  panel: "Panels to repair",
  dent: "Dents to repair",
  windscreen: "Windscreens",
  lamp: "Lamps to replace",
  tyre: "Tyres",
};

export function RepairChooser({ analysis, selections, onChange }: Props) {
  return (
    <div className="chooser">
      {analysis.summary.by_type.map((t) => {
        const options = analysis.repair_options[t.damage_type] ?? [];
        const sel = selections[t.damage_type];
        const chosen = options.find((m) => m.id === sel?.method_id);
        const scale = scaleFor(options);
        const colour = damageColour(t.damage_type);
        const group = `repair-${t.damage_type.replace(/\s+/g, "-")}`;

        return (
          <fieldset key={t.damage_type} className="repair-group" style={{ borderLeftColor: colour }}>
            <legend>
              <span className="repair-title">{t.label}</span>
              <span className="repair-meta">
                {units(t.count, "area")} detected, highest confidence {percent(t.max_confidence)}
              </span>
              {t.safety_related && <span className="tag tag-alert">Safety item</span>}
            </legend>

            {options.length === 0 ? (
              <p className="muted">
                The price database has no repair methods for this damage type. It will be listed in
                the report for professional assessment.
              </p>
            ) : (
              <>
                {options.map((m) => {
                  const checked = !sel?.excluded && sel?.method_id === m.id;
                  return (
                    <label key={m.id} className={`option${checked ? " is-checked" : ""}`}>
                      <input
                        type="radio"
                        name={group}
                        checked={checked}
                        onChange={() =>
                          onChange(t.damage_type, {
                            damage_type: t.damage_type,
                            method_id: m.id,
                            excluded: false,
                            quantity: sel?.quantity ?? 1,
                          })
                        }
                      />
                      <span className="option-body">
                        <span className="option-head">
                          <span className="option-name">{m.method}</span>
                          <span className="option-price">
                            {range(m.min_gbp, m.max_gbp, m.max_open)}
                            <span className="per"> per {m.unit}</span>
                          </span>
                        </span>
                        <RangeBar
                          min={m.min_gbp}
                          max={m.max_gbp}
                          open={m.max_open}
                          scaleMax={scale}
                          colour={checked ? colour : undefined}
                        />
                        <span className="option-desc">{m.description}</span>
                        <span className="option-source">
                          <a href={m.source.url} target="_blank" rel="noreferrer">
                            {sourceDate(m.source)}
                          </a>
                          {checked && <span className="source-note">{m.source.note}</span>}
                        </span>
                      </span>
                    </label>
                  );
                })}

                <label className={`option option-exclude${sel?.excluded ? " is-checked" : ""}`}>
                  <input
                    type="radio"
                    name={group}
                    checked={Boolean(sel?.excluded)}
                    onChange={() =>
                      onChange(t.damage_type, {
                        damage_type: t.damage_type,
                        method_id: null,
                        excluded: true,
                        quantity: 1,
                      })
                    }
                  />
                  <span className="option-body">
                    <span className="option-name">Leave out of the estimate</span>
                    <span className="option-desc">For a false detection, or damage that won't be repaired.</span>
                  </span>
                </label>

                {chosen && sel && (
                  <div className="qty">
                    <span id={`${group}-qty`}>{UNIT_HEADINGS[chosen.unit] ?? "Quantity"}</span>
                    <div className="stepper" role="group" aria-labelledby={`${group}-qty`}>
                      <button
                        type="button"
                        aria-label="One fewer"
                        disabled={sel.quantity <= 1}
                        onClick={() => onChange(t.damage_type, { ...sel, quantity: sel.quantity - 1 })}
                      >
                        −
                      </button>
                      <output aria-live="polite">{sel.quantity}</output>
                      <button
                        type="button"
                        aria-label="One more"
                        disabled={sel.quantity >= 20}
                        onClick={() => onChange(t.damage_type, { ...sel, quantity: sel.quantity + 1 })}
                      >
                        +
                      </button>
                    </div>
                    <span className="qty-total">
                      {range(chosen.min_gbp * sel.quantity, chosen.max_gbp * sel.quantity, chosen.max_open)}
                    </span>
                  </div>
                )}
              </>
            )}
          </fieldset>
        );
      })}
    </div>
  );
}
