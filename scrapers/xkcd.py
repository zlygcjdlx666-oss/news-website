"""
XKCD 每日漫画爬虫
抓取最新的科学/技术幽默漫画，英文互联网文化经典
"""

import requests
from config import SOURCES


def fetch_xkcd():
    """抓取最近几期的 XKCD 漫画"""
    config = SOURCES["xkcd"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        # 先获取最新漫画编号
        latest = requests.get("https://xkcd.com/info.0.json", timeout=15).json()
        latest_num = latest.get("num", 0)

        # 抓取最近几期
        for num in range(latest_num, max(latest_num - max_items, 0), -1):
            try:
                comic = requests.get(f"https://xkcd.com/{num}/info.0.json", timeout=10).json()
                title = comic.get("title", "")
                alt = comic.get("alt", "")  # 悬停文字是精华
                if title:
                    news_list.append({
                        "title": f"XKCD: {title}",
                        "url": f"https://xkcd.com/{num}/",
                        "source": "XKCD",
                        "score": 0,
                        "comments": 0,
                        "summary": f"漫画说明: {alt}"[:300] if alt else "",
                    })
            except Exception:
                continue

    except Exception as e:
        print(f"[XKCD] 抓取失败: {e}")

    print(f"[XKCD] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_xkcd()[:3]:
        print(f"  {n['title'][:60]}...")
        print(f"    {n['summary'][:80]}...")
