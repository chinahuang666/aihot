"use client";

import { useState } from "react";
import Link from "next/link";
import type { Story, Source, SearchEntry } from "@/lib/types";
import { StatusBadge, CategoryChip, ScoreBars } from "./ui";
import { fmtTime, relTime } from "@/lib/api";

interface ItemInfo {
  title: string;
  sourceId?: string;
  text?: string;
}

export function StoryCard({
  story,
  itemMap,
  sourceMap,
}: {
  story: Story;
  itemMap: Map<string, ItemInfo>;
  sourceMap: Map<string, Source>;
}) {
  const [open, setOpen] = useState(false);
  const sources = story.itemIds
    .map((id) => itemMap.get(id))
    .filter(Boolean) as ItemInfo[];
  const uniqueSources = new Set(sources.map((s) => s.sourceId));

  return (
    <article className="bg-white border border-line rounded-xl p-4 hover:shadow-sm transition">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <StatusBadge status={story.status} />
            <CategoryChip category={story.category} />
            {story.entities.slice(0, 3).map((e) => (
              <span key={e} className="text-xs text-brand">#{e.replace(/^(prod|ver|org):/, "")}</span>
            ))}
          </div>
          <Link href={`/story?id=${story.id}`} className="block">
            <h2 className="text-base sm:text-lg font-semibold leading-snug hover:text-brand">
              {story.headline}
            </h2>
          </Link>
          <p className="text-sm text-muted mt-1 line-clamp-2">{story.whyItMatters}</p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
        <ScoreBars story={story} />
        <div className="text-xs text-muted sm:text-right">
          <div>首发 {fmtTime(story.firstSeenAt)}</div>
          <div>{relTime(story.lastUpdatedAt)}更新 · {uniqueSources.size} 个来源</div>
        </div>
      </div>

      {story.rankingReasons.length > 0 && (
        <ul className="mt-2 text-xs text-muted list-disc list-inside">
          {story.rankingReasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}

      <button
        onClick={() => setOpen((v) => !v)}
        className="mt-3 text-sm text-brand font-medium hover:underline"
      >
        {open ? "收起来源 ▲" : `展开 ${sources.length} 个来源 ▼`}
      </button>

      {open && (
        <ul className="mt-2 divide-y divide-line border-t border-line">
          {sources.map((s, i) => {
            const src = s.sourceId ? sourceMap.get(s.sourceId) : undefined;
            return (
              <li key={i} className="py-2 flex items-start gap-2 text-sm">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-brand shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs text-muted">{src?.name || s.sourceId || "未知来源"}</div>
                  <div className="truncate">{s.title}</div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </article>
  );
}
