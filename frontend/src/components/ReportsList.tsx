import { useEffect, useState } from "react";
import { api } from "../api";
import type { ReportListItem } from "../types";
import { dateTime, range } from "../format";

export function ReportsList() {
  const [items, setItems] = useState<ReportListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reports().then(setItems, (e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="alert" role="alert">{error}</p>;
  if (!items) return <p className="muted">Loading reports…</p>;
  if (items.length === 0) {
    return (
      <div className="empty">
        <p>No reports yet. Reports you create are saved here.</p>
        <a className="btn btn-primary" href="#/">Start an estimate</a>
      </div>
    );
  }

  return (
    <div className="table-scroll">
      <table className="table reports-table">
        <thead>
          <tr>
            <th scope="col">Report</th>
            <th scope="col">Created</th>
            <th scope="col">Photo</th>
            <th scope="col">Damage</th>
            <th scope="col">Priority</th>
            <th scope="col" className="num">Estimate</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id}>
              <td>
                <a href={`#/reports/${r.id}`}>{r.id}</a>
              </td>
              <td>{dateTime(r.created_at)}</td>
              <td className="truncate">{r.image_name}</td>
              <td>{r.damage_types.join(", ") || "None"}</td>
              <td>{r.inspection_priority}</td>
              <td className="num strong">{range(r.total_min_gbp, r.total_max_gbp, r.max_open)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
