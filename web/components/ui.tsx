import type { Story, StoryStatus } from "@/lib/types";
import { STATUS_LABEL, CATEGORY_LABEL, scorePct } from "@/lib/api";

const STATUS_STYLE: Record<StoryStatus, string> = {
  new: "bg-blue-50 text-blue-700 border-blue-200",
  warming: "bg-amber-50 text-amber-700 border-amber-200",
  hot: "bg-red-50 text-red-700 border-red-200",
  cooling: "bg-slate-100 text-slate-600 border-slate-200",
  archived: "bg-slate-100 text-slate-500 border-slate-200",
  disputed: "bg-purple-50 text-purple-700 border-purple-200",
};

export function StatusBadge({ status }: { status: StoryStatus }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs border ${STATUS_STYLE[status] || ""}`}>
      {STATUS_LABEL[status] || status}
    </span>
  );
}

export function CategoryChip({ category }: { category: string }) {
  return (
    <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-muted text-xs">
      {CATEGORY_LABEL[category] || category}
    </span>
  );
}

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-8 text-muted">{label}</span>
      <div className="flex-1 h-1.5 rounded bg-slate-100 overflow-hidden">
        <div className="h-full rounded" style={{ width: `${scorePct(value)}%`, background: color }} />
      </div>
      <span className="w-8 text-right tabular-nums text-muted">{scorePct(value)}</span>
    </div>
  );
}

export function ScoreBars({ story }: { story: Story }) {
  return (
    <div className="space-y-1">
      <Bar label="热度" value={story.heatScore} color="#dc2626" />
      <Bar label="重要" value={story.importanceScore} color="#2563eb" />
      <Bar label="可信" value={story.confidenceScore} color="#16a34a" />
    </div>
  );
}
