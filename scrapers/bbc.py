"""
BBC News 爬虫
通过 RSS Feed 获取最近新闻
"""

import feedparser
from config import SOURCES


def fetch_bbc():
    """抓取 BBC News RSS Feed"""
    config = SOURCES["bbc"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    # BBC 多个 RSS Feed
    feeds = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",   # 世界新闻
        "https://feeds.bbci.co.uk/news/technology/rss.xml",  # 科技
        "https://feeds.bbci.co.uk/news/business/rss.xml",    # 财经
    ]

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            category = feed_url.split("/")[-2] if "/" in feed_url else "news"

            for entry in feed.entries[:max_items // len(feeds) + 5]:
                title = entry.get("title", "")
                if not title:
                    continue

                news_list.append({
                    "title": title,
                    "url": entry.get("link", ""),
                    "source": f"BBC {category.title()}",
                    "score": 0,
                    "comments": 0,
                    "summary": entry.get("summary", "")[:300] if entry.get("summary") else "",
                })

        except Exception as e:
            print(f"[BBC] {feed_url} 抓取失败: {e}")

    print(f"[BBC] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_bbc()[:5]:
        print(f"  {n['title'][:60]}... | {n['source']}")
