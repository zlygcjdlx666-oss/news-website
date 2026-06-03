"""
Steam 热门游戏爬虫
抓取 Steam 热销 & 热门游戏
"""

import requests
from config import SOURCES


def fetch_steam():
    """抓取 Steam 热销游戏"""
    config = SOURCES["steam"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        # Steam 商店 featured API
        url = "https://store.steampowered.com/api/featuredcategories"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # 收集所有游戏
        games = []
        seen = set()

        # 热销 & 热门
        for category in ["top_sellers", "specials", "coming_soon"]:
            items = data.get(category, {}).get("items", [])
            for item in items:
                app_id = item.get("id")
                if app_id and app_id not in seen:
                    seen.add(app_id)
                    games.append({
                        "title": item.get("name", ""),
                        "url": f"https://store.steampowered.com/app/{app_id}",
                        "image": item.get("large_capsule_image", ""),
                        "discount": item.get("discount_percent", 0),
                        "price": item.get("final_price", 0) / 100,
                        "score": item.get("discount_percent", 0) * 100 + 100,  # 热度值
                    })

        games = games[:max_items]

        for g in games:
            parts = []
            if g.get("discount"):
                parts.append(f"-{g['discount']}%")
            if g.get("price"):
                parts.append(f"${g['price']:.0f}")
            summary = " | ".join(parts) if parts else "Steam 热销游戏"

            news_list.append({
                "title": g["title"],
                "url": g["url"],
                "source": "Steam",
                "score": g.get("score", 100),
                "comments": 0,
                "summary": summary,
            })

    except Exception as e:
        print(f"[Steam] 抓取失败: {e}")

    print(f"[Steam] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_steam()[:5]:
        print(f"  {n['title'][:60]}... | {n['summary']}")
