import type { Analysis, DamageClass, Health, Report, ReportListItem, Selection } from "./types";

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new ApiError(
      "Can't reach the API. Start the backend (uvicorn app.main:app --port 8000) and try again.",
      0,
    );
  }
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) {
        detail = body.detail.map((d: { msg?: string }) => d.msg ?? "").filter(Boolean).join("; ");
      }
    } catch {
      /* not JSON */
    }
    throw new ApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),
  damageClasses: () => request<DamageClass[]>("/api/damage-classes"),

  analyse(file: File, confidence: number) {
    const form = new FormData();
    form.append("image", file);
    form.append("confidence", String(confidence));
    return request<Analysis>("/api/analyses", { method: "POST", body: form });
  },

  createReport(analysisId: string, selections: Selection[]) {
    return request<Report>("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis_id: analysisId, selections }),
    });
  },

  report: (id: string) => request<Report>(`/api/reports/${encodeURIComponent(id)}`),
  reports: () => request<ReportListItem[]>("/api/reports"),
};
