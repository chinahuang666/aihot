import sys, time, requests, feedparser, json
s = requests.Session(); s.headers.update({"User-Agent":"AIhot-verify/0.1","Accept":"*/*"})
def probe(cid, ctype, url):
    try:
        r = s.get(url, timeout=25, allow_redirects=True)
        if r.status_code>=400: return (cid,ctype,"HTTP%d"%r.status_code,0,r.url)
        b=r.content; n=0
        if ctype in ("rss","atom"):
            n=len(feedparser.parse(b).entries)
        elif ctype=="github_release":
            try: n=len(json.loads(b))
            except: n=0
        elif ctype=="arxiv":
            n=len(feedparser.parse(b).entries)
        return (cid,ctype,"OK",n,r.url)
    except Exception as e: return (cid,ctype,"ERR:%s"%str(e)[:50],0,url)

# retry/alternate candidates
C = [
    ("jiqizhixin_x", "rss", "https://www.jiqizhixin.com/rss.xml"),
    ("36kr_x", "rss", "https://36kr.com/feed"),
    ("huggingface_blog2", "rss", "https://huggingface.co/blog/feed.xml"),
    ("arxiv_cl2", "arxiv", "http://export.arxiv.org/api/query?search_query=cat:cs.CL&sortBy=submittedDate&max_results=20"),
    ("anthropic_alt", "rss", "https://www.anthropic.com/news/rss"),
    ("deepmind_alt", "rss", "https://www.deepmind.com/blog/rss.xml"),
    ("microsoft_alt", "rss", "https://techcommunity.microsoft.com/category/ai-machine-learning/b/log/feed"),
    ("meta_alt", "rss", "https://ai.meta.com/blog/rss/"),
    ("bair_alt", "rss", "https://bair.berkeley.edu/blog/?feed=rss2"),
    ("google_research", "rss", "https://research.google/blog/rss/"),
    ("kdnuggets", "rss", "https://www.kdnuggets.com/feed"),
    ("analyticsvidhya", "rss", "https://www.analyticsvidhya.com/feed/"),
    ("llamaindex", "rss", "https://www.llamaindex.ai/blog/rss.xml"),
    ("assemblyai", "rss", "https://www.assemblyai.com/blog/rss.xml"),
    ("infoq_ai", "rss", "https://feed.infoq.com/ai/"),
]
for c in C:
    res=probe(*c); print("%-20s %-14s %-10s items=%d  %s"%(res[0],res[1],res[2],res[3],res[4])); sys.stdout.flush(); time.sleep(0.4)
