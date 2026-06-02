"""
Solidot 科技新闻爬虫（中文 Slashdot）
使用 RSS Feed，稳定可靠
"""

import feedparser
from config import SOURCES


def fetch_solidot():
    """抓取 Solidot 科技新闻（替代知乎热榜）"""
    config = SOURCES["solidot"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        feed = feedparser.parse("https://www.solidot.org/index.rss")

        for entry in feed.entries[:max_items]:
            title = entry.get("title", "")
            if not title:
                continue

            # Solidot RSS 的 summary 通常包含更多信息
            summary = entry.get("summary", "")
            # 清理 HTML 标签
            import re
            summary = re.sub(r"<[^>]+>", "", summary)[:300] if summary else ""

            # 从标题中提取分类标签
            category = "科技"
            if "安全" in title:
                category = "科技"
            elif "科学" in title:
                category = "科学"
            elif "AI" in title or "人工智能" in title:
                category = "科技"

            news_list.append({
                "title": title,
                "url": entry.get("link", ""),
                "source": "Solidot",
                "score": 0,
                "comments": 0,
                "summary": summary,
            })

    except Exception as e:
        print(f"[Solidot] 抓取失败: {e}")

    print(f"[Solidot] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_solidot()[:5]:
        print(f"  {n['title'][:60]}... | {n['source']}")
