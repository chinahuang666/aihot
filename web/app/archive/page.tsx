"use client";

import { useEffect, useState } from "react";
import type { Envelope, Story, Source, SearchEntry } from "@/lib/types";
import { loadStories, loadSearchIndex, loadSources, combinedScore } from "@/lib/api";
import { StoryCard } from "@/components/StoryCard";

interface ItemInfo { title: string; sourceId?: string; text?: string; }

export default function ArchivePage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [itemMap, setItemMap] = useState<Map<string, ItemInfo>>(new Map());
  const [sourceMap, setSourceMap] = useState<Map<string, Source>>(new Map());
  const [label, setLabel] = useState("今日日报");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const today = new Date().toISOString().slice(0, 10);
        let data: Story[] = [];
        try {
          const d = await fetch(`/data/daily/${today}.json`, { cache: "no-store" });
          if (d.ok) {
            const env = (await d.json()) as Envelope<Story>;
            data = env.data as Story[];
            setLabel(`日报 ${today}`);
          }
        } catch { /* fall back */ }
        if (data.length === 0) {
          const st = await loadStories();
          data = (st.data as Story[]).slice().sort((a, b) => combinedScore(b) - combinedScore(a));
          setLabel("最新精选");
        }
        const idx = await loadSearchIndex();
        const im = new Map<string, ItemInfo>();
        for (const e of idx.data as SearchEntry[]) if (e.type === "item") im.set(e.id, { title: e.title, sourceId: e.sourceId, text: e.text });
        const sm = new Map<string, Source>();
        const src = await loadSources();
        for (const s of src.data as Source[]) sm.set(s.id, s);
        setStories(data);
        setItemMap(im); setSourceMap(sm);
      } finally { setLoading(false); }
    })();
  }, []);

  return (
    <div>
      <h1 className="text-xl font-bold mb-1">日报</h1>
      <p className="text-sm text-muted mb-4">{label} · 按综合信号排序</p>
      {loading && <p className="text-muted text-sm">加载中…</p>}
      <div className="space-y-3">
        {stories.map((s) => <StoryCard key={s.id} story={s} itemMap={itemMap} sourceMap={sourceMap} />)}
      </div>
    </div>
  );
}
