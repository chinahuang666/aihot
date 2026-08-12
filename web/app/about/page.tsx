export default function AboutPage() {
  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-xl font-bold">关于 AIhot</h1>
      <p className="text-sm leading-relaxed text-muted">
        AIhot 是一个<strong className="text-ink">零服务端、纯静态</strong>的 AI 资讯聚合器。
        它把多家来源（官方博客、科技媒体、论文、代码仓库发布）的报道，按「事件」而非「文章」组织：
        同一事件的多篇报道会被去重合并为一个事件，来源可逐条展开。
      </p>

      <h2 className="font-semibold">方法论</h2>
      <ul className="text-sm text-muted list-disc list-inside space-y-1">
        <li><strong className="text-ink">事件化聚类</strong>：基于产品/版本实体 + 标题相似度，仅跨来源合并，同来源的不同发布保持独立。</li>
        <li><strong className="text-ink">规则摘要</strong>：默认使用确定性规则生成摘要与「关键说法」，每条说法附带证据来源；不调用 LLM，零成本、可复现。</li>
        <li><strong className="text-ink">三维度打分</strong>：热度（传播速度×覆盖×互动×新鲜度）、重要度、可信度，分别独立计算。</li>
        <li><strong className="text-ink">信号可展开</strong>：每个事件展示全部来源与证据，便于交叉核对。</li>
      </ul>

      <h2 className="font-semibold">数据来源</h2>
      <p className="text-sm text-muted">
        涵盖 OpenAI / Google / Anthropic / Meta / DeepSeek 等官方渠道，The Verge、TechCrunch、Wired 等媒体，
        arXiv 论文，以及 vLLM、Ollama、Transformers 等开源项目的发布动态（通过公开 Atom Feed 获取，免鉴权）。
      </p>

      <h2 className="font-semibold">隐私与安全</h2>
      <p className="text-sm text-muted">
        抓取层内置 SSRF 防护（屏蔽内网/元数据地址）、超时、重试与体积限制；全程不收集任何用户数据。
      </p>
    </div>
  );
}
