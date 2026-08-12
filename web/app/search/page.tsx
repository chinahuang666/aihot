"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import MiniSearch from "minisearch";
import type { Envelope, SearchEntry } from "@/lib/types";
import { loadSearchIndex } from "@/lib/api";

function SearchInner() {
  const params = useSearchParams();
  const router = useRouter();
  const initial = params.get("q") || "";
  const [query, setQuery] = useState(initial);
  const [mini, setMini] = useState<MiniSearch | null>(null);
  const [results, setResults] = useState<SearchEntry[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const idx = await loadSearchIndex();
        const data = idx.data as SearchEntry[];
        const ms = new MiniSearch({
          fields: ["title", "text", "category"],
          storeFields: ["title", "text", "category", "type", "id", "sourceId"],
          tokenize: (s) => s.toLowerCase().split(/[\s\-_.，。、/]+/),
        });
        ms.addAll(data);
        setMini(ms);
      } catch {
        /* ignore */
      }
    })();
  }, []);

  useEffect(() => {
    if (!query.trim()) { setResults([]); return; }
    if (!mini) return;
    const r = mini
      .search(query.trim(), { prefix: true, fuzzy: 0.2 })
      .map((m: any) => ({
        type: m.type, id: m.id, title: m.title, text: m.text,
        category: m.category, sourceId: m.sourceId,
      })) as SearchEntry[];
    setResults(r);
  }, [query, mini]);

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold mb-3">搜索</h1>
      <input
        autoFocus
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          router.replace(`/search?q=${encodeURIComponent(e.target.value)}`);
        }}
        placeholder="搜索事件、模型、来源…"
        className="w-full border border-line rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand"
      />

      {query.trim() && <p className="text-sm text-muted mt-3">{results.length} 条结果</p>}

      <ul className="mt-3 divide-y divide-line border border-line rounded-xl bg-white">
        {results.map((r, i) => (
          <li key={i} className="p-3">
            {r.type === "story" ? (
              <Link href={`/story?id=${r.id}`} className="block hover:text-brand">
                <div className="text-sm font-medium">{r.title}</div>
                <div className="text-xs text-muted line-clamp-1">{r.text}</div>
              </Link>
            ) : (
              <div className="text-sm">
                <span className="text-xs text-muted mr-2">[{r.sourceId}]</span>
                {r.title}
              </div>
            )}
          </li>
        ))}
        {query.trim() && results.length === 0 && (
          <li className="p-3 text-sm text-muted">无匹配结果。</li>
        )}
      </ul>

      {!query.trim() && (
        <p className="text-sm text-muted mt-4">输入关键词以检索事件与来源。</p>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<p className="text-muted text-sm">加载中…</p>}>
      <SearchInner />
    </Suspense>
  );
}
