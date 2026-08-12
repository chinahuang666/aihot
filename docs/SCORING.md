# 打分模型（SCORING）

每个 Story 独立计算三个分数（0–1），权重在 `config/scoring.yaml` 中可读配置。

## 热度 Heat
`velocity * 0.35 + coverage * 0.25 + interaction * 0.20 + freshness * 0.20`
- **velocity**：独立来源在首次出现后的聚集速度（越快越高）。
- **coverage**：独立来源数量归一化（≥6 满分）。
- **interaction**：互动指标（如 HN points/comments 之和）归一化。
- **freshness**：基于 `firstSeenAt` 的时间衰减，半衰期按品类（`halfLifeHours`）不同。

## 重要度 Importance
`industryImpact * 0.35 + originality * 0.25 + authority * 0.20 + endurance * 0.20`
- **industryImpact**：来源覆盖广度 + 品类（model/safety 加权）。
- **originality**：是否含一手来源（一手满分，否则 0.4）。
- **authority**：来源信任等级均值归一化。
- **endurance**：覆盖度驱动，衡量持续价值。

## 可信度 Confidence
`firsthand * 0.40 + crossConfirm * 0.30 + histQuality * 0.20 + metaComplete * 0.10 − penalty`
- **firsthand**：一手来源存在则满分。
- **crossConfirm**：独立来源交叉确认（≥4 满分）。
- **histQuality**：来源历史质量（信任等级均值）。
- **metaComplete**：主来源发布时间/链接完整。
- **penalty**：存在矛盾 −0.20；单一来源/单一转发链 −0.15。

## 状态（status）
由热度与时效推导：`hot ≥ 0.70` · `warming ≥ 0.45` · `cooling`（>24h 且热度低）·
`archived`（>7 天）· `disputed`（存在矛盾）· 其余 `new`。

## 综合排序
`0.4*heat + 0.4*importance + 0.2*confidence`，用于信号板与日报的默认排序。
热榜单独按 `heat` 排序。
