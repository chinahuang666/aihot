"""Notify stage: push AIhot daily top stories to a WeCom (企业微信) group bot webhook.

Reads public/data/hot.json (top stories by heat), renders a markdown card,
and POSTs it to the group-robot webhook configured in config/wecom.yaml.

Usage:
    python -m pipeline notify            # push current top-N (default 10)
    python -m pipeline notify --top 10
"""
from __future__ import annotations

import argparse
import html
import json
import ssl
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# 默认指向已验证可用的 CloudStudio 线上站点；可在 config/wecom.yaml 覆盖。
DEFAULT_SITE = "https://f22de598162848ab94a210a212c7fd9d.bj9.agentos-app.net"


def load_config() -> dict:
    """Read config/wecom.yaml (simple key: value, or full YAML if pyyaml present).

    Secrets are intentionally NOT committed — only config/wecom.yaml.example is.
    """
    cfg = {"webhook_url": "", "site_url": DEFAULT_SITE, "top_n": 10}
    p = ROOT / "config" / "wecom.yaml"
    if not p.exists():
        return cfg
    text = p.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text) or {}
        cfg.update(loaded)
        return cfg
    except Exception:
        pass
    # fallback: parse `key: value` lines (strip surrounding quotes)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def load_hot(n: int) -> dict:
    p = ROOT / "public" / "data" / "hot.json"
    if not p.exists():
        raise FileNotFoundError(f"no hot.json at {p} — run `python -m pipeline run` first")
    env = json.loads(p.read_text(encoding="utf-8"))
    return env


def _esc(s: str) -> str:
    # Decode HTML entities (e.g. &#8217; -> ') then neutralise angle brackets
    # so they don't break WeCom markdown rendering.
    return html.unescape(s or "").replace("<", "&lt;").replace(">", "&gt;")


# category code -> 中文标签（任务书 §7 分类）
CAT_ZH = {
    "model": "模型", "product": "产品", "developer": "开发者",
    "research": "研究", "industry": "行业", "safety": "安全",
}


def render_markdown(stories: list, site_url: str, date_str: str) -> str:
    site = site_url.rstrip("/")
    lines = [
        f"# 🔥 AIhot 每日热点 Top {len(stories)}",
        f"> 日期 **{date_str}** ｜ 多平台 AI 资讯实时聚合",
        "",
    ]
    for i, s in enumerate(stories, 1):
        title = _esc(s.get("headline", "未命名事件"))
        sid = s.get("id", "")
        url = f"{site}/story/?id={sid}"
        cat = CAT_ZH.get(s.get("category", ""), s.get("category", ""))
        heat = float(s.get("heatScore", 0.0) or 0.0)
        n_reports = len(s.get("itemIds", []))
        status = s.get("status", "")
        status_tag = f" · {status}" if status else ""
        lines.append(f"**{i}. [{title}]({url})**")
        lines.append(
            f"> <font color=\"info\">{cat}</font>{status_tag} ｜ 🔥 热度 {heat:.2f} ｜ {n_reports} 条报道"
        )
        wh = _esc(s.get("whatHappened", ""))
        if wh:
            lines.append(f"> {wh[:80]}")
        lines.append("")
    lines.append("---")
    lines.append(f"🤖 由 AIhot 自动聚合 · 完整信号板：[{site}]({site})")
    return "\n".join(lines)


def send(webhook_url: str, content: str) -> dict:
    payload = {"msgtype": "markdown", "markdown": {"content": content}}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        body = r.read().decode("utf-8", "replace")
    return json.loads(body)


def notify(top_n: int = 10) -> dict:
    cfg = load_config()
    wh = (cfg.get("webhook_url") or "").strip()
    if not wh:
        print("WECHAT_WEBHOOK_MISSING: set webhook_url in config/wecom.yaml "
              "(see config/wecom.yaml.example)")
        return {"ok": False, "error": "no webhook configured"}
    env = load_hot(top_n)
    stories = env.get("data", [])[:top_n]
    if not stories:
        print("NOTIFY_EMPTY: no stories to push")
        return {"ok": False, "error": "empty"}
    date_str = (env.get("generatedAt") or "")[:10] or "今日"
    content = render_markdown(stories, cfg.get("site_url", DEFAULT_SITE), date_str)
    try:
        resp = send(wh, content)
    except Exception as e:  # network / http errors
        print(f"WECHAT_SEND_ERROR: {e}")
        return {"ok": False, "error": str(e)[:200]}
    print("WECHAT_SENT", resp)
    return {"ok": True, "resp": resp, "stories": len(stories)}


def main():
    ap = argparse.ArgumentParser(description="AIhot WeCom notifier")
    ap.add_argument("--top", type=int, default=None, help="how many top stories to push")
    args = ap.parse_args()
    n = args.top or load_config().get("top_n", 10)
    notify(n)


if __name__ == "__main__":
    main()
