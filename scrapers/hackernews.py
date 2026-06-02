"""
Hacker News 热榜爬虫
使用官方 Firebase API，无需爬取网页
"""

import requests
from config import SOURCES


def fetch_hackernews():
    """抓取 Hacker News 热门新闻 Top N"""
    config = SOURCES["hackernews"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        # 获取热门故事 ID 列表
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(top_url, timeout=15)
        resp.raise_for_status()
        story_ids = resp.json()[:max_items]

        # 逐个获取故事详情
        for sid in story_ids:
            try:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                item = requests.get(item_url, timeout=10).json()
                if item and item.get("title"):
                    news_list.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        "source": "Hacker News",
                        "score": item.get("score", 0),
                        "comments": item.get("descendants", 0),
                        "summary": "",
                    })
            except Exception:
                continue

    except Exception as e:
        print(f"[HackerNews] 抓取失败: {e}")

    print(f"[HackerNews] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_hackernews()[:5]:
        print(f"  {n['title'][:60]}... | 热度:{n['score']} | 评论:{n['comments']}")
