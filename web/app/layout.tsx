import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIhot · AI 信号板",
  description: "事件驱动的 AI 资讯聚合：同一事件多源去重，信号可展开。",
};

const NAV = [
  { href: "/", label: "信号板" },
  { href: "/hot", label: "热点" },
  { href: "/sources", label: "来源" },
  { href: "/archive", label: "日报" },
  { href: "/about", label: "关于" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="border-b border-line bg-white sticky top-0 z-20">
          <div className="container flex items-center justify-between h-14">
            <Link href="/" className="flex items-center gap-2 font-bold text-lg">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-brand" />
              AIhot
              <span className="text-muted font-normal text-sm hidden sm:inline">AI 信号板</span>
            </Link>
            <nav className="flex items-center gap-1 sm:gap-3 text-sm">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="px-2 py-1 rounded-md text-muted hover:text-ink hover:bg-slate-100"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="container py-6 min-h-[70vh]">{children}</main>
        <footer className="border-t border-line bg-white">
          <div className="container py-4 text-xs text-muted">
            AIhot · 零服务端静态聚合 · 事件去重 · 规则摘要（无 LLM）
          </div>
        </footer>
      </body>
    </html>
  );
}
