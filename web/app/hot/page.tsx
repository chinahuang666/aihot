"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Envelope, Story, Source, SearchEntry } from "@/lib/types";
import { loadHot, loadSearchIndex, loadSources } from "@/lib/api";
import { StoryCard } from "@/components/StoryCard";

interface ItemInfo { title: string; sourceId?: string; text?: string; }

export default function HotPage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [itemMap, setItemMap] = useState<Map<string, ItemInfo>>(new Map());
  const [sourceMap, setSourceMap] = useState<Map<string, Source>>(new Map());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [hot, idx, src] = await Promise.all([loadHot(), loadSearchIndex(), loadSources()]);
        const im = new Map<string, ItemInfo>();
        for (const e of idx.data as SearchEntry[]) if (e.type === "item") im.set(e.id, { title: e.title, sourceId: e.sourceId, text: e.text });
        const sm = new Map<string, Source>();
        for (const s of src.data as Source[]) sm.set(s.id, s);
        setStories(hot.data as Story[]);
        setItemMap(im); setSourceMap(sm);
      } finally { setLoading(false); }
    })();
  }, []);

  return (
    <div>
      <h1 className="text-xl font-bold mb-1">热点事件</h1>
      <p className="text-sm text-muted mb-4">按热度（传播速度 × 覆盖 × 互动 × 新鲜度）排序</p>
      {loading && <p className="text-muted text-sm">加载中…</p>}
      <div className="space-y-3">
        {stories.map((s) => <StoryCard key={s.id} story={s} itemMap={itemMap} sourceMap={sourceMap} />)}
      </div>
    </div>
  );
}
