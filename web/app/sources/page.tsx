"use client";

import { useEffect, useState } from "react";
import type { Envelope, Source } from "@/lib/types";
import { loadSources, fmtTime } from "@/lib/api";

const HEALTH: Record<string, string> = {
  ok: "bg-green-50 text-green-700 border-green-200",
  degraded: "bg-amber-50 text-amber-700 border-amber-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  unknown: "bg-slate-100 text-slate-500 border-slate-200",
};

const ROLE_LABEL: Record<string, string> = { primary: "一手", media: "媒体", aggregator: "聚合" };

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const s = await loadSources();
        setSources((s.data as Source[]).slice().sort((a, b) => a.name.localeCompare(b.name)));
      } finally { setLoading(false); }
    })();
  }, []);

  return (
    <div>
      <h1 className="text-xl font-bold mb-1">来源</h1>
      <p className="text-sm text-muted mb-4">当前 {sources.length} 个来源 · 一手来源优先</p>
      {loading && <p className="text-muted text-sm">加载中…</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {sources.map((s) => (
          <div key={s.id} className="bg-white border border-line rounded-xl p-3">
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm">{s.name}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full border ${HEALTH[s.healthStatus] || ""}`}>
                {s.healthStatus}
              </span>
            </div>
            <div className="text-xs text-muted mt-1 flex flex-wrap gap-x-3">
              <span>类型 {s.type}</span>
              <span>角色 {ROLE_LABEL[s.role] || s.role}</span>
              <span>信任 T{s.trustTier}</span>
            </div>
            <div className="text-xs text-muted mt-1">近期条目 {s.lastItemCount ?? 0} · 更新 {fmtTime(s.lastSuccessAt)}</div>
            {s.lastError && <div className="text-xs text-red-600 mt-1 truncate">{s.lastError}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
