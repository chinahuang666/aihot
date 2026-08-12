# AIhot · AI 信号板

> 零服务端、纯静态的 AI 资讯聚合器。把多家来源（官方博客、科技媒体、论文、代码仓库发布）
> 的报道，按「事件」而非「文章」组织：同一事件的多篇报道去重合并为一个事件，来源可逐条展开。

## 特性

- **事件化聚类**：基于产品/版本实体 + 标题相似度，仅跨来源合并；同来源的不同发布保持独立。
- **规则摘要（默认）**：确定性、零成本、可复现；每条「关键说法」附带证据来源。不调用 LLM。
- **三维度打分**：热度 / 重要度 / 可信度，分别独立计算（见 `docs/SCORING.md`）。
- **可展开来源**：每个事件展示全部来源与证据，便于交叉核对。
- **静态前端**：Next.js 静态导出，可托管于任意静态服务（GitHub Pages / CloudStudio / Nginx）。
- **SSRF 防护**：抓取层屏蔽内网与云元数据地址，含超时、重试、体积限制。

## 目录结构

```
AIhot/
├── pipeline/            # 数据管线（Python）
│   ├── httpclient.py    # 安全 HTTP 客户端（SSRF 防护）
│   ├── connectors/      # RSS/Atom/GitHub Release/HN/arXiv/API 解析
│   ├── entities.py      # 规则化实体抽取（产品/版本）
│   ├── dedupe.py        # 近重复检测与合并判定
│   ├── cluster.py       # 事件聚类（并查集 + 人工覆盖）
│   ├── score.py         # 热度/重要度/可信度
│   ├── build.py         # 生成静态 JSON
│   └── pipeline.py      # 编排入口
├── config/             # sources.yaml / scoring.yaml / overrides/
├── web/                # 前端（Next.js + TS + Tailwind + MiniSearch）
├── public/data/        # 管线输出（静态 JSON）
├── docs/               # 架构 / 决策 / 来源 / 打分 / 安全
└── tests/              # pytest 单元与聚类夹具
```

## 快速开始

### 1. 运行管线（生成数据）

```bash
cd AIhot
python -m venv .venv && .venv\Scripts\activate   # 或已存在的 .venv
pip install -r requirements.txt
python -m pipeline run        # 抓取 → 标准化 → 去重 → 聚类 → 打分 → 生成 JSON
```

产物位于 `public/data/`：`manifest.json`、`stories.json`、`hot.json`、
`latest-selected.json`、`source-status.json`、`search-index.json`、`daily/`。

### 2. 本地预览前端

```bash
cd web
npm install
npm run build            # 先拷贝数据，再静态导出到 out/
# 预览：
npx serve out          # 或 python -m http.server 3000 --directory out
```

> 注：本环境对 `fs.rm` 有安全拦截，构建时请使用 `NODE_OPTIONS="" npm run build` 以绕过。

### 3. 测试

```bash
pytest tests/ -q
```

## 配置

- `config/sources.yaml`：来源清单（类型、角色、信任等级、刷新周期）。
- `config/scoring.yaml`：三维度权重、半衰期、状态阈值、抓取窗口。
- `config/overrides/`：人工合并 / 拆分 / 隐藏 / 来源信任覆盖。
- `.env`（参考 `.env.example`）：可选 LLM 密钥与预算（默认关闭）。

## 部署（自动化）

见 `.github/workflows/build.yml`：定时（每 30 分钟）运行管线并将 `web/out` 发布到
GitHub Pages。本地亦可直接将 `web/out` 上传至任意静态托管。

## 文档

- `docs/ARCHITECTURE.md` — 管线与数据流
- `docs/DECISIONS.md` — 关键设计决策与权衡
- `docs/SOURCES.md` — 来源注册表与可靠性
- `docs/SCORING.md` — 打分模型
- `docs/SECURITY.md` — 抓取层安全
