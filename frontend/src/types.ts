// Shapes returned by the FastAPI backend (backend/app/main.py).

export interface Source {
  publisher: string;
  title: string;
  url: string;
  published: string | null;
  updated: string | null;
  retrieved_on: string;
  note: string;
}

export interface RepairMethod {
  id: number;
  damage_type: string;
  method: string;
  description: string;
  min_gbp: number;
  max_gbp: number;
  max_open: boolean;
  unit: string;
  source: Source;
}

export interface DamageClass {
  name: string;
  label: string;
  safety_related: boolean;
  repair_methods: RepairMethod[];
}

export interface Box {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Detection {
  id: number;
  damage_type: string;
  label: string;
  confidence: number;
  low_confidence: boolean;
  box: Box;
  width_px: number;
  height_px: number;
  coverage_pct: number;
}

export interface TypeSummary {
  damage_type: string;
  label: string;
  count: number;
  max_confidence: number;
  safety_related: boolean;
}

export interface Summary {
  total_detections: number;
  damage_types: string[];
  by_type: TypeSummary[];
  highest_confidence: number | null;
  average_confidence: number | null;
  largest_coverage_pct: number | null;
  max_overlap_pct: number;
  inspection_priority: string;
  physical_severity: string;
}

export interface Analysis {
  id: string;
  created_at: string;
  image_name: string;
  image_url: string;
  image_width: number;
  image_height: number;
  confidence_threshold: number;
  model_name: string;
  detections: Detection[];
  summary: Summary;
  repair_options: Record<string, RepairMethod[]>;
}

export interface Selection {
  damage_type: string;
  method_id: number | null;
  quantity: number;
  excluded: boolean;
  note?: string;
}

export interface ReportLine {
  damage_type: string;
  label: string;
  detections: number;
  max_confidence: number;
  method_id: number;
  method: string;
  description: string;
  quantity: number;
  unit: string;
  unit_min_gbp: number;
  unit_max_gbp: number;
  max_open: boolean;
  min_gbp: number;
  max_gbp: number;
  midpoint_gbp: number;
  source: Source;
  note: string;
}

export interface Report {
  id: string;
  analysis_id: string;
  created_at: string;
  image_name: string;
  image_url: string;
  image_width: number;
  image_height: number;
  model_name: string;
  confidence_threshold: number;
  detections: Detection[];
  summary: Summary;
  inspection_priority: string;
  physical_severity: string;
  lines: ReportLine[];
  excluded: { damage_type: string; label: string; detections: number; max_confidence: number; note: string }[];
  unpriced: { damage_type: string; label: string; detections: number; note: string }[];
  totals: { currency: "GBP"; min_gbp: number; max_gbp: number; midpoint_gbp: number; max_open: boolean };
  estimate_status: string;
  disclaimer: string;
}

export interface ReportListItem {
  id: string;
  analysis_id: string;
  created_at: string;
  image_name: string;
  total_min_gbp: number;
  total_max_gbp: number;
  max_open: boolean;
  damage_types: string[];
  inspection_priority: string;
}

export interface Health {
  status: "ok" | "model_missing";
  model: { loaded: boolean; model_file: string; classes: string[]; error: string | null };
  database: { path: string; repair_methods: number; sources: number };
  default_confidence: number;
}
