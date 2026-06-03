"""
CS:GO 皮肤大盘指数爬虫
追踪热门皮肤 Steam 市场价格，计算涨跌指数
"""

import concurrent.futures
import requests
from config import SOURCES

# CS:GO appid
APP_ID = 730
# 人民币
CURRENCY = 23

# 大盘指数追踪的 12 款标杆皮肤
INDEX_ITEMS = [
    "AK-47 | Redline (Field-Tested)",
    "AWP | Asiimov (Field-Tested)",
    "M4A4 | 龙王 (Minimal Wear)",
    "Glock-18 | 水灵 (Minimal Wear)",
    "USP-S | 脑洞大开 (Field-Tested)",
    "Desert Eagle | 印花集 (Minimal Wear)",
    "AK-47 | 火蛇 (Field-Tested)",
    "M4A1-S | 血色运动 (Minimal Wear)",
    "AWP | 野火 (Field-Tested)",
    "SSG 08 | 浮生若梦 (Field-Tested)",
    "P250 | 核子污染 (Minimal Wear)",
    "MAC-10 | 核子花园 (Minimal Wear)",
]


def _get_price(market_hash_name):
    """获取单个皮肤的价格"""
    try:
        url = "https://steamcommunity.com/market/priceoverview/"
        params = {
            "appid": APP_ID,
            "currency": CURRENCY,
            "market_hash_name": market_hash_name,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if not data.get("success"):
            return None

        price_str = data.get("lowest_price", "$0")
        volume_str = data.get("volume", "0")

        # 解析价格
        price_str = price_str.replace("¥", "").replace(",", "").strip()
        try:
            price = float(price_str)
        except ValueError:
            return None

        volume = int(volume_str.replace(",", "")) if volume_str else 0

        return {
            "name": market_hash_name,
            "price": price,
            "volume": volume,
        }
    except Exception:
        return None


def fetch_csgo_market():
    """获取 CS:GO 皮肤大盘指数"""
    config = SOURCES.get("csgo", {})
    if not config.get("enabled", True):
        return []

    max_items = config.get("max_items", 12)
    news_list = []

    try:
        items = INDEX_ITEMS[:max_items]

        # 并行获取价格
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(_get_price, item): item for item in items}
            for f in concurrent.futures.as_completed(futures):
                result = f.result()
                if result:
                    results.append(result)

        if not results:
            print("[CSGO] 未获取到任何价格数据")
            return []

        # 按价格排序
        results.sort(key=lambda x: x["price"], reverse=True)

        # 计算大盘指数
        total_price = sum(r["price"] for r in results)
        total_volume = sum(r["volume"] for r in results)
        avg_price = total_price / len(results)

        for r in results:
            short_name = r["name"].split(" (")[0] if " (" in r["name"] else r["name"]
            direction = "📈" if r["volume"] > 50 else "➡"
            summary = f"¥{r['price']:.2f} | 成交量:{r['volume']} | {direction}"

            news_list.append({
                "title": f"{short_name} ¥{r['price']:.2f}",
                "url": f"https://steamcommunity.com/market/listings/{APP_ID}/{r['name'].replace(' ', '%20')}",
                "source": "CSGO大盘",
                "score": min(10, max(1, int(r["price"] / 50))),
                "comments": r["volume"],
                "summary": summary,
            })

        # 大盘指数摘要（第一条作为指数）
        index_item = {
            "title": f"🔫 CS:GO 大盘指数 ¥{avg_price:.2f}",
            "url": "https://steamcommunity.com/market/search?appid=730",
            "source": "CSGO大盘",
            "score": 8,
            "comments": total_volume,
            "summary": f"12款标杆皮肤均价 ¥{avg_price:.2f} | 总成交量 {total_volume} | 最高 ¥{results[0]['price']:.2f} 最低 ¥{results[-1]['price']:.2f}",
        }
        news_list.insert(0, index_item)

    except Exception as e:
        print(f"[CSGO] 抓取失败: {e}")

    print(f"[CSGO] 抓取完成: {len(news_list)} 条 (大盘指数 ¥{avg_price:.2f})")
    return news_list


if __name__ == "__main__":
    for n in fetch_csgo_market()[:5]:
        print(f"  {n['title'][:60]} | {n['summary'][:60]}")
