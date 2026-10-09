import { useEffect, useState } from "react";
import { api } from "../api";
import type { DamageClass } from "../types";
import { damageColour, range, sourceDate } from "../format";
import { RangeBar, scaleFor } from "./RangeBar";

/** Everything in the SQLite repair-cost database, grouped by damage type. */
export function PriceList() {
  const [classes, setClasses] = useState<DamageClass[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.damageClasses().then(setClasses, (e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="alert" role="alert">{error}</p>;
  if (!classes) return <p className="muted">Loading prices…</p>;

  const scale = scaleFor(classes.flatMap((c) => c.repair_methods));

  return (
    <div className="price-list">
      <p className="lede">
        UK guide prices for each repair the app can suggest, with the page each figure came from. All
        bars share one scale, from £0 to the highest price. Prices are indicative, not quotations.
      </p>
      {classes.map((c) => (
        <section key={c.name} className="price-group" style={{ borderLeftColor: damageColour(c.name) }}>
          <h3>
            {c.label}
            {c.safety_related && <span className="tag tag-alert">Safety item</span>}
          </h3>
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Repair method</th>
                  <th scope="col" className="num">UK price</th>
                  <th scope="col" className="bar-col">
                    <span className="visually-hidden">Range on a shared scale</span>
                  </th>
                  <th scope="col">Source</th>
                </tr>
              </thead>
              <tbody>
                {c.repair_methods.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <strong>{m.method}</strong>
                      <span className="cell-note">{m.description}</span>
                    </td>
                    <td className="num nowrap">
                      {range(m.min_gbp, m.max_gbp, m.max_open)}
                      <span className="cell-note">per {m.unit}</span>
                    </td>
                    <td className="bar-col">
                      <RangeBar min={m.min_gbp} max={m.max_gbp} open={m.max_open} scaleMax={scale} colour={damageColour(c.name)} />
                    </td>
                    <td>
                      <a href={m.source.url} target="_blank" rel="noreferrer">
                        {sourceDate(m.source)}
                      </a>
                      <span className="cell-note">{m.source.note}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
