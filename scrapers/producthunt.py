"""
Product Hunt 热门产品爬虫
抓取每日最受欢迎的新产品/工具，发现有趣创新的东西
"""

import feedparser
from config import SOURCES


def fetch_producthunt():
    """抓取 Product Hunt 今日热门产品"""
    config = SOURCES["producthunt"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        feed = feedparser.parse("https://www.producthunt.com/feed")

        for entry in feed.entries[:max_items]:
            title = entry.get("title", "")
            if not title:
                continue

            # Product Hunt 的 title 格式通常是 "Product Name: tagline"
            summary = entry.get("summary", "")
            import re
            summary = re.sub(r"<[^>]+>", "", summary)[:250] if summary else ""

            # 提取投票数（从 summary 中）
            votes = ""
            desc = entry.get("description", "")
            if desc:
                desc_clean = re.sub(r"<[^>]+>", "", desc)
                match = re.search(r"(\d+)\s*upvotes", desc_clean)
                if match:
                    votes = match.group(1)

            score_info = f"👍 {votes}" if votes else ""

            news_list.append({
                "title": f"🆕 {title}"[:200],
                "url": entry.get("link", ""),
                "source": "Product Hunt",
                "score": int(votes) if votes else 0,
                "comments": 0,
                "summary": f"{score_info} | {summary}"[:300],
            })

    except Exception as e:
        print(f"[ProductHunt] 抓取失败: {e}")

    print(f"[ProductHunt] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_producthunt()[:5]:
        print(f"  {n['title'][:60]}... | 热度:{n['score']}")
