# 架构（ARCHITECTURE）

```
                ┌──────────────┐
   定时/手动 ──▶ │  pipeline.py │  (编排入口: run_once)
                └──────┬───────┘
        ┌──────────────┼───────────────────────────────┐
        ▼              ▼                               ▼
  ┌──────────┐  ┌─────────────┐                ┌──────────────┐
  │ httpclient│  │  connectors │                │   config/    │
  │(SSRF防护) │  │ RSS/Atom/   │◀── sources.yaml │ sources/     │
  └────┬─────┘  │ GH Atom/HN/ │                │ scoring.yaml │
       │        │ arXiv/API   │                └──────────────┘
       ▼        └──────┬──────┘
  原始字节 ──────────▶ 条目(dict, camelCase)
                          │
            ┌─────────────┼─────────────────────────┐
            ▼             ▼                         ▼
      ┌──────────┐ ┌──────────┐              ┌──────────────┐
      │ normalize│ │ entities │              │  dedupe      │
      │(URL/时间)│ │(产品/版本)│              │(近重复判定)  │
      └────┬─────┘ └────┬─────┘              └──────┬───────┘
           └────────────┼───────────────────────────┘
                        ▼
                 ┌──────────────┐
                 │   cluster    │  并查集合并 → Story
                 │ (+overrides) │
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │   score      │  热度/重要度/可信度
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │    build     │  → public/data/*.json
                 └──────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  web/ (Next) │  静态导出 → web/out/
                 │  消费 JSON   │
                 └──────────────┘
```

## 数据契约（camelCase，见任务书 §7）
- **Source**: id, name, type, role, trustTier, url, category, language, pollMinutes, enabled,
  lastSuccessAt, healthStatus, lastHttpStatus, lastItemCount, consecutiveFailures, lastError
- **Item**: id, sourceId, externalId, canonicalUrl, titleOriginal, titleZh, excerpt, author,
  language, publishedAt, discoveredAt, contentHash, category, entities[], metrics{}, sourceRole, trustTier
- **Story**: id, slug, headline, headlineZh, whatHappened, whyItMatters, category, entities[],
  firstSeenAt, lastUpdatedAt, status, heatScore, importanceScore, confidenceScore,
  rankingReasons[], itemIds[], primaryItemId, claims[], summaryVersion

## 产物（public/data）
`manifest.json` `stories.json` `hot.json` `latest-selected.json` `latest-all.json`
`source-status.json` `search-index.json` `daily/YYYY-MM-DD.json`
