"""
微博热搜爬虫
使用微博公开 API
"""

import requests
from config import SOURCES


def fetch_weibo():
    """抓取微博热搜榜 Top N"""
    config = SOURCES["weibo"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/",
            "X-Requested-With": "XMLHttpRequest",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # 热搜榜
        realtime = data.get("data", {}).get("realtime", [])[:max_items]

        for item in realtime:
            word = item.get("word", "").strip()
            if not word:
                continue

            raw_hot = item.get("raw_hot", 0)
            category = item.get("category", "")

            # 构建搜索链接
            search_url = f"https://s.weibo.com/weibo?q={requests.utils.quote(word)}&t=31"

            news_list.append({
                "title": word,
                "url": search_url,
                "source": "微博热搜",
                "score": int(raw_hot) if raw_hot else 0,
                "comments": 0,
                "summary": f"热搜指数: {raw_hot} | 分类: {category}" if category else f"热搜指数: {raw_hot}",
            })

    except Exception as e:
        print(f"[微博] 抓取失败: {e}")

    print(f"[微博] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_weibo()[:5]:
        print(f"  {n['title'][:60]}... | 热度:{n['score']}")
