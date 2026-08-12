import sys, time, requests, feedparser
s = requests.Session(); s.headers.update({"User-Agent":"AIhot-verify/0.1","Accept":"*/*"})
def probe(cid, url):
    try:
        r = s.get(url, timeout=25, allow_redirects=True)
        if r.status_code>=400: return (cid,"HTTP%d"%r.status_code,0,r.url)
        n=len(feedparser.parse(r.content).entries)
        return (cid,"OK",n,r.url)
    except Exception as e: return (cid,"ERR:%s"%str(e)[:50],0,url)
for cid,url in [
    ("qwenlm","https://qwenlm.github.io/feed.xml"),
    ("jiqizhixin2","https://www.jiqizhixin.com/rss"),
    ("jiqizhixin3","https://jiqizhixin.com/rss"),
    ("baichuan","https://www.baichuan-ai.com/rss"),
    ("stepfun","https://www.stepfun.com/feed"),
]:
    res=probe(cid,url); print("%-14s %-10s items=%d  %s"%(res[0],res[1],res[2],res[3])); sys.stdout.flush(); time.sleep(0.4)
