import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Analysis, Health, Report, Selection } from "../types";
import { percent, units } from "../format";
import { PhotoFrame } from "./PhotoFrame";
import { DetectionList } from "./DetectionList";
import { RepairChooser } from "./RepairChooser";
import { ReportView } from "./ReportView";

const STEPS = ["Upload a photo", "Detect damage", "Choose repairs", "Get the report"];
const IMAGE_EXT = /\.(jpe?g|png|webp|bmp)$/i;

/** Damage types that still need a repair choice (types with no prices need none). */
export function missingChoices(analysis: Analysis, selections: Record<string, Selection>): string[] {
  return analysis.summary.by_type
    .filter((t) => (analysis.repair_options[t.damage_type] ?? []).length > 0)
    .filter((t) => {
      const s = selections[t.damage_type];
      return !s || (!s.excluded && s.method_id == null);
    })
    .map((t) => t.label);
}

export function Estimate({ health }: { health: Health | null }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(25);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [selections, setSelections] = useState<Record<string, Selection>>({});
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState<"detect" | "report" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [highlight, setHighlight] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const thresholdSet = useRef(false);

  useEffect(() => {
    if (health && !thresholdSet.current) {
      setThreshold(Math.round(health.default_confidence * 100));
      thresholdSet.current = true;
    }
  }, [health]);

  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview);
  }, [preview]);

  const step = report ? 4 : analysis ? 3 : file ? 2 : 1;
  const modelMissing = health?.status === "model_missing";

  function choose(f: File | undefined | null) {
    if (!f) return;
    if (!f.type.startsWith("image/") && !IMAGE_EXT.test(f.name)) {
      setError(`${f.name} isn't an image. Choose a JPEG, PNG, WebP or BMP photo.`);
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setAnalysis(null);
    setSelections({});
    setReport(null);
    setError(null);
    setHighlight(null);
  }

  async function detect() {
    if (!file) return;
    setBusy("detect");
    setError(null);
    try {
      const result = await api.analyse(file, threshold / 100);
      setAnalysis(result);
      setSelections({});
      setReport(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function createReport() {
    if (!analysis) return;
    setBusy("report");
    setError(null);
    try {
      const chosen = Object.values(selections).filter((s) => s.excluded || s.method_id != null);
      const result = await api.createReport(analysis.id, chosen);
      setReport(result);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  function restart() {
    setFile(null);
    setPreview(null);
    setAnalysis(null);
    setSelections({});
    setReport(null);
    setError(null);
    if (input.current) input.current.value = "";
  }

  const missing = analysis ? missingChoices(analysis, selections) : [];

  return (
    <div className={`estimate${report ? " is-report" : ""}`}>
      <ol className="steps" aria-label="Progress">
        {STEPS.map((label, i) => {
          const n = i + 1;
          const state = n < step ? "done" : n === step ? "current" : "todo";
          return (
            <li key={label} className={`step is-${state}`} aria-current={state === "current" ? "step" : undefined}>
              <span className="step-n">{n}</span>
              {label}
            </li>
          );
        })}
      </ol>

      {report ? (
        <ReportView report={report} onNew={restart} />
      ) : (
        <div className="workspace">
          <section
            className={`stage${dragging ? " is-dragging" : ""}`}
            aria-label="Photo"
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              choose(e.dataTransfer.files?.[0]);
            }}
          >
            <input
              ref={input}
              id="photo-input"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/bmp"
              className="visually-hidden"
              onChange={(e) => choose(e.target.files?.[0])}
            />
            {!preview ? (
              <label htmlFor="photo-input" className="dropzone">
                <svg viewBox="0 0 120 64" className="dropzone-art" aria-hidden="true">
                  <path
                    d="M8 46h104M14 46c0-8 4-12 12-14l14-12c3-3 7-4 11-4h22c4 0 7 2 10 4l12 12c9 1 15 5 15 14"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  />
                  <circle cx="34" cy="47" r="8" fill="none" stroke="currentColor" strokeWidth="2.5" />
                  <circle cx="88" cy="47" r="8" fill="none" stroke="currentColor" strokeWidth="2.5" />
                  <rect x="54" y="25" width="22" height="16" fill="none" stroke="#FFCC00" strokeWidth="2.5" strokeDasharray="4 3" />
                </svg>
                <span className="dropzone-title">Drop a photo of the damage here</span>
                <span className="dropzone-hint">or click to choose one. JPEG, PNG, WebP or BMP.</span>
              </label>
            ) : (
              <>
                <PhotoFrame
                  src={analysis ? analysis.image_url : preview}
                  alt={file ? `Uploaded photo ${file.name}` : "Uploaded photo"}
                  width={analysis?.image_width}
                  height={analysis?.image_height}
                  detections={analysis?.detections}
                  highlighted={highlight}
                  onHighlight={setHighlight}
                />
                <div className="stage-bar">
                  <span className="truncate">{file?.name}</span>
                  <label htmlFor="photo-input" className="link-button">
                    Use a different photo
                  </label>
                </div>
              </>
            )}
            {busy === "detect" && (
              <div className="scanning" role="status">
                <span>Looking for damage…</span>
              </div>
            )}
          </section>

          <section className="panel" aria-label="Estimate">
            {modelMissing && (
              <div className="alert" role="alert">
                <strong>The damage model isn't loaded.</strong> {health?.model.error} Then restart the backend.
              </div>
            )}
            {error && (
              <div className="alert" role="alert">
                {error}
              </div>
            )}

            {!file && (
              <div className="intro">
                <h2>Estimate a repair from a photo</h2>
                <p>
                  The model looks for six kinds of damage: dents, scratches, cracks, shattered glass, broken
                  lamps and flat tyres. You then choose how each would be repaired, and the app prices it from
                  a database of published UK repair costs.
                </p>
                <p className="muted">A clear, close photo of one damaged area works best.</p>
              </div>
            )}

            {file && (
              <div className="detect-controls">
                <div className="threshold">
                  <label htmlFor="threshold">Detection threshold</label>
                  <output htmlFor="threshold">{threshold}%</output>
                  <input
                    id="threshold"
                    type="range"
                    min={5}
                    max={95}
                    step={5}
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value))}
                    aria-describedby="threshold-hint"
                  />
                  <p id="threshold-hint" className="hint">
                    Boxes below this confidence are hidden. Lower it to find more damage, with more false alarms.
                  </p>
                </div>
                <button
                  type="button"
                  className={analysis ? "btn" : "btn btn-primary"}
                  onClick={detect}
                  disabled={busy !== null || modelMissing}
                >
                  {busy === "detect" ? "Detecting…" : analysis ? "Detect again" : "Detect damage"}
                </button>
              </div>
            )}

            {analysis && (
              <>
                <div className="result-head">
                  <h2>
                    {analysis.summary.total_detections === 0
                      ? "No damage found"
                      : `${units(analysis.summary.total_detections, "damage area")} found`}
                  </h2>
                  <p
                    className={`priority${analysis.summary.inspection_priority === "Prompt inspection" ? " is-alert" : ""}`}
                  >
                    {analysis.summary.inspection_priority}
                  </p>
                </div>

                {analysis.summary.total_detections === 0 ? (
                  <p>
                    Nothing scored above {threshold}%. Lower the threshold and detect again, or try a closer photo
                    of the damaged area.
                  </p>
                ) : (
                  <>
                    <p className="muted small">
                      Highest confidence {percent(analysis.summary.highest_confidence)}, average{" "}
                      {percent(analysis.summary.average_confidence)}. Dashed boxes are below 50%. Severity isn't
                      assessed by the model.
                    </p>
                    <DetectionList
                      detections={analysis.detections}
                      highlighted={highlight}
                      onHighlight={setHighlight}
                    />
                    <h2 className="choose-title">Choose a repair for each type of damage</h2>
                    <RepairChooser
                      analysis={analysis}
                      selections={selections}
                      onChange={(type, next) => setSelections((s) => ({ ...s, [type]: next }))}
                    />
                  </>
                )}

                <div className="report-cta">
                  <button
                    type="button"
                    className="btn btn-primary btn-large"
                    onClick={createReport}
                    disabled={busy !== null || missing.length > 0}
                    aria-describedby="report-cta-hint"
                  >
                    {busy === "report" ? "Creating report…" : "Create repair-cost report"}
                  </button>
                  <p id="report-cta-hint" className="hint">
                    {missing.length > 0
                      ? `Choose a repair, or leave out, for: ${missing.join(", ")}.`
                      : "Prices come from the UK repair-cost database, with their sources."}
                  </p>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
