"""Dev helper: probe candidate source URLs, report status + item count.

Not part of the runtime pipeline; used to build a verified sources.yaml.
"""
import sys
import time
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter

session = requests.Session()
session.headers.update({"User-Agent": "AIhot-verify/0.1", "Accept": "*/*"})
try:
    from lxml import etree
except Exception:
    etree = None
try:
    import feedparser
except Exception:
    feedparser = None

CANDIDATES = [
    ("openai_blog", "rss", "https://openai.com/blog/rss.xml"),
    ("anthropic_news", "rss", "https://www.anthropic.com/news/rss.xml"),
    ("google_ai", "rss", "https://blog.google/technology/ai/rss/"),
    ("deepmind_blog", "rss", "https://deepmind.google/discover/blog/rss.xml"),
    ("microsoft_ai", "rss", "https://blogs.microsoft.com/ai/rss/"),
    ("meta_ai", "rss", "https://ai.meta.com/blog/rss/"),
    ("jiqizhixin", "rss", "https://www.jiqizhixin.com/rss"),
    ("qbitai", "rss", "https://www.qbitai.com/feed"),
    ("36kr", "rss", "https://36kr.com/feed"),
    ("huggingface_blog", "rss", "https://huggingface.co/blog/feed.xml"),
    ("theverge_ai", "rss", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("techcrunch_ai", "rss", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("wired_ai", "rss", "https://www.wired.com/feed/tag/ai/latest/rss"),
    ("zdnet_ai", "rss", "https://www.zdnet.com/topic/artificial-intelligence/rss.xml"),
    ("venturebeat", "rss", "https://venturebeat.com/feed/"),
    ("marktechpost", "rss", "https://www.marktechpost.com/feed/"),
    ("synced", "rss", "https://syncedreview.com/feed/"),
    ("mit_tech_review", "rss", "https://www.technologyreview.com/feed/"),
    ("bair", "rss", "https://bair.berkeley.edu/blog/feed/"),
    ("huggingface_papers", "rss", "https://huggingface.co/papers/feed.xml"),
    ("vllm_rel", "github_release", "https://api.github.com/repos/vllm-project/vllm/releases"),
    ("ollama_rel", "github_release", "https://api.github.com/repos/ollama/ollama/releases"),
    ("transformers_rel", "github_release", "https://api.github.com/repos/huggingface/transformers/releases"),
    ("langchain_rel", "github_release", "https://api.github.com/repos/langchain-ai/langchain/releases"),
    ("llamacpp_rel", "github_release", "https://api.github.com/repos/ggerganov/llama.cpp/releases"),
    ("autogen_rel", "github_release", "https://api.github.com/repos/microsoft/autogen/releases"),
    ("hn_ai", "hn", "https://hn.algolia.com/api/v1/search?tags=story&query=artificial%20intelligence&hitsPerPage=30"),
    ("arxiv_ai", "arxiv", "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&max_results=20"),
    ("arxiv_cl", "arxiv", "http://export.arxiv.org/api/query?search_query=cat:cs.CL&sortBy=submittedDate&max_results=20"),
]


def probe(cid, ctype, url):
    try:
        r = session.get(url, timeout=25, allow_redirects=True)
        if r.status_code >= 400:
            return (cid, ctype, "HTTP%d" % r.status_code, 0)
        body = r.content
        n = 0
        if ctype in ("rss", "atom"):
            if feedparser:
                n = len(feedparser.parse(body).entries)
            elif etree:
                try:
                    n = len(etree.fromstring(body).findall(".//{*}entry")) or len(etree.fromstring(body).findall(".//item"))
                except Exception:
                    n = 0
        elif ctype == "github_release":
            import json
            try:
                n = len(json.loads(body))
            except Exception:
                n = 0
        elif ctype == "hn":
            import json
            try:
                n = len(json.loads(body).get("hits", []))
            except Exception:
                n = 0
        elif ctype == "arxiv":
            if feedparser:
                n = len(feedparser.parse(body).entries)
        return (cid, ctype, "OK", n)
    except Exception as e:
        return (cid, ctype, "ERR:%s" % str(e)[:40], 0)


if __name__ == "__main__":
    results = []
    for c in CANDIDATES:
        res = probe(*c)
        results.append(res)
        print("%-22s %-14s %-10s items=%d" % (res[0], res[1], res[2], res[3]))
        sys.stdout.flush()
        time.sleep(0.3)
    ok = [r for r in results if r[2] == "OK" and r[3] > 0]
    print("\nVERIFIED=%d / %d" % (len(ok), len(results)))
