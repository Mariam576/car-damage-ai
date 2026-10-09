import type { Report, Source } from "../types";
import { damageColour, date, dateTime, money, percent, range, units } from "../format";
import { PhotoFrame } from "./PhotoFrame";

interface Props {
  report: Report;
  onNew?: () => void;
}

function uniqueSources(report: Report): Source[] {
  const seen = new Map<string, Source>();
  for (const line of report.lines) if (!seen.has(line.source.url)) seen.set(line.source.url, line.source);
  return [...seen.values()];
}

function download(report: Report) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${report.id}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportView({ report, onNew }: Props) {
  const sources = uniqueSources(report);
  const prompt = report.inspection_priority === "Prompt inspection";
  const t = report.totals;

  return (
    <article className="report" aria-labelledby="report-title">
      <header className="report-head">
        <div>
          <h2 id="report-title">Repair-cost estimate</h2>
          <p className="report-ref">
            <span>Report {report.id}</span>
            <span>{dateTime(report.created_at)}</span>
            <span>Photo: {report.image_name}</span>
          </p>
        </div>
        <div className="report-actions no-print">
          <button type="button" className="btn btn-primary" onClick={() => window.print()}>
            Print or save as PDF
          </button>
          <button type="button" className="btn" onClick={() => download(report)}>
            Download JSON
          </button>
          {onNew && (
            <button type="button" className="btn btn-quiet" onClick={onNew}>
              Start a new estimate
            </button>
          )}
        </div>
      </header>

      <section className="report-total" aria-label="Estimated total">
        <div className="total-figure">
          <span className="total-label">Estimated repair cost</span>
          <strong className="total-range">{range(t.min_gbp, t.max_gbp, t.max_open)}</strong>
          <span className="total-mid">
            Midpoint {money(t.midpoint_gbp)}
            {t.max_open && ", upper figure open-ended"}
          </span>
        </div>
        <dl className="total-facts">
          <div>
            <dt>Inspection priority</dt>
            <dd className={prompt ? "is-alert" : undefined}>{report.inspection_priority}</dd>
          </div>
          <div>
            <dt>Physical severity</dt>
            <dd>{report.physical_severity}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{report.estimate_status}</dd>
          </div>
        </dl>
      </section>

      <div className="report-body">
        <figure className="report-photo">
          <PhotoFrame
            src={report.image_url}
            alt={`Photo ${report.image_name} with detected damage`}
            width={report.image_width}
            height={report.image_height}
            detections={report.detections}
            compact
          />
          <figcaption>
            {report.model_name}, threshold {Math.round(report.confidence_threshold * 100)}%
          </figcaption>
        </figure>

        <section className="report-detections">
          <h3>Detected damage</h3>
          {report.detections.length === 0 ? (
            <p className="muted">The model found no damage in this photo.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Damage</th>
                  <th scope="col" className="num">Confidence</th>
                  <th scope="col" className="num">Photo coverage</th>
                </tr>
              </thead>
              <tbody>
                {report.detections.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <span className="swatch" style={{ background: damageColour(d.damage_type) }}>
                        {d.id}
                      </span>
                    </td>
                    <td>{d.label}</td>
                    <td className="num">{percent(d.confidence)}</td>
                    <td className="num">{percent(d.coverage_pct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      <section>
        <h3>Repairs</h3>
        {report.lines.length === 0 ? (
          <p className="muted">No repairs were priced.</p>
        ) : (
          <div className="table-scroll">
            <table className="table repairs">
              <thead>
                <tr>
                  <th scope="col">Damage</th>
                  <th scope="col">Repair method</th>
                  <th scope="col" className="num">Quantity</th>
                  <th scope="col" className="num">Price each</th>
                  <th scope="col" className="num">Cost range</th>
                  <th scope="col" className="num">Midpoint</th>
                  <th scope="col">UK price source</th>
                </tr>
              </thead>
              <tbody>
                {report.lines.map((l) => (
                  <tr key={l.damage_type}>
                    <td>
                      <span className="dot" style={{ background: damageColour(l.damage_type) }} />
                      {l.label}
                    </td>
                    <td>
                      <strong>{l.method}</strong>
                      <span className="cell-note">{l.description}</span>
                    </td>
                    <td className="num">{units(l.quantity, l.unit)}</td>
                    <td className="num">{range(l.unit_min_gbp, l.unit_max_gbp, l.max_open)}</td>
                    <td className="num strong">{range(l.min_gbp, l.max_gbp, l.max_open)}</td>
                    <td className="num">{money(l.midpoint_gbp)}</td>
                    <td>
                      <a href={l.source.url} target="_blank" rel="noreferrer">
                        {l.source.publisher}
                      </a>
                      <span className="cell-note">{l.source.note}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row" colSpan={4}>
                    Total
                  </th>
                  <td className="num strong">{range(t.min_gbp, t.max_gbp, t.max_open)}</td>
                  <td className="num strong">{money(t.midpoint_gbp)}</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        )}

        {(report.excluded.length > 0 || report.unpriced.length > 0) && (
          <ul className="report-notes">
            {report.excluded.map((e) => (
              <li key={e.damage_type}>
                <strong>{e.label}</strong> ({units(e.detections, "detection")}) left out: {e.note}.
              </li>
            ))}
            {report.unpriced.map((u) => (
              <li key={u.damage_type}>
                <strong>{u.label}</strong> ({units(u.detections, "detection")}): {u.note}; no UK price in the
                database.
              </li>
            ))}
          </ul>
        )}
      </section>

      {sources.length > 0 && (
        <section>
          <h3>Price sources</h3>
          <ol className="sources">
            {sources.map((s) => (
              <li key={s.url}>
                {s.publisher}, “{s.title}”
                {s.published && `, published ${date(s.published)}`}
                {s.updated && `, updated ${date(s.updated)}`}. Read {date(s.retrieved_on)}.{" "}
                <a href={s.url} target="_blank" rel="noreferrer" className="source-url">
                  {s.url}
                </a>
              </li>
            ))}
          </ol>
        </section>
      )}

      <p className="disclaimer">{report.disclaimer}</p>
    </article>
  );
}
