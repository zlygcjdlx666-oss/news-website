"""
CS:GO 皮肤大盘行情爬虫
数据来源: Steam 官方社区市场 + FirePulse 指数（国内访问优先）
"""

import requests
from config import SOURCES

STEAM_API = "https://steamcommunity.com/market/search/render/"
FIREPULSE_API = "https://api.firepulse.com.cn/v1/market/facade/category/large_cap"


def _fetch_firepulse():
    """尝试从 FirePulse 获取大盘指数（国内可访问）"""
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://firepulse.com.cn/",
        }
        resp = requests.post(FIREPULSE_API, json={}, headers=headers, timeout=15)
        data = resp.json()
        if data.get("code") == 200:
            index = data["data"]["index_basic_info"]
            trade = data["data"]["trade_basic_info"]
            updown = data["data"]["updown_basic_info"]
            return {
                "current_index": index["current_index"],
                "change_index": index["change_index"],
                "change_percent": index["change_index_percent"],
                "max_index": index["max_index"],
                "min_index": index["min_index"],
                "change_day": index["change_day"],
                "latest_time": index["latest_time"],
                "today_amount": trade["today_amount"] / 10000,
                "today_volume": trade["today_volume"],
                "up_count": updown["up_count"],
                "flat_count": updown["flat_count"],
                "down_count": updown["down_count"],
            }
    except Exception:
        pass
    return None


def _fetch_steam():
    """从 Steam 市场获取热门饰品行情（海外可访问）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        params = {
            "appid": 730,
            "norender": 1,
            "count": 10,
            "sort_column": "volume",
            "sort_dir": "desc",
            "currency": 23,
        }
        resp = requests.get(STEAM_API, params=params, headers=headers, timeout=20)
        data = resp.json()
        items = data.get("results", [])[:10]

        if not items:
            return None

        total_price = 0
        item_count = 0
        results = []
        for item in items:
            name = item.get("name", "").strip()
            if not name:
                continue
            price_text = item.get("sell_price_text", "0")
            try:
                price = float(price_text.replace("¥", "").replace(",", "").replace(" ", ""))
            except (ValueError, AttributeError):
                price = 0
            if price <= 0:
                continue

            volume = item.get("sell_listings", 0)
            total_price += price
            item_count += 1
            results.append({"name": name, "price": price, "volume": volume})

        if item_count == 0:
            return None

        avg = total_price / item_count
        total_vol = sum(r["volume"] for r in results)
        top3 = " · ".join(r["name"][:15] for r in results[:3])
        return {
            "avg_price": avg,
            "item_count": item_count,
            "total_volume": total_vol,
            "top_items": results,
            "top3": top3,
            "source": "Steam",
        }
    except Exception:
        return None


def fetch_csgo_market():
    """获取 CS:GO 大盘行情"""
    config = SOURCES.get("csgo", {})
    if not config.get("enabled", True):
        return []

    news_list = []

    # 先尝试 FirePulse（国内）
    fp = _fetch_firepulse()
    if fp:
        direction = "📈" if fp["change_index"] > 0 else "📉" if fp["change_index"] < 0 else "➡"
        sign = "+" if fp["change_index"] >= 0 else ""
        news_list.append({
            "title": f"🔫 CS:GO 大盘指数 {fp['current_index']} {direction}{sign}{fp['change_index']}({sign}{fp['change_percent']}%)",
            "url": "https://firepulse.com.cn/#/home",
            "source": "CSGO大盘",
            "score": 9,
            "comments": fp["today_volume"],
            "summary": (
                f"今日 {fp['current_index']} | {direction} {sign}{fp['change_index']}({sign}{fp['change_percent']}%) | "
                f"最高 {fp['max_index']} 最低 {fp['min_index']} | 连涨 {fp['change_day']}天 | "
                f"成交额 ¥{fp['today_amount']:.0f}万 | 成交量 {fp['today_volume']}件 | "
                f"📈{fp['up_count']} ➡{fp['flat_count']} 📉{fp['down_count']}"
            ),
        })
        print(f"[CSGO] FirePulse 大盘: {fp['current_index']} ({sign}{fp['change_percent']}%)")
        return news_list

    # 回退到 Steam 市场
    steam = _fetch_steam()
    if steam:
        news_list.append({
            "title": f"🔫 CS:GO Steam大盘均价 ¥{steam['avg_price']:.2f}",
            "url": "https://steamcommunity.com/market/search?appid=730",
            "source": "CSGO大盘",
            "score": 8,
            "comments": steam["total_volume"],
            "summary": (
                f"Steam成交量Top{steam['item_count']}均价 ¥{steam['avg_price']:.2f} | "
                f"总挂单 {steam['total_volume']}件 | 热门: {steam['top3']}"
            ),
        })
        for item in steam["top_items"][:6]:
            news_list.append({
                "title": f"{item['name'][:40]} ¥{item['price']:.2f}",
                "url": f"https://steamcommunity.com/market/listings/730/{item['name']}",
                "source": "CSGO大盘",
                "score": min(10, max(2, int(item['price'] / 100))),
                "comments": item["volume"],
                "summary": f"Steam市场 ¥{item['price']:.2f} | 挂单 {item['volume']}件",
            })
        print(f"[CSGO] Steam大盘: ¥{steam['avg_price']:.2f} ({steam['item_count']}款)")
        return news_list

    print("[CSGO] 所有数据源均失败")
    return []


if __name__ == "__main__":
    for n in fetch_csgo_market():
        print(f"  {n['title'][:80]}")
