# 来源注册表（SOURCES）

来源在 `config/sources.yaml` 中声明，字段：
`id, name, type, url, role, trustTier, language, category, pollMinutes, enabled`。

## 类型（type）→ 连接器
| type | 连接器 | 说明 |
|------|--------|------|
| rss / atom | parse_rss | 通用 RSS/Atom |
| github_release | parse_github_release | GitHub API（需鉴权/受限） |
| github_release_atom | parse_github_atom | **默认**：公开 releases Atom Feed，免鉴权 |
| hn | parse_hn | Hacker News Algolia API |
| arxiv | parse_arxiv | arXiv Atom |
| api | parse_api | 通用 JSON（itemsPath 指定路径） |

## 角色（role）
- `primary`：一手/官方来源（官方博客、GitHub Release）。合并后计入「一手来源」信号。
- `media`：媒体/聚合。
- `aggregator`：二次聚合。

## 信任等级（trustTier 1–3）
用于可信度打分中的「来源权威性」维度。

## 当前来源（21 个，已验证可达）
- 官方/一手：openai_blog, google_ai, deepmind, vllm_rel, ollama_rel, transformers_rel,
  langchain_rel, llamacpp_rel, autogen_rel
- 媒体：theverge_ai, techcrunch_ai, wired_ai, zdnet_ai, venturebeat, marktechpost,
  synced, mit_tech_review, kdnuggets
- 社区/研究：hn_ai, arxiv_ai

## 可靠性要点
- **GitHub Release 走 Atom**：避免 `api.github.com` 60 次/小时未鉴权限额（共享出口 IP 易触顶 403）。
- 健康检查写入 `source-status.json`：`healthStatus ∈ {ok, degraded, failed, unknown}`、
  `lastHttpStatus`、`lastItemCount`、`consecutiveFailures`、`lastError`。
- 失败来源不影响整体构建，仅从 `sourceCount` 中扣除。

## 新增来源
在 `sources.yaml` 追加一项，选择匹配 `type`，运行 `python -m pipeline run` 验证
`healthStatus == ok` 与 `lastItemCount > 0`。
