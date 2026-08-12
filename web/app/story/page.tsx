"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import type { Envelope, Story, Source, SearchEntry } from "@/lib/types";
import { loadStories, loadSearchIndex, loadSources, fmtTime, relTime } from "@/lib/api";
import { StatusBadge, CategoryChip, ScoreBars } from "@/components/ui";

function StoryInner() {
  const params = useSearchParams();
  const id = params.get("id") || "";
  const [story, setStory] = useState<Story | null>(null);
  const [itemMap, setItemMap] = useState<Map<string, SearchEntry>>(new Map());
  const [sourceMap, setSourceMap] = useState<Map<string, Source>>(new Map());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      if (!id) { setLoading(false); return; }
      try {
        const [st, idx, src] = await Promise.all([loadStories(), loadSearchIndex(), loadSources()]);
        const im = new Map<string, SearchEntry>();
        for (const e of idx.data as SearchEntry[]) im.set(e.id, e);
        const sm = new Map<string, Source>();
        for (const s of src.data as Source[]) sm.set(s.id, s);
        setStory((st.data as Story[]).find((x) => x.id === id) || null);
        setItemMap(im); setSourceMap(sm);
      } finally { setLoading(false); }
    })();
  }, [id]);

  if (loading) return <p className="text-muted text-sm">加载中…</p>;
  if (!story) return <p className="text-muted text-sm">未找到该事件。<Link href="/" className="text-brand">返回信号板</Link></p>;

  return (
    <div className="max-w-3xl">
      <Link href="/" className="text-sm text-brand hover:underline">← 信号板</Link>
      <div className="flex flex-wrap items-center gap-2 mt-3">
        <StatusBadge status={story.status} />
        <CategoryChip category={story.category} />
        {story.entities.map((e) => (
          <span key={e} className="text-xs text-brand">#{e.replace(/^(prod|ver|org):/, "")}</span>
        ))}
      </div>
      <h1 className="text-2xl font-bold mt-2 leading-snug">{story.headline}</h1>
      <p className="text-muted text-sm mt-1">首发 {fmtTime(story.firstSeenAt)} · {relTime(story.lastUpdatedAt)}更新</p>

      <div className="mt-4 bg-white border border-line rounded-xl p-4">
        <ScoreBars story={story} />
      </div>

      <section className="mt-5">
        <h2 className="font-semibold mb-1">发生了什么</h2>
        <p className="text-sm leading-relaxed">{story.whatHappened}</p>
        <h2 className="font-semibold mt-4 mb-1">为何重要</h2>
        <p className="text-sm leading-relaxed text-muted">{story.whyItMatters}</p>
      </section>

      {story.rankingReasons.length > 0 && (
        <section className="mt-5 bg-slate-50 border border-line rounded-xl p-4">
          <h2 className="font-semibold mb-2 text-sm">排序依据</h2>
          <ul className="text-sm text-muted list-disc list-inside space-y-1">
            {story.rankingReasons.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </section>
      )}

      <section className="mt-5">
        <h2 className="font-semibold mb-2">来源（{story.itemIds.length}）</h2>
        <ul className="divide-y divide-line border border-line rounded-xl bg-white">
          {story.itemIds.map((iid) => {
            const it = itemMap.get(iid);
            const src = it?.sourceId ? sourceMap.get(it.sourceId) : undefined;
            return (
              <li key={iid} className="p-3 flex items-start gap-2">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-brand shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs text-muted">{src?.name || it?.sourceId || "未知来源"}</div>
                  <div className="text-sm">{it?.title || iid}</div>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      {story.claims.length > 0 && (
        <section className="mt-5">
          <h2 className="font-semibold mb-2">关键说法（每条附证据来源）</h2>
          <ul className="space-y-2">
            {story.claims.map((c, i) => (
              <li key={i} className="text-sm bg-white border border-line rounded-lg p-3">
                {c.text}
                <span className="text-muted text-xs ml-2">· 证据 {c.supportingItemIds.length} 条</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

export default function StoryPage() {
  return (
    <Suspense fallback={<p className="text-muted text-sm">加载中…</p>}>
      <StoryInner />
    </Suspense>
  );
}
