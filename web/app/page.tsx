"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { Envelope, Story, Source, SearchEntry } from "@/lib/types";
import { loadStories, loadSearchIndex, loadSources, combinedScore, CATEGORY_LABEL } from "@/lib/api";
import { StoryCard } from "@/components/StoryCard";

interface ItemInfo {
  title: string;
  sourceId?: string;
  text?: string;
}

export default function HomePage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [itemMap, setItemMap] = useState<Map<string, ItemInfo>>(new Map());
  const [sourceMap, setSourceMap] = useState<Map<string, Source>>(new Map());
  const [cat, setCat] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [st, idx, src] = await Promise.all([
          loadStories(),
          loadSearchIndex(),
          loadSources(),
        ]);
        const im = new Map<string, ItemInfo>();
        for (const e of (idx.data as SearchEntry[])) {
          if (e.type === "item") im.set(e.id, { title: e.title, sourceId: e.sourceId, text: e.text });
        }
        const sm = new Map<string, Source>();
        for (const s of (src.data as Source[])) sm.set(s.id, s);
        const list = (st.data as Story[]).slice().sort((a, b) => combinedScore(b) - combinedScore(a));
        setStories(list);
        setItemMap(im);
        setSourceMap(sm);
      } catch (e: any) {
        setErr(String(e?.message || e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const cats = useMemo(() => {
    const s = new Set(stories.map((x) => x.category));
    return ["all", ...Array.from(s)];
  }, [stories]);

  const filtered = useMemo(
    () => (cat === "all" ? stories : stories.filter((s) => s.category === cat)),
    [stories, cat]
  );

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
        <div>
          <h1 className="text-xl font-bold">AI 信号板</h1>
          <p className="text-sm text-muted">同一事件多源去重 · 信号可展开 · 规则摘要</p>
        </div>
        <Link href="/search" className="text-sm text-brand hover:underline shrink-0">
          搜索 →
        </Link>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {cats.map((c) => (
          <button
            key={c}
            onClick={() => setCat(c)}
            className={`px-3 py-1 rounded-full text-sm border ${
              cat === c ? "bg-brand text-white border-brand" : "bg-white text-muted border-line hover:border-brand"
            }`}
          >
            {c === "all" ? "全部" : CATEGORY_LABEL[c] || c}
          </button>
        ))}
      </div>

      {loading && <p className="text-muted text-sm">加载中…</p>}
      {err && <p className="text-red-600 text-sm">加载失败：{err}</p>}
      {!loading && !err && filtered.length === 0 && <p className="text-muted text-sm">暂无数据。</p>}

      <div className="space-y-3">
        {filtered.map((s) => (
          <StoryCard key={s.id} story={s} itemMap={itemMap} sourceMap={sourceMap} />
        ))}
      </div>
    </div>
  );
}
