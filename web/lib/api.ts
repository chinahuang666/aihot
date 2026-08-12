import type { Envelope, Story, Source, SearchEntry } from "./types";

const BASE = "/data";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}/${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to load ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export const loadManifest = () => getJSON<any>("manifest.json");
export const loadStories = () => getJSON<Envelope<Story>>("stories.json");
export const loadSelected = () => getJSON<Envelope<Story>>("latest-selected.json");
export const loadHot = () => getJSON<Envelope<Story>>("hot.json");
export const loadSources = () => getJSON<Envelope<Source>>("source-status.json");
export const loadSearchIndex = () => getJSON<Envelope<SearchEntry>>("search-index.json");
export const loadDaily = (file: string) => getJSON<Envelope<Story>>(`daily/${file}`);

// ---- formatting helpers ----
export function fmtTime(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function relTime(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso).getTime();
  if (isNaN(d)) return "";
  const diff = Date.now() - d;
  const m = Math.floor(diff / 60000);
  if (m < 1) return "刚刚";
  if (m < 60) return `${m} 分钟前`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} 小时前`;
  const day = Math.floor(h / 24);
  return `${day} 天前`;
}

export function scorePct(n: number): number {
  return Math.round(Math.max(0, Math.min(1, n)) * 100);
}

export const CATEGORY_LABEL: Record<string, string> = {
  model: "模型",
  product: "产品",
  developer: "开发者",
  research: "研究",
  industry: "行业",
  safety: "安全",
};

export const STATUS_LABEL: Record<string, string> = {
  new: "新",
  warming: "升温",
  hot: "热门",
  cooling: "降温",
  archived: "归档",
  disputed: "争议",
};

export function combinedScore(s: Story): number {
  return 0.4 * s.heatScore + 0.4 * s.importanceScore + 0.2 * s.confidenceScore;
}
