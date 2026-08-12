export type StoryStatus = "new" | "warming" | "hot" | "cooling" | "archived" | "disputed";

export interface Claim {
  text: string;
  supportingItemIds: string[];
}

export interface Story {
  id: string;
  slug: string;
  headline: string;
  headlineZh: string;
  whatHappened: string;
  whyItMatters: string;
  category: string;
  entities: string[];
  firstSeenAt: string;
  lastUpdatedAt: string;
  status: StoryStatus;
  heatScore: number;
  importanceScore: number;
  confidenceScore: number;
  rankingReasons: string[];
  itemIds: string[];
  primaryItemId: string;
  claims: Claim[];
  summaryVersion: string;
}

export interface Source {
  id: string;
  name: string;
  type: string;
  role: string;
  trustTier: number;
  url: string;
  category: string;
  language: string;
  pollMinutes: number;
  enabled: boolean;
  lastSuccessAt?: string | null;
  healthStatus: string;
  lastHttpStatus?: number | null;
  lastItemCount?: number;
  consecutiveFailures?: number;
  lastError?: string;
}

export interface SearchEntry {
  type: "story" | "item";
  id: string;
  slug?: string;
  title: string;
  category: string;
  text: string;
  sourceId?: string;
}

export interface Envelope<T> {
  schemaVersion: string;
  generatedAt: string;
  window: { start: string; end: string; hours?: number };
  storyCount?: number;
  sourceCount?: number;
  entryCount?: number;
  data: T[];
}
