export interface GalleryImage {
  filename: string;
  path: string;
  date: string;
  size_kb: number;
}

export interface QualityScore {
  overall: number;
  skin_realism: number;
  face_consistency: number;
  lighting_quality: number;
  composition: number;
  issues?: string[];
  recommendations?: string[];
}

export type LogEntryType = "info" | "success" | "warning" | "error";

export interface LogEntry {
  id: string;
  timestamp: string;
  agent: string;
  message: string;
  type: LogEntryType;
}

export const INFLUENCERS = [
  { id: "luna_vale", name: "Luna Vale", niche: "Production Ready", color: "text-purple-400" },
  { id: "starbright_monroe", name: "Starbright Monroe", niche: "Training", color: "text-cyan-400" }
];

export const getApiBase = (backendUrl: string) => {
  if (backendUrl) {
    return backendUrl.replace(/\/$/, "");
  }
  return window.location.origin;
};
