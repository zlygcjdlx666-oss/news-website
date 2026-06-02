"""
Bilibili 热门视频爬虫
抓取 B 站热门视频，涵盖科技、娱乐、生活等分区
"""

import requests
from config import SOURCES


def fetch_bilibili():
    """抓取 Bilibili 热门视频"""
    config = SOURCES["bilibili"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        url = "https://api.bilibili.com/x/web-interface/popular"
        params = {"ps": max_items + 10, "pn": 1}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("data", {}).get("list", [])[:max_items]
        for item in items:
            title = item.get("title", "").strip()
            if not title:
                continue

            owner = item.get("owner", {})
            stat = item.get("stat", {})
            views = stat.get("view", 0)
            danmaku = stat.get("danmaku", 0)  # 弹幕数
            bvid = item.get("bvid", "")

            # 构建有趣的摘要
            parts = []
            if views:
                parts.append(f"播放:{_format_count(views)}")
            if danmaku:
                parts.append(f"弹幕:{_format_count(danmaku)}")
            parts.append(f"UP主:{owner.get('name', '未知')}")
            summary = " | ".join(parts)

            news_list.append({
                "title": title,
                "url": f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                "source": "B站热门",
                "score": views,
                "comments": danmaku,
                "summary": summary,
            })

    except Exception as e:
        print(f"[Bilibili] 抓取失败: {e}")

    print(f"[Bilibili] 抓取完成: {len(news_list)} 条")
    return news_list


def _format_count(n):
    """格式化数字"""
    if n >= 10000:
        return f"{n/10000:.1f}万"
    return str(n)


if __name__ == "__main__":
    for n in fetch_bilibili()[:5]:
        print(f"  {n['title'][:60]}... | {n['summary'][:50]}")
